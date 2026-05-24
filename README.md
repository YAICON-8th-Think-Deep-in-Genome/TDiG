# TDiG — Think Deep in Genome

**Multi-axis residual-stream settling analysis for genomic foundation models.**

This project extends the gDTR framework (see [companion repo](https://github.com/darejinn/gDTR-PoC)) into a **family of geometric settling metrics** for Evo 2 7B. The central question:

> **언제, 그리고 어떻게 모델이 수렴하는가?** Direction, magnitude, trajectory dynamics, distribution, and path efficiency are each separately measurable axes of "settling". By spreading these out and analyzing each one's biological mapping, we obtain a multi-axis picture of how genomic foundation models compute biological grammar.

## Status

Project setup. Plan is locked through iteration 6 (see [`PLAN.md`](PLAN.md)). Implementation not started.

## Read this first

- [`PLAN.md`](PLAN.md) — Consolidated experimental plan (5 metric family × 3 reference variants × 6 stages × 9 figures)
- [`docs/thesis.md`](docs/thesis.md) — Why this research is meaningful
- [`docs/metric_definitions.md`](docs/metric_definitions.md) — All metric math + reference variants
- [`docs/design_decisions.md`](docs/design_decisions.md) — Decision log across iterations 1–6
- [`docs/preregistration.md`](docs/preregistration.md) — (stub) for hypothesis pre-registration if added back later

## The 5-metric family at a glance

| ID | Name | What it measures | Reference |
|---|---|---|---|
| M1 | $c_{\text{dir}}$ | Direction settling (cosine) | dependent (3 variants) |
| M2 | $c_{\text{mag}}$ | Magnitude settling ($\|r-1\|$) | dependent (2 variants) |
| M3 | $c_{\text{geo}}$ | Trajectory dynamics (velocity + curvature) | **reference-free** |
| M4 | $c_M$ | Mahalanobis (distribution-aware) | dependent (3 variants) |
| M5 | $c_\tau$ | Path tortuosity (cumulative efficiency) | dependent (3 variants) |
| (M6) | $D_{L_2}$ | L2 residual — consistency check (M1+M2 function) | dependent |

Total: **14 settling cells**, all from a single forward pass.

## Quickstart (future, once implemented)

```bash
# Pull hidden-state cache from DigitalOcean snapshot
bash scripts/00_pull_cache.sh

# Compute all 14 cells in one pass
python scripts/10_compute_all_cells.py

# Sanity gates per cell
python scripts/20_run_gates.py

# Cross-metric concordance + biological mapping
python scripts/30_concordance.py
python scripts/40_context_stratify.py

# Visualizations (V1–V9)
python scripts/50_make_viz.py

# Downstream tasks
python scripts/60_downstream.py
```

## Provenance

- Extends: [`gDTR-PoC`](https://github.com/darejinn/gDTR-PoC) (Phase 0–5 + Tier 1/2 + workshop paper)
- Origin: YAICON 8th hackathon team "Think Deep in Genome"

## License

MIT (see [`LICENSE`](LICENSE)).
