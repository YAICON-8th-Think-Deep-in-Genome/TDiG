"""PHASE B — chr22 main forward + optional concurrent cross-arch.

SERVER script. ~15–20 min on H200 with batch=8–16.

12,978 chr22 windows × 6 kb. For each (window, layer, token) computes Tier 2
scalars; for the 100 representative windows (from 05_select_subset.py) stores
Tier 3 raw h_ell subsampled to 600 tokens per window.

CLI:
    --batch-size N        explicit batch size (default: auto-probe)
    --with-crossarch      run HyenaDNA-large + NT-v2 500M + DNABERT-2 117M
                          concurrently on Stream B (saves ~10 min vs sequential)
    --resume              skip already-completed windows
    --windows-file PATH   limit to specific window IDs (for debugging)

Outputs:
    /root/TDiG/data/cache/chr22/
        tier1_settling.parquet           14 cells x ~78M tokens
        tier2_scalars.h5                 11 fields x per-layer per-token
        tier3_raw.h5                     100 windows raw h_ell (subsampled)
        window_metadata.parquet
        _done                            completion marker
        _provenance.json                 model SHA, batch size, wall time, etc.

When --with-crossarch is set, additionally writes:
    /root/TDiG/data/cache/crossarch/
        hyenadna_tier1.parquet
        nt_v2_tier1.parquet
        dnabert2_tier1.parquet
        per_model_summary.json

Resume semantics:
    Per-window _done flags inside tier2_scalars.h5 attrs. On --resume, skip
    windows where window_done[i] == 1.

Sanity gate (run automatically at end):
    Splice donor vs intron Cohen's d for M1 x Ref C must be -0.43 +/- 0.05
    (matches gDTR-PoC phase1.6/gate_b.json). If outside tolerance, the script
    exits non-zero and run_pipeline.sh halts before PHASE C.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def probe_optimal_batch_size(model, seq_length, vram_headroom_gb=10.0):
    """Try batch sizes 1, 2, 4, 8, 16 and return the largest that fits."""
    raise NotImplementedError


def main_chr22_stream(args, stream_a):
    """Stream A — Evo 2 chr22 main forward.

    For each batch:
      1. forward h_0..h_31, h_norm
      2. compute Tier 2 scalars (cos_refA/B/C, res_norm_refA/B/C, etc.)
      3. compute Tier 1 settling depths from scalars + sanity gate values
      4. async write to h5
    """
    raise NotImplementedError


def crossarch_concurrent_stream(args, stream_b):
    """Stream B — HyenaDNA + NT-v2 + DNABERT chr22 forward (concurrent)."""
    raise NotImplementedError


def sanity_gate_check(out_dir):
    """Splice donor vs intron Cohen's d on M1 x Ref C. Returns (d, passed)."""
    raise NotImplementedError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=0, help="0 = auto-probe")
    parser.add_argument("--with-crossarch", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--windows-file", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=Path("/root/TDiG/data/cache/chr22"))
    parser.add_argument("--subset-file", type=Path, default=Path("/root/TDiG/data/subset_window_ids.json"))
    args = parser.parse_args()

    # 1. Load population_stats/gamma_calibration.json (must exist from step 10)
    # 2. If batch-size == 0, probe optimal
    # 3. Two CUDA streams if --with-crossarch:
    #    stream A: Evo 2 chr22
    #    stream B: HyenaDNA + NT-v2 + DNABERT (interleaved batches)
    # 4. Async I/O writer thread for h5
    # 5. End: sanity_gate_check; write _done + _provenance.json
    raise NotImplementedError("chr22 batched forward + optional concurrent cross-arch")


if __name__ == "__main__":
    main()
