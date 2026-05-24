# Design decisions log

Decisions across 6 planning iterations (2026-05-24). Each entry records what was decided, what was reversed, and why.

---

## Iteration 1 — initial CLM/MLM dual-track plan (superseded)

- Proposed metric family: M1 direction, M2 magnitude, M3 JSD, M4 tortuosity, M5 step-wise, M6 trajectory vector
- Workstreams for 4 team members
- Target: 5/27 YAICON final presentation

**Reversed in iter 2+**: JSD, M5 step-wise, MLM transferability, hard timeline.

---

## Iteration 2 — narrow to Evo 2 CLM, lock L\* = 29

- **Lock**: $L^\star = 29$ as canonical interpretively-distinct tap (carried from gDTR-PoC Phase 1's L31-idle finding)
- **Drop**: JSD — genomic vocab $|V| = 4$ makes distribution comparison weak; cosine/L2/Mahalanobis suffice
- **Drop**: M5 step-wise as primary metric — only relevant for MLM, which is deferred
- **Defer**: MLM (NT-v2, DNABERT-2) transferability to Phase 2
- **Reasoning**: Phase 1 should establish a coherent CLM-focused framework before generalizing across architectures

---

## Iteration 3 — separate M2 into direction and magnitude; 3 reference variants

- **Decision**: M2 unbundles into a clean **magnitude-only** metric. Direction stays as M1 (cosine); magnitude becomes $\lvert r - 1\rvert$ where $r = \lVert h_\ell\rVert / \lVert h_{\text{ref}}\rVert$.
- **Reasoning**: The previous unified L2 residual proposal mixed direction and magnitude — useful as a consistency check but obscures the 2D signature analysis.
- **Decision**: 3 reference variants (A no-norm / B both-norm / C current gDTR) applied uniformly across all reference-dependent metrics
- **Reasoning**: Isolates RMSNorm $\gamma$ asymmetry effect — A vs C measures $\gamma$ removal; B vs C measures DTR-style symmetrization; A vs B measures pure $\gamma$.
- **Caveat**: M2 × Ref B is mathematically degenerate (RMSNorm flattens magnitudes); reported diagnostically but not used as a settling cell

---

## Iteration 4 — adopt c_geo (velocity + curvature), drop tortuosity (later reversed)

- **Decision**: New M3 = $c_{\text{geo}}$, defined as a reference-free combination of velocity $v_\ell$ and curvature $\kappa_\ell$. Settling = "all subsequent $k$ stay small" (strict, no running-min).
- **Reasoning**: Reference-free + naturally robust to single-dip artifact + theoretically grounded in Neural ODE / Transformer Dynamics literature + Evo 2 L30 rotation auto-absorbed as velocity spike
- **Decision (this iteration)**: tortuosity $\tau$ subsumed into c_geo's curvature; removed from family
- **Reversed in iter 6**: tortuosity and c_geo measure different things — pointwise dynamics vs cumulative path efficiency
- **Also considered (then dropped in iter 5)**: c_fn functional/causal settling as M5, with H0/H1/H2 falsification framework

---

## Iteration 5 — drop c_fn; drop falsification framework; switch to descriptive science

- **Drop**: c_fn (functional / causal settling) — computationally expensive (per-token layer interventions) and shifts the project from geometric to causal-mechanistic, which is a different kind of paper
- **Drop**: H0 / H1 / H2 falsification framework that was built around c_geo vs c_fn comparison
- **Decision**: Project mode is now **descriptive science** — "spread out all metrics and analyze + visualize convergence patterns + connect to biology"
- **Reasoning**: User instruction prioritizes meaningful research over the narrower falsification frame. Systematic mapping is the value; binary verdicts are not required.
- **Implication**: Visualization (V1–V9) and context-stratification (S4 98-cell heatmap) become the headline deliverables rather than hypothesis-test verdicts

---

## Iteration 6 — add tortuosity back as M5

- **Reverse iter 4**: $\tau$ tortuosity restored as a distinct metric (M5)
- **Reasoning**: c_geo (pointwise velocity + curvature) and $\tau$ (cumulative path efficiency) measure different quantities:
  - A trajectory can have low curvature but high tortuosity (slow consistent drift away from endpoint)
  - Or high curvature but low tortuosity (zigzag that net-cancels)
- **Family now**: M1 direction, M2 magnitude, M3 c_geo (reference-free), M4 Mahalanobis, M5 tortuosity, M6 L2 (consistency)
- **Cell count**: 14 main cells (M1×3 + M2×2 + M3×1 + M4×3 + M5×3 + M6×2)

---

## Assets reused from `gDTR-PoC`

| Asset | Role in TDiG |
|---|---|
| `src/ur_gdtr.py`, `src/tuned_lens.py` | M1 baseline implementation |
| `phase1/scripts/` Evo 2 forward infrastructure | Hidden-state caching pipeline |
| `scripts/40_t11_per_layer_ablation.py` | Per-layer AUROC pipeline, reused for all 14 cells |
| `scripts/41_t14_bootstrap.py` | 1000× bootstrap CI |
| `scripts/45_t12_delta_h.py` | $\lVert h_\ell - h_{\text{ref}}\rVert$ vector arithmetic |
| `scripts/exp1_entropy_correlation.py` (E8) | Entropy gate — required sanity for every cell |
| `scripts/exp2_shuffled_motif_control.py` (E9) | Motif gate — required sanity for every cell |
| `results/phase1.6/chr22_cache.h5` (server snapshot) | Hidden-state input for all cells |
| `results/phase2.1/chr17_cache.h5` (server snapshot) | chr17 replication input |
| `results/phase3_main/variants_features.csv` (regenerable) | T-B ClinVar variant features |
| `results/phase4/per_model_summary.json` + 3 caches | Future cross-architecture validation (Phase 2) |

## What is NOT carried over

- Phase 0 HyenaDNA-medium codepath — superseded by HyenaDNA-large in Phase 4
- LaTeX / figure-build infrastructure — TDiG paper is separate
- v1 / v3 / v4 paper iterations and DOCX history
- Decision documents (`docs/findings/`, `docs/decisions/` from gDTR-PoC) — TDiG writes its own
- JSD-related code — dropped in iter 2

---

## Open questions that remain open

See [`../PLAN.md`](../PLAN.md) §7 for the live list (12 open questions, mostly S1-gating decisions).
