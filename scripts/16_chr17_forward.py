"""PHASE C (part 1) — chr17 batched forward.

SERVER script. ~25–35 min on H200 with batch=8–16.

27,586 chr17 windows × 6 kb. **Trimmed Tier 2** — only settling tables
(Tier 1) + 100-window raw subset (Tier 3) + chr17-specific stats are stored.
Per-layer Tier 2 scalars SKIPPED for chr17 due to storage budget (would
require ~140 GB).

Concurrent with 18_variant_forward.py on the same H200. The two share GPU
memory via cooperative allocation:
    chr17 owns ~80 GB (main forward batches)
    variants owns ~30 GB (smaller working set, kv-cache reuse)
    headroom: ~20 GB

Outputs:
    /root/TDiG/data/cache/chr17/
        tier1_settling.parquet
        tier3_raw.h5
        window_metadata.parquet
        _done
        _provenance.json

The chr17 subset (Tier 3) is selected to MIRROR the chr22 subset (same
context-class stratification) for cross-chromosome comparison.

CLI flags same shape as 15_chr22_forward.py (--batch-size, --resume).
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=Path("/root/TDiG/data/cache/chr17"))
    parser.add_argument("--memory-budget-gb", type=float, default=80.0,
                        help="Soft GPU memory cap for cooperative scheduling with 18_variant_forward.py")
    args = parser.parse_args()

    # 1. Load population_stats/gamma_calibration.json
    # 2. Auto-probe batch size respecting memory_budget_gb
    # 3. Iterate chr17 windows, write Tier 1 + Tier 3 (trimmed Tier 2)
    # 4. End: write _done + _provenance.json
    raise NotImplementedError("chr17 trimmed forward")


if __name__ == "__main__":
    main()
