"""Pick 100 representative chr22 windows for Tier 3 raw storage.

Runs on SERVER (needs gDTR chr22_windows.tsv). Selection: stratify by
per-window majority context to ensure all 7 context classes are represented.

Output:
    data/subset_window_ids.json
        {"chr22": [window_idx, ...], "selection_seed": 42, "stratification": {...}}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


CONTEXT_COLS = [
    "n_coding_exon",
    "n_intron",
    "n_5utr",
    "n_3utr",
    "n_splice",
    "n_intergenic",
]


def select_stratified(df: pd.DataFrame, n_total: int, seed: int) -> dict:
    """Pick windows representative across context classes.

    Strategy:
        For each context column, take the top-N windows by that column's count.
        Combine + dedupe. Boundary picks fill to n_total.
    """
    rng = np.random.default_rng(seed)
    per_context = n_total // (len(CONTEXT_COLS) + 1)  # +1 boundary slack
    picks = set()
    contribution = {}

    for col in CONTEXT_COLS:
        top = df.nlargest(per_context, col)["window_idx"].tolist()
        contribution[col] = top
        picks.update(top)

    # Fill remainder with boundary-rich windows (mix of multiple contexts)
    df_b = df.copy()
    df_b["context_diversity"] = (df_b[CONTEXT_COLS] > 0).sum(axis=1)
    boundary_candidates = df_b.nlargest(per_context * 3, "context_diversity")["window_idx"].tolist()
    contribution["boundary_mix"] = []
    for w in boundary_candidates:
        if len(picks) >= n_total:
            break
        if w not in picks:
            picks.add(w)
            contribution["boundary_mix"].append(w)

    # Random fill if still short
    remaining = df[~df["window_idx"].isin(picks)]["window_idx"].tolist()
    rng.shuffle(remaining)
    contribution["random_fill"] = []
    for w in remaining:
        if len(picks) >= n_total:
            break
        picks.add(w)
        contribution["random_fill"].append(int(w))

    return {
        "selected": sorted(int(w) for w in picks),
        "selection_seed": seed,
        "stratification": {k: [int(x) for x in v] for k, v in contribution.items()},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-windows", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--windows-tsv",
        type=Path,
        default=Path("/root/gDTR/data/baselines/chr22_windows.tsv"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("/root/TDiG/data/subset_window_ids.json"),
    )
    args = parser.parse_args()

    df = pd.read_csv(args.windows_tsv, sep="\t")
    print(f"loaded {len(df)} chr22 windows")
    print(df[CONTEXT_COLS].describe().T)

    result = select_stratified(df, args.n_windows, args.seed)
    result_full = {
        "chr22": result["selected"],
        "n_windows": len(result["selected"]),
        "selection_seed": result["selection_seed"],
        "stratification": result["stratification"],
        "source": str(args.windows_tsv),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result_full, indent=2))
    print(f"\nwrote {len(result['selected'])} window IDs to {args.out}")


if __name__ == "__main__":
    main()
