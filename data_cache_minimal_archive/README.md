# Forward-Pass Artifacts Archive

These are the Evo 2 7B forward-pass outputs that all 19 analyses in
`../results/` derive from. Pulled from `digitalocean-gpu` 2026-05-25 before
server shutdown — preserves full reproducibility without re-running the ~8h
GPU forward pipeline (`scripts/15_chr22_forward.py`, `16_chr17_forward.py`,
`18_variant_forward.py`).

## Contents (after reassembly, ~1.1 GB uncompressed)

```
data_cache_minimal/
├── chr22_tier1.parquet                  (283 MB) 17 cells × 12,978 windows
├── chr17_tier1.parquet                  (600 MB) 17 cells × 27,586 windows
├── variant_scalars.parquet              (11 MB)  10,910 variants × per-layer ΔH
├── chr22_metadata.parquet               (333 KB) window coordinates
├── chr17_metadata.parquet               (695 KB) window coordinates
└── population_stats/
    ├── gamma_calibration_v2.json         γ thresholds for all 17 cells
    ├── gamma_calibration.json            v1 thresholds (legacy)
    ├── sigma_ref_inv_A.npy               (64 MB) Σ_ref⁻¹ for M4_set refA
    ├── sigma_ref_inv_B.npy               (64 MB) Σ_ref⁻¹ for M4_set refB
    ├── sigma_ref_inv_C.npy               (64 MB) Σ_ref⁻¹ for M4_set refC
    ├── h_norm_mean.npy / std.npy         (16 KB ea) global h_norm stats
    ├── per_layer_mean.npy / std.npy      (512 KB ea) per-layer stats
    └── sigma_diagonal.npy / inv_diag.npy (512 KB ea) diagonal-only Σ
```

## Reassembly

```bash
cd /Users/yoonjincho/Project/TDiG/data_cache_minimal_archive/
cat data_cache_minimal.tar.gz.part-* | tar xzf -
ls ../data_cache_minimal/          # extracted here
```

## Excluded (server-only, 47 GB total)

- `chr22_v2/tier3_raw_v2.h5` — raw + RMSnormed hidden states (47 GB)
- `chr17/tier3_raw_v2.h5` — same for chr17
- `variants/variant_h_ell_ref.h5` + `_alt.h5` — variant ref/alt hidden states (5.4 GB × 2)
- `chr*_v2/tier2_scalars_subset_v2.h5` — per-(window, layer, token) scalars (614 MB ea)

To regenerate any of the excluded h5 files: re-run `scripts/15_chr22_forward.py`
(chr22) or `16_chr17_forward.py` (chr17) or `18_variant_forward.py` (variants)
on H200 GPU. Wall time: chr22 ~3h, chr17 ~7h, variants ~1.5h. Total ~12h.

## Provenance

- Source: digitalocean-gpu `/root/TDiG/data/cache/{chr22_v2, chr17, variants, population_stats}/`
- Pulled: 2026-05-25 ~14:18 KST via rsync
- Model: Evo 2 7B (arcinstitute/evo2_7b_base, 8K context, no FP8)
- Calibration: 100 sanity sequences (`scripts/10b_calibrate_v2.py`)
- Cell definitions: see `scripts/15_chr22_forward.py` `compute_v2_settling()`
