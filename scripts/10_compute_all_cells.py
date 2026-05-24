"""S1 — compute all 14 settling cells in a single forward pass.

Inputs:
    data/cache/chr22_cache.h5 (and optionally chr17_cache.h5)

Outputs:
    results/settling_table.parquet
        Schema: token_id, position, context, metric_id, ref_id, c_value, layer-vector

For each token, we compute 14 (metric, reference) cells:
    M1 c_dir x {A, B, C} = 3
    M2 c_mag x {A, C}    = 2     (B reported separately as degenerate)
    M3 c_geo             = 1     (reference-free)
    M4 c_M   x {A, B, C} = 3
    M5 c_tau x {A, B, C} = 3
    M6 D_L2  x {A, C}    = 2     (consistency check)
    -----------------------
    Total                  14

All cells share the single forward pass; downstream processing is CPU.
"""

from __future__ import annotations


def main():
    """Entry point. Loads cache, computes all 14 cells, writes parquet."""
    raise NotImplementedError("S1 implementation")


if __name__ == "__main__":
    main()
