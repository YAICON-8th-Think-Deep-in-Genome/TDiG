# TDiG — Project Plan (consolidated through iteration 6)

This document consolidates 6 iterations of planning into the canonical project plan. Locked decisions, metric family, reference variants, experimental sequence, visualization plan, and open questions are all here.

For decision history (what was tried and discarded across iterations 1–6), see [`docs/design_decisions.md`](docs/design_decisions.md).

---

## 1. Project framing

**Core question.** When and how does a genomic foundation model converge, and what does that pattern reveal about how the model computes biological grammar?

**Approach.** Spread out a *family of geometric settling metrics* over the residual-stream trajectory, analyze each one's biological mapping, and visualize the resulting multi-axis convergence picture.

**Mode.** Descriptive science. Falsification-based hypothesis testing (H0/H1/H2) was considered and dropped in iteration 5 — the value of this project is *systematic exposure* of the metric × biology mapping, not binary hypothesis verdicts.

**Scope.**
- Primary model: **Evo 2 7B** (CLM, 32 blocks)
- Canonical tap: $L^\star = 29$ (locked; Evo 2 pre-final saturation per `gDTR-PoC` Phase 1)
- MLM transferability (NT-v2, DNABERT-2): deferred to Phase 2. M3 c_geo's reference-free nature gives a partial path forward there.

---

## 2. Final metric family (5 main + 1 derived)

### 2.1 Definitions

| ID | Name | Definition | Reference | Axis |
|---|---|---|---|---|
| **M1** | $c_{\text{dir}}$ | $D_{\text{dir}}(\ell, t) = 1 - \cos(h_\ell, h_{\text{ref}}) \le \gamma_{\text{dir}}$ (running-min, q70 calibration) | dependent (3 variants) | direction (pointwise) |
| **M2** | $c_{\text{mag}}$ | $D_{\text{mag}}(\ell, t) = \lvert r - 1\rvert$ where $r = \lVert h_\ell\rVert / \lVert h_{\text{ref}}\rVert$, $\le \gamma_{\text{mag}}$ | dependent (2 variants; B degenerate) | magnitude (pointwise) |
| **M3** | $c_{\text{geo}}$ | $g_\ell = \alpha\tilde v_\ell + \beta\tilde\kappa_\ell$; $c_{\text{geo}} = \min\{\ell : g_k \le \tau \;\forall k \in [\ell, L-2]\}$ | **independent** | trajectory dynamics (pointwise) |
| **M4** | $c_M$ | $D_M(\ell, t) = \sqrt{(h_\ell - h_{\text{ref}})^T \Sigma_\ell^{-1} (h_\ell - h_{\text{ref}})} \le \gamma_M$ | dependent (3 variants) | distribution anisotropy (pointwise) |
| **M5** | $c_\tau$ | $\tau(\ell, t) = \frac{\sum_{k=\ell}^{28} \lVert h_{k+1} - h_k\rVert}{\lVert h_\ell - h_{\text{ref}}\rVert + \epsilon}$; first $\ell$ with $\tau \le \gamma_\tau$ | dependent (3 variants) | path efficiency (cumulative) |
| (M6) | $D_{L_2}$ | $\lVert h_\ell - h_{\text{ref}}\rVert_2 / \lVert h_{\text{ref}}\rVert_2$ — function of M1 and M2 | dependent | consistency check / single-scalar baseline |

### 2.2 M3 c_geo details (the principled trajectory metric)

- Velocity: $v_\ell(t) = \lVert h_{\ell+1} - h_\ell\rVert / \lVert h_\ell\rVert$ (ratio for scale invariance)
- Curvature: $\kappa_\ell(t) = 1 - \cos(h_{\ell+1} - h_\ell,\; h_{\ell+2} - h_{\ell+1})$
- Standardization: $\tilde v$, $\tilde\kappa$ z-scored per layer over chr22 sanity population
- Combined gauge: $g_\ell = \alpha \tilde v_\ell + \beta \tilde\kappa_\ell$ with default $(\alpha, \beta) = (1, 1)$
- Settling: first $\ell$ such that $g_k \le \tau$ for **all** $k \in [\ell, L-2]$ (strict — disallows transient dips)
- Control: CKA cross-validation against skip-connection bias (see [`docs/metric_definitions.md`](docs/metric_definitions.md) §M3)

### 2.3 M5 c_τ tortuosity details

- Numerator: remaining cumulative path from $\ell$ to layer 29 (reference-invariant)
- Denominator: straight-line distance from $h_\ell$ to $h_{\text{ref}}$ (reference-dependent — hence 3 variants)
- $\tau \ge 1$ always; $\tau = 1$ iff path is collinear
- Numerical: $\epsilon$ smoothing required as $\ell \to 29$ (denominator $\to 0$)
- Diagnostic obligation: monotonicity check on chr22 sanity (target $\ge 95\%$ monotone decreasing); if fails, strengthen $\epsilon$ or switch reference variant

### 2.4 Complementarity matrix

|  | direction | magnitude | distribution | local trajectory | cumulative trajectory | reference-free |
|---|---|---|---|---|---|---|
| M1 $c_{\text{dir}}$ | ✓ | | | | | |
| M2 $c_{\text{mag}}$ | | ✓ | | | | |
| M3 $c_{\text{geo}}$ | partial ($\kappa$) | partial ($v$) | | ✓ | | ✓ |
| M4 $c_M$ | partial | partial | ✓ | | | |
| M5 $c_\tau$ | | | | | ✓ | |

5 metrics cover 5 of 6 axes. The missing cell ("reference-free cumulative") is a future-work candidate.

---

## 3. Reference variant matrix

Three variants of the reference frame, applied uniformly to all reference-dependent metrics. This isolates the effect of RMSNorm $\gamma$ asymmetry.

### 3.1 Variants

| Variant | $h_\ell$ treatment | reference treatment | $\gamma$ symmetry | Meaning |
|---|---|---|---|---|
| **A "no-norm"** | raw | $h_{29}$ raw | none (symmetric) | pure hidden-state comparison, no $\gamma$ |
| **B "both-norm"** | $\mathrm{RMSNorm}(h_\ell)$ | $\mathrm{RMSNorm}(h_{29})$ | both (symmetric) | DTR-style |
| **C "current gDTR"** | raw | $h_{\text{norm}}$ | reference only (asymmetric) | existing baseline |

### 3.2 Cell compatibility

|  | A | B | C |
|---|---|---|---|
| M1 $c_{\text{dir}}$ | ✓ | ✓ | ✓ |
| M2 $c_{\text{mag}}$ | ✓ | ⚠ degenerate | ✓ |
| M3 $c_{\text{geo}}$ | (reference-free — no variants) | | |
| M4 $c_M$ | ✓ | ✓ | ✓ |
| M5 $c_\tau$ | ✓ | ✓ | ✓ |
| M6 $D_{L_2}$ | ✓ | (degenerate possible) | ✓ |

**Total cell count: 14 main cells** (M1×3 + M2×2 + M3×1 + M4×3 + M5×3 + M6×2). All computed from a single forward pass.

### 3.3 Diagnostic value of the variant matrix
- **A ↔ C**: effect of removing $\gamma$ asymmetry
- **B ↔ C**: effect of moving to DTR-style $\gamma$-symmetric
- **A ↔ B**: pure $\gamma$ effect (within symmetric pair)
- **All vs M3**: reference-induced effect vs trajectory-intrinsic measurement

---

## 4. Experimental sequence (6 stages)

### S1. Compute (single forward pass)
- Input: chr22 12,978 windows × 6 kb hidden-state cache (server)
- Output: `results/settling_table.parquet`, schema `(token_id, position, context, metric_id, ref_id, c_value)`
- Approximate size: 14 cells × 77 M positions = ~850 M rows

### S2. Per-cell sanity (3 gates × 14 cells = 42 runs)

| Gate | Spec | Pass criterion |
|---|---|---|
| **Splice signal** | chr22 splice donor vs intron Cohen's $d$ | $\lvert d\rvert \ge 0.20$ |
| **Entropy** (E8 carry-over) | $\rho(c, H_{\text{per-pos}})$ on 720 K positions | $\lvert\rho\rvert \le 0.20$ AND residualized $d$ not weaker than raw |
| **Motif** (E9 carry-over) | 1,000 GT-AG donors, motif edit and flank shuffle, both directions | metric responds to both perturbations |

A cell failing a gate is **not** dropped automatically — failure mode itself is information about what that metric × reference combination captures.

### S3. Cross-metric concordance

| Sub-analysis | What |
|---|---|
| Pairwise Spearman $\rho$ matrix | 14×14 settling-depth correlation |
| Dissociation token identification | Tokens where metric A says "settled" but metric B says "not yet". Which contexts are these enriched in? |
| 2D signature analysis | Joint scatter pairs: $(c_{\text{dir}}, c_{\text{mag}})$, $(c_{\text{dir}}, c_{\text{geo}})$, $(c_{\text{geo}}, c_\tau)$, … |
| PCA on settling vector | Each token → 14-d settling vector → 2D PCA → token clusters |

Central question: how redundant or orthogonal are the 14 cells?

### S4. Context stratification (biological mapping)

For each cell: 7 context classes (intergenic, intron, coding_exon, 5'UTR, 3'UTR, splice_donor, splice_acceptor) × (distribution, mean, std, Cohen's $d$ vs intron baseline).

→ **14 × 7 = 98-cell heatmap** as the densest single view of the project.

### S5. Visualization (V1–V9)

| Figure | Role | Headline? |
|---|---|---|
| V1 trajectory 2D PCA | Visual intuition for trajectory shape | ⭐ |
| V2 velocity heatmap | Per-layer movement speed by context | diagnostic |
| V3 curvature heatmap | Per-layer direction change by context | diagnostic |
| V4 cumulative path | Plateau ≈ $c_{\text{geo}}$ | ⭐ |
| V5 2D signature scatter | e.g. $(c_{\text{dir}}, c_{\text{mag}})$ or $(c_{\text{dir}}, c_{\text{geo}})$ | ⭐ |
| V6 CKA layer×layer matrix | Skip-bias control | diagnostic |
| V7 98-cell context heatmap | Densest summary of S4 | ⭐ |
| V8 dissociation map | Chromosome position × metric disagreement | optional |
| V9 tortuosity profile | Mean $\tau(\ell)$ by context | diagnostic |

V1 / V4 / V5 / V7 are the main headline candidates.

### S6. Downstream tasks

| Task | Input | Eval |
|---|---|---|
| **T-A** splice site prediction | chr22 + chr17, GENCODE v44 splice positions | per-position recall@k, AUC-PR |
| **T-B** ClinVar variant classification | 10,910 variants (8,008 P/B + 2,902 VUS) | 10-fold stratified AUROC, DeLong |

Feature space:
- per-cell scalar settling depth (14 features)
- per-cell per-layer $D$ vector (14 × 32 = 448 features) — high-dim, requires l1 / group-l1
- pairwise joints (M1+M2, M3+M5, ...)
- Full family joint vs Paper 2 baseline $\lVert\Delta h\rVert_2$ AUROC 0.926

---

## 5. Biological mapping strategy

### 5.1 Context-level mapping (from S4)
"What is each biological context's settling fingerprint across the 14 cells?"

Hypothetical pattern (to be confirmed by data):
- Splice donor: low $c_{\text{dir}}$, low $c_{\text{geo}}$, average $c_{\text{mag}}$ → "direction and trajectory stabilize early, magnitude average" — signature of long-range integration
- Intron: averages across all → simple context
- 5'UTR: high $c$, entropy-coupled → unstable

### 5.2 Variant-level mapping (from S6 T-B)
"Do pathogenic vs benign variants create distinct settling fingerprints?"
- Per-variant 14-cell settling vector
- P/LP cluster vs B/LB cluster
- Which metric/ref is the strongest single P/B discriminator?
- $\Delta$(ref → alt) of the settling vector — variant impact map

### 5.3 Headline narrative candidate
> Representation in a genomic foundation model does **not** settle at a single layer. Direction, magnitude, trajectory dynamics, distribution, and cumulative path efficiency each stabilize at different layers, and this multi-axis settling pattern varies systematically with biological context. The pattern reveals which axes of representation the model commits to early versus late when computing each kind of biological grammar.

---

## 6. Assets reused from `gDTR-PoC`

See [`docs/design_decisions.md`](docs/design_decisions.md) §Assets for the full map. Key items:

- `src/ur_gdtr.py`, `src/tuned_lens.py` — M1 baseline implementation
- `phase1/scripts/` — Evo 2 forward-pass infrastructure
- `scripts/40_t11_per_layer_ablation.py` — per-layer AUROC pipeline (reused across all cells)
- `scripts/41_t14_bootstrap.py` — 1000× bootstrap CI
- `scripts/exp1_entropy_correlation.py` (E8) — entropy gate required for all cells
- `scripts/exp2_shuffled_motif_control.py` (E9) — motif gate required for all cells
- `results/phase1.6/chr22_cache.h5` (server snapshot) — input for all cells
- `results/phase3_main/variants_features.csv` (regenerable) — T-B downstream

---

## 7. Open questions (lock before S1 begins)

| # | Question | Decision needed by |
|---|---|---|
| 1 | Magnitude definition — $\lvert r - 1\rvert$ vs $\lvert\log r\rvert$ (Evo 2 huge scales) | S1 |
| 2 | M2 Ref B handling — degenerate report only? define $\gamma$-only variant? | S1 |
| 3 | M3 $c_{\text{geo}}$ $(\alpha, \beta)$ — start $(1, 1)$, tune after calibration | S1 |
| 4 | M3 "all $k$" range — $[\ell, L-2]$ vs $[\ell, \ell+5]$ rolling | S1 |
| 5 | M4 $\Sigma$ estimation — Ledoit-Wolf vs diagonal vs PCA-top-k | S1 (recommend: diagonal first) |
| 6 | CKA control threshold for M3 | S1 |
| 7 | V1 PCA mode — raw / per-layer-centered / tuned-lens | S5 (recommend: per-layer-centered + raw) |
| 8 | V5 headline pair — $(c_{\text{dir}}, c_{\text{mag}})$ vs $(c_{\text{dir}}, c_{\text{geo}})$ | S5 |
| 9 | M6 $D_{L_2}$ — main paper vs appendix consistency check | paper-writing |
| 10 | M5 $\tau$ $\epsilon$ — distribution-based (1st percentile) vs constant (1e-6) | S1 |
| 11 | M5 $\tau$ monotonicity fail handling — running-min? or report as that metric's result? | S1 |
| 12 | M5 $\tau$ vs M3 $\kappa$ high-correlation tokens — drop one in feature engineering? regularize? | S6 |

---

## 8. Next actions

1. **Confirm open questions 1, 2, 4, 5, 10–12** (S1 gating decisions)
2. **DigitalOcean snapshot revival** + cache path mapping
3. **Implement `src/tdig/references/`** first (every metric depends on it)
4. **Single-sequence dry run** — chr22 1 sequence × 14 cells → distribution inspection → q70 calibration

After (1)–(4) land, the project enters S1 proper.
