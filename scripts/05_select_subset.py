"""Pick 100 representative chr22 windows for Tier 3 raw storage.

LOCAL one-time script. Reads gDTR-PoC chr22_cache.h5 metadata to stratify
window selection across all 7 context classes plus boundary regions.

Output:
    data/subset_window_ids.json   # COMMITTED to repo (small, < 5 KB)

The 100-window subset is stable across the pipeline — same windows used
for Tier 3 raw storage in chr22 (15) and chr17 (16) for cross-chromosome
comparison.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-windows", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--source-cache", type=Path,
                        default=Path("../ICML/results/phase1.6/chr22_cache.h5"),
                        help="Local mirror or server-accessible chr22 cache for metadata")
    parser.add_argument("--out", type=Path, default=Path("data/subset_window_ids.json"))
    args = parser.parse_args()

    # Selection criteria:
    #   - 14 windows × 7 context classes = 98 (stratified by majority context)
    #   - 2 boundary windows (intron-exon junctions known to be interesting)
    raise NotImplementedError("Stratified window selection from chr22 metadata")


if __name__ == "__main__":
    main()
