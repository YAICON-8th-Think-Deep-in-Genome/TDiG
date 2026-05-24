"""PHASE B — chr22 main forward (optimized).

Architecture (2 tracks for speed):
    All 12,978 windows -> Tier 1 settling depths only (fast)
    100 subset windows  -> + Tier 2 per-layer scalars + Tier 3 raw h_ell

Stored per-layer per-token scalars (subset only):
    cos_refA/B/C            fp16, (L, T)        for M1
    norm_h_ell              fp32, (L, T)        for M2
    step_norm               fp32, (L-1, T)      for M3 velocity, M5 path
    step_cos                fp16, (L-2, T)      for M3 curvature
    norm_h_29, norm_rms_h_29, norm_h_norm   fp32, (T,)  per-token refs

Derived on-the-fly (NOT stored separately):
    res_norm = sqrt(||a||^2 + ||b||^2 - 2*||a||*||b||*cos)   (law of cosines)

Dropped fields:
    entropy_ell, top1_prob_ell — lm_head × 32 layers too expensive.
    Computable post-hoc from Tier 3 raw subset if needed.

Tier 1 (all windows): wide-form parquet with 14 list-columns (one per cell).

Resume support: per-window done_mask in parquet header.
Target wall on H200 batch=1: ~85-90 min (matches gDTR Phase 1.6 rate).
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

sys.path.insert(0, "/root/gDTR")

# ─── Constants ──────────────────────────────────────────────────────────────
L_STAR = 29
N_LAYERS = 32
HIDDEN_SIZE = 4096


def settling_running_min_threshold(D_per_layer: np.ndarray, gamma: float) -> np.ndarray:
    """First ell where running-min(D[:ell+1]) <= gamma. -1 if never."""
    rmin = np.minimum.accumulate(D_per_layer, axis=0)
    settled = rmin <= gamma
    c = np.full(D_per_layer.shape[1], -1, dtype=np.int32)
    any_settled = settled.any(axis=0)
    c[any_settled] = np.argmax(settled, axis=0)[any_settled]
    return c


def settling_geo(g_per_layer: np.ndarray, tau: float) -> np.ndarray:
    """First ell where g[k] <= tau for ALL k in [ell, end]."""
    below = g_per_layer <= tau
    # reverse cumulative-OR over not-below gives 'violation in future'
    rev_or = np.maximum.accumulate((~below)[::-1], axis=0)[::-1]
    settled = ~rev_or
    c = np.full(g_per_layer.shape[1], -1, dtype=np.int32)
    any_settled = settled.any(axis=0)
    c[any_settled] = np.argmax(settled, axis=0)[any_settled]
    return c


@torch.no_grad()
def compute_window(bundle, seq: str):
    """Forward + compute the minimal scalar set needed for 14-cell settling.

    Returns dict of numpy arrays:
        cos_refA, cos_refB, cos_refC      (L, T) fp16
        norm_h_ell                          (L, T) fp32
        step_norm                           (L-1, T) fp32
        step_cos                            (L-2, T) fp16
        norm_h_29, norm_rms_h_29, norm_h_norm   (T,) fp32
    Plus the GPU-resident tensors for optional Tier 3 dumping:
        h_blocks_gpu, h_norm_gpu, h_blocks_rms_gpu     (kept on GPU)
    """
    from src.constants_evo2 import N_LAYERS as L, HIDDEN_SIZE as H
    from src.model_loader_evo2 import tokenize
    from src.logit_lens_evo2 import extract_hidden_states, all_layer_names

    input_ids = tokenize(seq, bundle, device="cuda")
    layer_names = all_layer_names()
    hs = extract_hidden_states(bundle, input_ids, save_layers=layer_names)

    T = hs["norm"].shape[1]
    h_blocks = torch.stack([hs[f"blocks.{ell}"][0] for ell in range(L)], dim=0).float()  # (L, T, H)
    h_norm = hs["norm"][0].float()  # (T, H)
    h_29 = h_blocks[L_STAR]  # (T, H)

    # Batched RMSNorm: single call on (L*T, H) instead of 32 calls
    h_flat = h_blocks.reshape(L * T, H).to(bundle.embedding_weight.dtype)
    h_blocks_rms = bundle.norm(h_flat).reshape(L, T, H).float()
    h_29_rms = h_blocks_rms[L_STAR]  # (T, H)

    # Cosines (3 refs)
    cos_A = F.cosine_similarity(h_blocks, h_29.unsqueeze(0).expand(L, -1, -1), dim=-1)
    cos_B = F.cosine_similarity(h_blocks_rms, h_29_rms.unsqueeze(0).expand(L, -1, -1), dim=-1)
    cos_C = F.cosine_similarity(h_blocks, h_norm.unsqueeze(0).expand(L, -1, -1), dim=-1)

    # Magnitudes
    norm_h_ell = torch.linalg.vector_norm(h_blocks, dim=-1)  # (L, T)
    norm_h_29 = torch.linalg.vector_norm(h_29, dim=-1)  # (T,)
    norm_rms_h_29 = torch.linalg.vector_norm(h_29_rms, dim=-1)
    norm_h_norm = torch.linalg.vector_norm(h_norm, dim=-1)

    # Steps
    deltas = h_blocks[1:] - h_blocks[:-1]  # (L-1, T, H)
    step_norm = torch.linalg.vector_norm(deltas, dim=-1)
    step_cos = F.cosine_similarity(deltas[1:], deltas[:-1], dim=-1)  # (L-2, T)

    out = {
        "cos_refA": cos_A.cpu().numpy().astype(np.float16),
        "cos_refB": cos_B.cpu().numpy().astype(np.float16),
        "cos_refC": cos_C.cpu().numpy().astype(np.float16),
        "norm_h_ell": norm_h_ell.cpu().numpy().astype(np.float32),
        "step_norm": step_norm.cpu().numpy().astype(np.float32),
        "step_cos": step_cos.cpu().numpy().astype(np.float16),
        "norm_h_29": norm_h_29.cpu().numpy().astype(np.float32),
        "norm_rms_h_29": norm_rms_h_29.cpu().numpy().astype(np.float32),
        "norm_h_norm": norm_h_norm.cpu().numpy().astype(np.float32),
    }
    # GPU tensors kept for Tier 3 if subset
    gpu = {
        "h_blocks": h_blocks,
        "h_norm": h_norm,
        "h_blocks_rms": h_blocks_rms,
    }
    return out, gpu, T


def res_norm_from_cos(norm_a_LT, norm_b_T, cos_LT):
    """Law of cosines: ||a - b|| = sqrt(||a||^2 + ||b||^2 - 2 ||a|| ||b|| cos).

    norm_a_LT (L, T), norm_b_T (T,), cos_LT (L, T) -> (L, T)
    """
    a2 = norm_a_LT.astype(np.float32) ** 2
    b2 = (norm_b_T.astype(np.float32) ** 2)[None, :]
    cross = norm_a_LT.astype(np.float32) * norm_b_T.astype(np.float32)[None, :] * cos_LT.astype(np.float32)
    return np.sqrt(np.maximum(a2 + b2 - 2 * cross, 0.0))


def compute_14_cells(scalars: dict, gamma: dict) -> dict:
    """Compute 14 cells' settling depth from minimal scalars."""
    L = N_LAYERS
    T = scalars["norm_h_ell"].shape[1]
    cells = {}

    # M1 c_dir x 3 refs (1 - cos)
    for ref in ("refA", "refB", "refC"):
        D_dir = 1.0 - scalars[f"cos_{ref}"].astype(np.float32)
        cells[f"M1_dir_{ref}"] = settling_running_min_threshold(D_dir, gamma[f"D_dir_{ref}"])

    # M2 c_mag x {A, C} (B is degenerate by construction)
    norm_ell = scalars["norm_h_ell"]
    for ref, ref_norm_key in (("refA", "norm_h_29"), ("refC", "norm_h_norm")):
        norm_ref = scalars[ref_norm_key]
        r = norm_ell / (norm_ref[None, :] + 1e-12)
        D_mag = np.abs(r - 1.0)
        cells[f"M2_mag_{ref}"] = settling_running_min_threshold(D_mag, gamma[f"D_mag_{ref}"])

    # M3 c_geo (reference-free)
    v_mean = gamma["_geo_v_mean"]; v_std = gamma["_geo_v_std"]
    k_mean = gamma["_geo_kappa_mean"]; k_std = gamma["_geo_kappa_std"]
    step_n = scalars["step_norm"]   # (L-1, T)
    step_c = scalars["step_cos"].astype(np.float32)   # (L-2, T)
    v = step_n / (norm_ell[: L - 1] + 1e-12)  # (L-1, T)
    kappa = 1.0 - step_c                       # (L-2, T)
    v_use = v[: L - 2]
    g = (v_use - v_mean) / (v_std + 1e-12) + (kappa - k_mean) / (k_std + 1e-12)
    cells["M3_geo"] = settling_geo(g, gamma["D_geo_at_ell26"])

    # M4 c_M Mahalanobis — deferred (needs Sigma access)
    cells["M4_mahal_refA"] = np.full(T, -1, dtype=np.int32)
    cells["M4_mahal_refB"] = np.full(T, -1, dtype=np.int32)
    cells["M4_mahal_refC"] = np.full(T, -1, dtype=np.int32)

    # M5 c_tau x 3 refs (calibrated at ell=27)
    # tau(ell) = remaining_path / ||h_ell - h_ref||;  derive res via law of cosines.
    path_cum = np.cumsum(step_n[:L_STAR], axis=0)  # (L*, T) cumsum 0..L*-1
    path_total = path_cum[L_STAR - 1]              # (T,)
    remaining = np.zeros((L_STAR, T), dtype=np.float32)
    remaining[0] = path_total
    remaining[1:] = path_total[None, :] - path_cum[: L_STAR - 1]

    for ref, norm_ref_key in (("refA", "norm_h_29"), ("refB", "norm_rms_h_29"), ("refC", "norm_h_norm")):
        cos_ref = scalars[f"cos_{ref}"]
        # For Ref B numerator we keep RAW path (Option A in design_decisions.md).
        # Path consistency under fully-normed trajectory is future work.
        norm_a_LT = norm_ell if ref != "refB" else None
        if ref == "refB":
            # RMSNormed h_ell, denominator is ||RMSNorm(h_ell) - RMSNorm(h_29)||
            # We approximate using law of cosines with norm_rms_h_ell. Since norm_rms_h_ell
            # is nearly constant (= ||gamma||), we use norm_rms_h_29 as a proxy for all layers.
            # This is reasonable per the metric definition (Ref B mostly diagnostic).
            norm_a_LT_proxy = scalars["norm_rms_h_29"][None, :] * np.ones((L, T), dtype=np.float32)
            res = res_norm_from_cos(norm_a_LT_proxy, scalars["norm_rms_h_29"], cos_ref)
        else:
            res = res_norm_from_cos(norm_ell, scalars[norm_ref_key], cos_ref)
        denom = res[: L_STAR] + 1e-12
        tau = remaining / denom
        cells[f"M5_tau_{ref}"] = settling_running_min_threshold(tau, gamma[f"D_tau_{ref}"])

    return cells


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows-tsv", type=Path,
                        default=Path("/root/gDTR/data/baselines/chr22_windows.tsv"))
    parser.add_argument("--fasta", type=Path,
                        default=Path("/root/gDTR/data/reference/chr22.fa"))
    parser.add_argument("--subset-file", type=Path,
                        default=Path("/root/TDiG/data/subset_window_ids.json"))
    parser.add_argument("--gamma-file", type=Path,
                        default=Path("/root/TDiG/data/cache/population_stats/gamma_calibration.json"))
    parser.add_argument("--out-dir", type=Path,
                        default=Path("/root/TDiG/data/cache/chr22"))
    parser.add_argument("--max-windows", type=int, default=0)
    parser.add_argument("--log-every", type=int, default=200)
    parser.add_argument("--save-every", type=int, default=500)
    parser.add_argument("--tier3-tokens-per-window", type=int, default=600)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[setup] loading windows / FASTA / gamma / subset", flush=True)
    df_w = pd.read_csv(args.windows_tsv, sep="\t")
    if args.max_windows > 0:
        df_w = df_w.head(args.max_windows).reset_index(drop=True)
    N = len(df_w)
    print(f"[setup] N={N} windows")

    import pysam
    fasta = pysam.FastaFile(str(args.fasta))

    gamma = json.loads(args.gamma_file.read_text())
    subset = json.loads(args.subset_file.read_text())
    subset_ids = set(subset["chr22"])
    print(f"[setup] {len(subset_ids)} subset windows for Tier 2+3")

    print(f"[setup] loading Evo 2", flush=True)
    from src.constants_evo2 import N_LAYERS as L, HIDDEN_SIZE as H
    from src.model_loader_evo2 import load_evo2
    bundle = load_evo2()
    print(f"[setup] model loaded, variant={bundle.loaded_variant}", flush=True)

    # --- Output paths ---
    tier1_path = args.out_dir / "tier1_settling.parquet"
    tier2_path = args.out_dir / "tier2_scalars_subset.h5"   # subset only
    tier3_path = args.out_dir / "tier3_raw.h5"               # subset only
    meta_path = args.out_dir / "window_metadata.parquet"

    # --- Tier 2 + 3 h5 prep (subset only) ---
    N_subset = len(subset_ids)
    T_typ = 6000
    T_sub = args.tier3_tokens_per_window
    subset_local_idx = {wid: i for i, wid in enumerate(sorted(subset_ids))}

    if not tier2_path.exists():
        with h5py.File(tier2_path, "w") as h5:
            # cos: fp16; norms/steps: fp32 (huge magnitudes overflow fp16)
            h5.create_dataset("cos_refA",     shape=(N_subset, L, T_typ), dtype="float16")
            h5.create_dataset("cos_refB",     shape=(N_subset, L, T_typ), dtype="float16")
            h5.create_dataset("cos_refC",     shape=(N_subset, L, T_typ), dtype="float16")
            h5.create_dataset("norm_h_ell",   shape=(N_subset, L, T_typ), dtype="float32")
            h5.create_dataset("step_norm",    shape=(N_subset, L - 1, T_typ), dtype="float32")
            h5.create_dataset("step_cos",     shape=(N_subset, L - 2, T_typ), dtype="float16")
            h5.create_dataset("norm_h_29",      shape=(N_subset, T_typ), dtype="float32")
            h5.create_dataset("norm_rms_h_29",  shape=(N_subset, T_typ), dtype="float32")
            h5.create_dataset("norm_h_norm",    shape=(N_subset, T_typ), dtype="float32")
            h5.create_dataset("window_idx", shape=(N_subset,), dtype="int64")
            h5.create_dataset("done_mask",  shape=(N_subset,), dtype="uint8")
            h5["window_idx"][:] = sorted(subset_ids)

    if not tier3_path.exists():
        with h5py.File(tier3_path, "w") as h5:
            h5.create_dataset("raw_h_ell",            shape=(N_subset, L, T_sub, H), dtype="float32")
            h5.create_dataset("raw_h_ell_rmsnormed",  shape=(N_subset, L, T_sub, H), dtype="float16")
            h5.create_dataset("raw_h_norm",            shape=(N_subset, T_sub, H), dtype="float16")
            h5.create_dataset("window_idx",  shape=(N_subset,), dtype="int64")
            h5.create_dataset("token_stride", shape=(N_subset,), dtype="int32")
            h5.create_dataset("done_mask",   shape=(N_subset,), dtype="uint8")
            h5["window_idx"][:] = sorted(subset_ids)

    # --- Tier 1 in-memory accumulator (write batched) ---
    tier1_records = []

    # --- Resume from existing parquet if any ---
    completed_set = set()
    if tier1_path.exists():
        existing = pd.read_parquet(tier1_path)
        completed_set = set(existing["window_idx"].tolist())
        tier1_records = existing.to_dict(orient="records")
        print(f"[resume] {len(completed_set)} windows already done", flush=True)

    t_start = time.time()
    processed = 0

    for i, row in df_w.iterrows():
        wid = int(row["window_idx"])
        if wid in completed_set:
            continue
        chrom = row["chrom"]; start = int(row["start"]); end = int(row["end"])

        try:
            seq = fasta.fetch(chrom, start, end).upper()
            scalars, gpu_tensors, T = compute_window(bundle, seq)
            cells = compute_14_cells(scalars, gamma)

            # Tier 1 record
            rec = {"window_idx": wid, "chrom": chrom, "start": start, "end": end, "T": T}
            for cell_id, c_arr in cells.items():
                rec[cell_id] = c_arr[:T].astype(np.int32).tolist()
            tier1_records.append(rec)

            # Subset path: write Tier 2 + Tier 3
            if wid in subset_ids:
                li = subset_local_idx[wid]
                with h5py.File(tier2_path, "a") as h5:
                    def pad(arr, target_T):
                        if arr.shape[-1] >= target_T:
                            return arr[..., :target_T]
                        pads = np.zeros(arr.shape[:-1] + (target_T - arr.shape[-1],), dtype=arr.dtype)
                        return np.concatenate([arr, pads], axis=-1)
                    h5["cos_refA"][li]    = pad(scalars["cos_refA"], T_typ)
                    h5["cos_refB"][li]    = pad(scalars["cos_refB"], T_typ)
                    h5["cos_refC"][li]    = pad(scalars["cos_refC"], T_typ)
                    h5["norm_h_ell"][li]  = pad(scalars["norm_h_ell"], T_typ)
                    h5["step_norm"][li]   = pad(scalars["step_norm"], T_typ)
                    h5["step_cos"][li]    = pad(scalars["step_cos"], T_typ)
                    h5["norm_h_29"][li]    = pad(scalars["norm_h_29"], T_typ)
                    h5["norm_rms_h_29"][li]= pad(scalars["norm_rms_h_29"], T_typ)
                    h5["norm_h_norm"][li]  = pad(scalars["norm_h_norm"], T_typ)
                    h5["done_mask"][li] = 1

                # Tier 3 raw subset
                stride = max(1, T // args.tier3_tokens_per_window)
                pos_idx = np.arange(0, T, stride)[: args.tier3_tokens_per_window]
                if len(pos_idx) < args.tier3_tokens_per_window:
                    pos_idx = np.pad(pos_idx,
                                     (0, args.tier3_tokens_per_window - len(pos_idx)),
                                     mode="edge")
                pos_t = torch.as_tensor(pos_idx, dtype=torch.long, device=gpu_tensors["h_blocks"].device)
                raw = gpu_tensors["h_blocks"][:, pos_t, :].detach().cpu().numpy().astype(np.float32)
                raw_rms = gpu_tensors["h_blocks_rms"][:, pos_t, :].detach().cpu().numpy().astype(np.float16)
                raw_norm = gpu_tensors["h_norm"][pos_t, :].detach().cpu().numpy().astype(np.float16)
                with h5py.File(tier3_path, "a") as h5:
                    h5["raw_h_ell"][li] = raw
                    h5["raw_h_ell_rmsnormed"][li] = raw_rms
                    h5["raw_h_norm"][li] = raw_norm
                    h5["token_stride"][li] = stride
                    h5["done_mask"][li] = 1

            # Free GPU
            del gpu_tensors
            torch.cuda.empty_cache()
            processed += 1

            if processed % args.log_every == 0:
                elapsed = time.time() - t_start
                rate = processed / elapsed
                eta = (N - len(completed_set) - processed) / rate / 60
                gpu_peak = torch.cuda.max_memory_allocated() / 1e9
                print(f"  [{len(completed_set)+processed}/{N}] rate={rate:.2f} win/s ETA={eta:.1f}min GPU_peak={gpu_peak:.1f}GB", flush=True)

            if processed % args.save_every == 0:
                tmp = tier1_path.with_suffix(".tmp.parquet")
                pd.DataFrame(tier1_records).to_parquet(tmp, index=False)
                tmp.replace(tier1_path)

        except Exception as e:
            print(f"  [ERR window {wid}] {type(e).__name__}: {e}", flush=True)
            raise

    # Final save
    pd.DataFrame(tier1_records).to_parquet(tier1_path, index=False)

    # Metadata
    df_w[["window_idx", "chrom", "start", "end", "gc_content", "n_fraction",
          "n_coding_exon", "n_intron", "n_5utr", "n_3utr", "n_splice",
          "n_intergenic"]].to_parquet(meta_path, index=False)

    prov = {
        "script": "15_chr22_forward.py",
        "host": platform.node(),
        "n_windows_total": int(N),
        "n_completed_this_run": int(processed),
        "n_subset": N_subset,
        "wall_minutes": (time.time() - t_start) / 60,
        "model_variant": bundle.loaded_variant,
        "batch_size": 1,
        "tier1_parquet": str(tier1_path),
        "tier2_h5_subset_only": str(tier2_path),
        "tier3_h5_subset_only": str(tier3_path),
        "metadata_parquet": str(meta_path),
        "gamma_source": str(args.gamma_file),
        "subset_source": str(args.subset_file),
        "notes": [
            "Tier 2 stored only for the 100 subset windows (storage budget).",
            "Tier 3 raw_h_ell fp32 (Evo 2 raw magnitudes ~ 2e10 overflow fp16).",
            "M4 Mahalanobis settling deferred (needs Sigma load + 2nd pass).",
            "Entropy / top1_prob dropped from this iteration (lm_head x 32 too expensive).",
            "M5 Ref B uses RAW path numerator + normed denominator (Option A; design decision).",
        ],
    }
    (args.out_dir / "_provenance.json").write_text(json.dumps(prov, indent=2))
    (args.out_dir / "_done").write_text(json.dumps({"ok": True,
                                                     "n_completed": int(processed),
                                                     "wall_minutes": prov["wall_minutes"]},
                                                    indent=2))
    print(f"[done] {args.out_dir}  wall={prov['wall_minutes']:.2f}min")


if __name__ == "__main__":
    main()
