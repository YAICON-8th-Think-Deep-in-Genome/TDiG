"""Population statistics + Sigma estimation from chr22 sanity sequences.

SERVER script. Runs BEFORE all other forwards. Locks gamma calibration.

Inputs:
    Evo 2 7B weights (HF cache)
    chr22 GRCh38 + GENCODE v44 (for sanity-sequence selection)

Outputs (all to /root/TDiG/data/cache/population_stats/):
    per_layer_mean.npy            (32, 4096) fp32
    per_layer_std.npy             (32, 4096) fp32
    sigma_diagonal.npy            (32, 4096) fp32       # M4 fast path
    sigma_ledoit_wolf.npy         (32, 4096, 4096) fp32 # M4 full (~2 GB)
    sigma_pca_top128.npy          (32, 128, 4096) fp32  # M4 reduced
    sigma_inv_diag.npy            (32, 4096) fp32       # precomputed
    gamma_calibration.json        {gamma_dir, gamma_mag, gamma_M, gamma_tau}
    _provenance.json              run metadata

Approach: 100 sanity sequences × 6 kb context × batch=16 (~5 min on H200).
Per-layer running statistics computed online to avoid materializing the
full activation tensor.

gamma calibration uses q70 at the penultimate layer (L*-1 = 28) — the same
protocol that locks gDTR-PoC gamma_cos = 0.397 in Phase 1.4.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def estimate_sigma_diagonal(hidden_per_layer):
    raise NotImplementedError


def estimate_sigma_ledoit_wolf(hidden_per_layer):
    """Ledoit-Wolf shrinkage on a 4096x4096 covariance.

    Uses sklearn.covariance.LedoitWolf. Cost ~3 GB peak RAM per layer.
    """
    raise NotImplementedError


def estimate_sigma_pca(hidden_per_layer, k=128):
    """Top-k PCA components for reduced Mahalanobis."""
    raise NotImplementedError


def calibrate_gamma_q70(distances_at_penultimate):
    """q70 of distance distribution at layer 28 (L*-1)."""
    raise NotImplementedError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-sanity", type=int, default=100)
    parser.add_argument("--seq-length", type=int, default=6000)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--out-dir", type=Path, default=Path("/root/TDiG/data/cache/population_stats"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sample 100 chr22 sequences (50 GC-matched + 50 dinucleotide-shuffled, same as gDTR Phase 1.4)
    # 2. Forward through Evo 2 7B (batch=16), capture h_ell for ell=0..31 + h_norm + h_29 raw
    # 3. Per-layer mean / std (online accumulation)
    # 4. Sigma estimates (three options)
    # 5. Compute distances for all 14 cells at layer 28, q70 -> gamma values
    # 6. Save NPYs + gamma_calibration.json + _provenance.json
    raise NotImplementedError("Population stats + Sigma + gamma calibration")


if __name__ == "__main__":
    main()
