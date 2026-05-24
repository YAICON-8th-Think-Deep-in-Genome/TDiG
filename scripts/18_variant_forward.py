"""PHASE C (part 2) — ClinVar variant forward with kv-cache reuse.

SERVER script. ~10–15 min on H200 with batching + kv-cache reuse.
Concurrent with 16_chr17_forward.py.

10,910 ClinVar variants in 15 cancer genes × {ref, alt} sequences.
Variant context: variant position ± 3 kb (matches gDTR-PoC Phase 3).

kv-cache reuse: for each variant, ref and alt sequences differ at exactly
one position. The kv-cache for tokens up to the variant position is
computable ONCE on the ref sequence, then reused for the alt sequence
(only the position-onward tokens need new forward passes). This gives
~2x speedup vs naive independent ref/alt forwards.

Outputs:
    /root/TDiG/data/cache/variants/
        variant_h_ell_ref.h5             (10910, 32, 4096) fp16  ~2.9 GB
                                          h_ell at variant position only, ref seq
        variant_h_ell_alt.h5             (10910, 32, 4096) fp16  ~2.9 GB
                                          h_ell at variant position only, alt seq
        variant_delta_norms.parquet      per layer + ±5 position scalars
        variant_metadata.parquet         gene, chr, pos, ref, alt, class, consequence
        _done
        _provenance.json

For each variant, compute and store:
    per (layer, position-in-±5) scalars:
        delta_norm_2:    ||h_ell_alt - h_ell_ref||_2
        delta_cos:       1 - cos(h_ell_alt, h_ell_ref)
        h_norm_ref:      ||h_ell_ref||
        h_norm_alt:      ||h_ell_alt||
    raw h_ell at variant position only (for T-B downstream and case studies):
        h_ell_ref[v], h_ell_alt[v] for all 32 layers

CLI:
    --memory-budget-gb     Cooperative cap (default 30 to coexist with chr17)
    --batch-size N         Default: auto-probe respecting memory budget
    --resume               Skip done variants
"""

from __future__ import annotations

import argparse
from pathlib import Path


def shared_prefix_kv_cache(model, ref_seq, variant_pos):
    """Forward ref_seq[:variant_pos], save kv-cache for reuse with alt."""
    raise NotImplementedError


def forward_with_kv_reuse(model, alt_seq, variant_pos, cached_kv):
    """Forward alt_seq using cached kv for tokens before variant_pos."""
    raise NotImplementedError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--variants-file", type=Path,
                        default=Path("/root/gDTR/results/phase3_main/variants_features.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("/root/TDiG/data/cache/variants"))
    parser.add_argument("--memory-budget-gb", type=float, default=30.0)
    args = parser.parse_args()

    # 1. Load variants_features.csv (10,910 variants metadata)
    # 2. For each variant: gather ±3kb context, prepare ref + alt sequences
    # 3. Batch variants whose ref-prefix is identical (same chr+pos+upstream)
    # 4. kv-cache prefix forward, then alt forward reusing cached kv
    # 5. Extract h_ell at variant position +/- 5
    # 6. Compute delta scalars, save raw vector at variant position
    raise NotImplementedError("ClinVar variant forward with kv-cache reuse")


if __name__ == "__main__":
    main()
