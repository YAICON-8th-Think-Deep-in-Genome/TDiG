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

## The 5-metric family (design v2 — see [`docs/metric_definitions.md`](docs/metric_definitions.md))

| ID | Name | What it measures | Reference |
|---|---|---|---|
| M1 | $c_{\text{dir}}$ | Direction settling (cosine), persistence W=3 | dependent (3 variants A/B/C) |
| M2 | "Residual accumulation magnitude" | Pre-norm magnitude ratio $\|r-1\|$ (diagnostic) | dependent (Ref A only healthy) |
| M3 | $c_{\text{geo}}$ | Trajectory dynamics (velocity + curvature), 5 α/β cells | **reference-free** |
| **M4** | $c_{M,\text{set}}$ | **Reference-whitened settling distance** $\sqrt{(h_\ell-h_{\text{ref}})^\top \Sigma_{\text{ref}}^{-1} (h_\ell-h_{\text{ref}})}$ (Σ_ref shrinkage, monotone) | dependent (3 variants) |
| M5 | $c_\tau$ | Path tortuosity (M5 Option B locked) | dependent (3 variants) |
| (M6) | $D_{L_2}$ | Consistency check (M1+M2 function, NOT a metric) | unit test |

**Design v2 (locked 2026-05-24)**:
- **Settling concept split into 3 explicit definitions**: Def 1 (M3 trajectory stops), Def 2 (M1/M5/M4_set Ref A toward h_29), Def 3 (h_norm — no metric captures; honest limitation)
- **Persistence-based settling** (rolling window W=3) replaces single-dip-vulnerable running-min envelope
- **M4_set adoption**: full Σ_ref-whitening with Ledoit-Wolf shrinkage, monotone-decrease by construction (no envelope needed)
- **M5 Option B**: RMSNormed trajectory for Ref B (numerator+denominator consistent)
- **γ ablation matrix**: q50/q70/q90 percentiles

Total: **17 settling cells**, all from a single forward pass.

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
