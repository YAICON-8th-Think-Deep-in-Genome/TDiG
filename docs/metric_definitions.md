# Metric definitions

Canonical math definitions for all 5 main metrics (M1–M5) and the M6 consistency-check metric. Reference variants (A / B / C) are defined in [`reference_variants.md`](reference_variants.md).

Notation:
- $h_\ell(t) \in \mathbb{R}^d$ — residual-stream hidden state at layer $\ell$, token $t$ (Evo 2 7B: $d = 4096$, $\ell \in \{0, 1, \ldots, 31\}$, $L^\star = 29$)
- $h_{\text{ref}}(t)$ — reference vector (variant-dependent; see `reference_variants.md`)
- $c$, $\gamma$ — settling depth and threshold
- $r = \lVert h_\ell\rVert / \lVert h_{\text{ref}}\rVert$ — magnitude ratio

---

## M1 — $c_{\text{dir}}$ direction settling

Cosine distance between $h_\ell$ and reference:

$$D_{\text{dir}}(\ell, t) = 1 - \cos\bigl(h_\ell(t), h_{\text{ref}}(t)\bigr)$$

Running-min envelope:

$$\widetilde D_{\text{dir}}(\ell, t) = \min_{k \le \ell} D_{\text{dir}}(k, t)$$

Settling depth:

$$c_{\text{dir}}(t) = \min\bigl\{\ell : \widetilde D_{\text{dir}}(\ell, t) \le \gamma_{\text{dir}}\bigr\}$$

**Calibration.** $\gamma_{\text{dir}}$ is the 70th percentile (q70) of $\widetilde D_{\text{dir}}(L^\star - 1, t)$ over the chr22 sanity population.

**Captures.** Pure direction settling. Scale-invariant (cosine ignores magnitude).

**Reference variants.** A, B, C — all valid.

**Known limitations.** Magnitude-blind; single-dip artifact (running-min lets a fluke layer count as settled); cross-layer basis mismatch (cosine 1 at layer 5 and at layer 25 mean different things if the layers have different functional bases).

---

## M2 — $c_{\text{mag}}$ magnitude settling

Magnitude ratio deviation from 1:

$$D_{\text{mag}}(\ell, t) = \lvert r(\ell, t) - 1\rvert, \quad r = \frac{\lVert h_\ell(t)\rVert_2}{\lVert h_{\text{ref}}(t)\rVert_2}$$

Running-min envelope:

$$\widetilde D_{\text{mag}}(\ell, t) = \min_{k \le \ell} D_{\text{mag}}(k, t)$$

Settling:

$$c_{\text{mag}}(t) = \min\bigl\{\ell : \widetilde D_{\text{mag}}(\ell, t) \le \gamma_{\text{mag}}\bigr\}$$

**Calibration.** $\gamma_{\text{mag}}$ via q70 on chr22 sanity, same protocol as M1.

**Captures.** Pure magnitude settling. Direction-blind.

**Reference variants.**
- A ✓ — raw magnitudes, no $\gamma$ asymmetry
- B ⚠ degenerate — RMSNorm flattens all magnitudes to a common value
- C ✓ — current gDTR baseline

**Open question.** $\lvert r - 1\rvert$ vs $\lvert\log r\rvert$. The latter is symmetric in log space and handles Evo 2's huge hidden-state norms ($h_{30}.\mathrm{std} \sim 2 \times 10^{10}$) more gracefully. Resolved during S1 distribution inspection.

**Antiparallel edge case.** $h_\ell = -h_{\text{ref}}$ has $r = 1$, so $D_{\text{mag}} = 0$ — "settled" by magnitude despite pointing backward. In Evo 2 residual streams this is rare (residual updates accumulate forward), but chr22 sanity should report its frequency.

---

## M3 — $c_{\text{geo}}$ trajectory dynamics (reference-free)

Per-layer velocity (scale-invariant):

$$v_\ell(t) = \frac{\lVert h_{\ell+1}(t) - h_\ell(t)\rVert_2}{\lVert h_\ell(t)\rVert_2}$$

Per-layer curvature (direction change of consecutive updates):

$$\kappa_\ell(t) = 1 - \cos\bigl(h_{\ell+1} - h_\ell,\; h_{\ell+2} - h_{\ell+1}\bigr)$$

Standardize per-population:

$$\tilde v_\ell(t) = \frac{v_\ell(t) - \mu_v(\ell)}{\sigma_v(\ell)}, \qquad \tilde\kappa_\ell(t) = \frac{\kappa_\ell(t) - \mu_\kappa(\ell)}{\sigma_\kappa(\ell)}$$

Combined gauge:

$$g_\ell(t) = \alpha \tilde v_\ell(t) + \beta \tilde\kappa_\ell(t)$$

Settling — strict "all subsequent $k$" condition:

$$c_{\text{geo}}(t) = \min\Bigl\{\ell : g_k(t) \le \tau \;\text{ for all } k \in [\ell, L - 2]\Bigr\}$$

**Default parameters.** $(\alpha, \beta) = (1, 1)$ to start; tune after calibration. $\tau$ via q70 on chr22 sanity penultimate-layer $g$.

**Open question.** Range of "all $k$" — strict $[\ell, L-2]$ versus a relaxed rolling $[\ell, \ell+5]$. Strict version may set $c_{\text{geo}}$ very late for tokens that fluctuate; rolling is more tolerant.

**Captures.** Local trajectory dynamics (velocity + curvature). Reference-free.

**Provenance.** Velocity-curvature decomposition has direct anchors in Neural ODE (Chen et al. 2018), Geshkovski et al. 2023, *Transformer Dynamics* (arXiv:2502.12131), and the curvature-naming convention of arXiv:2510.06640.

**CKA cross-validation.** Velocity and curvature are cosine-based, so residual skip connections may upward-bias adjacent-layer cosine similarity. To control this, compute CKA(h_ℓ, h_{ℓ+k}) for $k = 1, \ldots, 5$ across chr22 sanity tokens. A layer where $c_{\text{geo}}$ declares settling must also show high CKA to subsequent layers; mismatches flag skip-bias contamination.

---

## M4 — $c_M$ Mahalanobis residual

Distribution-aware distance:

$$D_M(\ell, t) = \sqrt{(h_\ell - h_{\text{ref}})^T \Sigma_\ell^{-1} (h_\ell - h_{\text{ref}})}$$

where $\Sigma_\ell$ is the per-layer empirical covariance estimated over the chr22 sanity population at layer $\ell$.

Settling pipeline: same as M1 (running-min + q70-calibrated $\gamma_M$).

**$\Sigma$ estimation options.**
1. **Diagonal $\Sigma_\ell$** — fast, numerically stable, ignores feature correlations. Recommended starting point.
2. **Ledoit-Wolf shrinkage** — full $\Sigma$ with shrinkage toward diagonal. Better accuracy, moderate cost.
3. **PCA-top-$k$ ($k = 64, 128, 256$)** — restrict to top-$k$ eigen-directions; interpretable, manageable cost.

**Diagnostic obligation.** Report condition number $\kappa(\Sigma_\ell)$ per layer. If $\kappa > 10^6$, switch from full $\Sigma$ to diagonal or apply stronger shrinkage.

**Captures.** Distribution anisotropy. High covariance directions are penalized less (treated as noise); low covariance directions are penalized more (treated as signal).

**Reference variants.** A, B, C — all valid. $\Sigma_\ell$ is estimated on each variant's hidden-state representation.

---

## M5 — $c_\tau$ path tortuosity

Remaining-path tortuosity from layer $\ell$:

$$\tau(\ell, t) = \frac{\sum_{k=\ell}^{L^\star - 1} \lVert h_{k+1}(t) - h_k(t)\rVert_2}{\lVert h_\ell(t) - h_{\text{ref}}(t)\rVert_2 + \epsilon}$$

Settling:

$$c_\tau(t) = \min\bigl\{\ell : \tau(\ell, t) \le \gamma_\tau\bigr\}$$

**Properties.**
- $\tau \ge 1$ always (triangle inequality)
- $\tau = 1$ iff the path from $h_\ell$ to $h_{\text{ref}}$ is collinear (perfectly direct)
- Denominator $\to 0$ as $\ell \to L^\star$ — numerical instability requires $\epsilon$ smoothing

**$\epsilon$ choice.** Distribution-based: 1st percentile of the denominator over chr22 sanity. Alternative: constant $10^{-6}$. Decided in S1.

**Calibration.** $\gamma_\tau$ via q70 on chr22 sanity at $\ell = 27$ (penultimate before $L^\star = 29$).

**Reference variants.** A, B, C — only the denominator changes; the numerator (cumulative path) is reference-invariant.

**Monotonicity diagnostic.** $\tau$ is *not* guaranteed monotone — denominator can decrease faster than numerator. On chr22 sanity, report fraction of tokens for which $\tau(\ell)$ is monotone non-increasing. Target $\ge 95\%$. Fail handling options: strengthen $\epsilon$, switch reference variant, or apply running-min as a fallback.

**Captures.** Cumulative path efficiency from $\ell$ to the reference. Complementary to M3:
- M3 velocity / curvature: pointwise (local) trajectory dynamics
- M5 tortuosity: cumulative (global) path efficiency

A trajectory can have low pointwise curvature but high tortuosity (slow consistent drift) or high curvature but low tortuosity (zigzag that net-cancels).

---

## M6 — $D_{L_2}$ consistency check

$$D_{L_2}(\ell, t) = \frac{\lVert h_\ell(t) - h_{\text{ref}}(t)\rVert_2}{\lVert h_{\text{ref}}(t)\rVert_2}$$

Algebraic decomposition (with $r$, $c = \cos(h_\ell, h_{\text{ref}})$):

$$D_{L_2}^2 = r^2 + 1 - 2rc = (r - c)^2 + (1 - c^2)$$

- $(r - c)^2$ — magnitude-mismatch term (captured by M2)
- $(1 - c^2)$ — angular term (captured by M1)

$D_{L_2} \to 0$ requires both $r \to 1$ AND $c \to 1$.

**Role.** Cross-check that M1 and M2 jointly reproduce $D_{L_2}$ patterns. If the family decomposition is correct, joint $(c_{\text{dir}}, c_{\text{mag}})$ analysis should explain $D_{L_2}$ behavior.

**Antiparallel handling.** $D_{L_2}$ is non-degenerate where $\lvert r - 1\rvert$ would be — useful audit when M2's antiparallel edge case occurs.

**Status.** Appendix-level metric. Not used as a primary headline feature.

---

## Calibration protocol (uniform across M1, M2, M4, M5)

1. Run chr22 sanity sequences through Evo 2 7B (100 sequences × 6 kb = 600 K positions, per Phase 1.4 protocol)
2. For each metric × reference variant cell:
   - Compute the per-position $D$ at layer $L^\star - 1$
   - $\gamma = \mathrm{q70}\bigl(\{D(L^\star - 1, t)\}_t\bigr)$
3. Lock $\gamma$ before analyzing any biological-context positions

This is the same regional-q70 protocol that locks `gDTR-PoC` Phase 1's $\gamma_{\text{cos}} = 0.397$.

---

## Computation cost summary

Per chr22 window (6 kb, 6000 positions):
- M1, M2: $O(L \cdot d)$ — cheap
- M3: $O(L \cdot d)$ — adds CKA $O(L^2 \cdot n_{\text{pairs}})$ for control
- M4: $O(L \cdot d^2)$ for full $\Sigma$ inversion; reducible by diagonal or PCA-top-$k$
- M5: $O(L \cdot d)$ — cheap once hidden states are in memory
- M6: $O(L \cdot d)$ — derived from M1+M2

All 14 cells fit in a single forward pass over chr22; post-processing (Cohen's $d$, q70, CKA, $\Sigma$ inversion, running-min) is CPU-bound and fast.
