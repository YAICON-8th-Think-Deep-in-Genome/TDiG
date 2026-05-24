"""PHASE A — batched-equivalence smoke test.

Runs 10 chr22 windows at batch=8 and at batch=1, asserts numerical
equivalence within epsilon=1e-5 for all stored fields.

If pass, the batched code path is verified for production use.
If fail, fall back to smaller batch size or batch=1; document the failure
in _phase_a_smoke.json.

SERVER script. ~5 min. Gates PHASE B.

Output:
    /root/TDiG/data/cache/_phase_a_smoke.json   # pass/fail + per-field max diff
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def forward_with_batch(window_ids, batch_size):
    """Run forward over the given window_ids with the specified batch size.

    Returns a dict of all Tier-2 scalar arrays + Tier-3 raw subset.
    Layered scalars: cos_refA/B/C, res_norm_refA/B/C, norm_h_ell_raw, step_norm, step_cos, entropy_ell, top1_prob_ell.
    """
    raise NotImplementedError


def compare_outputs(out_batch_n, out_batch_1, eps=1e-5):
    """Per-field max abs difference. Return dict {field: max_diff, ok: bool}."""
    raise NotImplementedError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-windows", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epsilon", type=float, default=1e-5)
    parser.add_argument("--out", type=Path, default=Path("/root/TDiG/data/cache/_phase_a_smoke.json"))
    args = parser.parse_args()

    # 1. Select 10 windows from gDTR Phase 1.6 indexing (deterministic)
    # 2. Run forward at batch=batch_size
    # 3. Run forward at batch=1 (same 10 windows)
    # 4. Compare every Tier-2 field — max abs diff < epsilon required
    # 5. Write JSON verdict + per-field diff statistics

    # Decision logic (encoded in JSON output, read by run_pipeline.sh):
    #   if all_fields_ok:
    #       phase_a_pass: true
    #       batched_path_verified: true
    #   else:
    #       phase_a_pass: false
    #       recommend_batch_size: <decreased>
    raise NotImplementedError("Smoke test")


if __name__ == "__main__":
    main()
