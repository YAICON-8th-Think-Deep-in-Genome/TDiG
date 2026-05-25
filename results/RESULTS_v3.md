# TDiG RESULTS_v3 — Comprehensive analysis tracker (2026-05-25)

This document supersedes `RESULTS_v2.md` for the active analysis phase.
It tracks every analysis done since 2026-05-24 with **input data**, **script**,
**output location**, and **headline finding**, so any result is reproducible.

## TL;DR — what the paper claims now have evidence for

1. **Variant pathogenicity AUROC 0.855 at L=8** (ΔH norm L2, full cohort P_LP vs B_LB, n=8,008 across 15 cancer genes). Per-gene 0.81–0.92 range. *Source: §A1.*
2. **Synonymous variants peak at L=27**, *intron/3UTR at L=8* — variant effect layer depends on disrupted information level (sequence vs protein-semantic). Confirms gDTR Paper 1 §3.3. *Source: §A2.*
3. **L29 phase transition** — context probing AUROC crashes 0.980→0.799 AND variant AUROC drops 0.85→0.79 AND PC1-metric correlations collapse, all at the same layer. Architectural singularity. *Source: §B1 + §A1 + §C.*
4. **PC1 (75.7% var) = "transcribed-region settling readiness axis"** — partially biological (Cohen d 0.18–0.45 vs intron per context), position confounder rejected (max \|r\|=0.34). PC1 \|r\|=0.85 with M1_dir_refC at L=4. *Source: §C.*
5. **γ q70 calibration is robust** — 12/15 cells preserve sign across γ q50/q70/q90. Headline d-values stable. *Source: §B2.*

## Repository layout

```
/Users/yoonjincho/Project/TDiG/
├── scripts/                          # all analysis scripts (numbered)
├── results/
│   ├── RESULTS_v2.md                 # original chr22 v2 summary
│   ├── RESULTS_v3.md                 # THIS file
│   ├── analysis_BD/                  # §B1 + §C
│   ├── analysis_T123/                # §C extended
│   ├── variant_analysis_scalars/     # §A1
│   ├── variant_per_consequence/      # §A2
│   ├── gamma_ablation/               # §B2 (v1, buggy)
│   ├── chr17_replication/            # §D (running)
│   ├── bootstrap_chr22_ci/           # §E (running)
│   ├── variant_settling_cells/       # §A3 (running)
│   └── random_alt_control/           # §A4 (running, GPU)
└── data/cache/  (server only, 100+ GB)
```

Local results are mirrored from `digitalocean-gpu:/root/TDiG/data/cache/_v2_analysis/`.

---

## §A Variant analyses (paper §4 backbone)

### §A1 Variant pathogenicity AUROC per layer — DONE
- **Input data**: `/root/TDiG/data/cache/variants/variant_scalars.parquet` (10,910 variants, 14 cols including per-layer `delta_h_norm_2/1` and `delta_cos`)
- **Script**: `scripts/19_variant_analysis_scalars.py`
- **Output**: `results/variant_analysis_scalars/`
  - `per_layer_auroc.csv` + `per_layer_auroc.png` — 32-layer AUROC curve for 3 features
  - `per_gene_auroc.csv` + `per_gene_auroc.png` — 14 genes (EGFR skipped: 0 P_LP)
  - `stars_stratified.csv`
  - `summary.json`
- **Findings**:
  - Best overall: ΔH_norm_L1 AUROC **0.856 at L=8** (close: ΔH_norm_L2 0.855 at L=8, Δcos 0.841 at L=28)
  - L=0 baseline 0.64, L=8 peak 0.855, L=27 0.807, **L=29 crash to 0.792**, L=31 recovery 0.82
  - Per-gene best: VHL 0.916, PIK3CA 0.909, PTEN 0.906, BRCA2 0.883, ATM 0.875, KRAS 0.874, BRAF 0.868, PALB2 0.868, MSH2 0.856, TP53 0.851, BRCA1 0.830, APC 0.827, RB1 0.820, MLH1 0.811
  - Per-gene peak layer splits into **early-peak (L=7-8)** and **deep-peak (L=26-29)** groups

### §A2 Per-consequence stratification — DONE
- **Input data**: variant_scalars.parquet + `/root/gDTR/data/variants/clinvar.vcf.gz` (joined on chrom/pos/ref/alt to extract MC field)
- **Script**: `scripts/21_variant_per_consequence.py`
- **Output**: `results/variant_per_consequence/`
  - `variant_with_consequence.csv` — 10,910 variants joined with SO consequence
  - `per_consequence_auroc.csv` + `.png` — 9 consequence classes (≥5 P + 5 B)
  - `per_consequence_delta_distribution.csv` + `.png` — mean ΔH per consequence per layer
  - `per_consequence_kw.csv` — Kruskal-Wallis at each layer
  - `summary.json`
- **Findings (per-consequence best L, AUROC)**:
  - 3utr: L=8, 0.927 (n=137)
  - noncoding: L=27, 0.906 (n=341)
  - 5utr: L=27, 0.888 (n=651)
  - synonymous: L=27, 0.841 (n=1796) ← **gDTR Paper 1 §3.3 reconfirmed at scale**
  - intron: L=8, 0.830 (n=1930)
  - missense: L=27, 0.809 (n=1236)
- **Big picture**: variant peak layer tracks the biological information level the variant disrupts. Sequence-level (intron, 3utr) peaks early at L=8; protein/regulatory-semantic (missense, synonymous, 5utr) peaks deep at L=27.

### §A3 Full 17-cell variant ΔC analysis — RUNNING
- **Input**: `variant_h_ell_ref.h5` + `_alt.h5` (10,910 × 32 × 4096 each, 5.4 GB × 2) + `gamma_calibration_v2.json` + `sigma_ref_inv_A.npy`
- **Script**: `scripts/24_variant_settling_cells.py`
- **Output (pending)**: `results/variant_settling_cells/`
  - `variant_settling_per_cell.csv` — per variant × cell: c_ref, c_alt, Δc
  - `cell_auroc.csv` + `.png` — |Δc| AUROC per cell P_LP vs B_LB
  - `per_consequence_cell.csv` — cell × consequence AUROC
- **What it answers**: which of our 17 settling cells best predicts pathogenicity from variant-induced settling shift?

### §A4 GPU random-alt biological validation — RUNNING
- **Input**: variant_scalars.parquet (sample 300 P_LP + 300 B_LB) + hg38 fasta + Evo 2 7B
- **Script**: `scripts/25_random_alt_control.py`
- **Output (pending)**: `results/random_alt_control/`
  - `random_alt_delta_h.parquet` — ΔH norm per (variant, k, layer) for real + 3 random alt controls
  - `comparison_summary.csv` + `.png` — real vs random ΔH per layer per category
- **What it answers**: Does ΔH at L=8 distinguish *specific ClinVar variants* from *any random mutation at the same position*? If real >> random → biology beyond position-sensitivity.

---

## §B chr22 v2 methodological backbone

### §B1 Per-layer probing AUROC (B from earlier session) — DONE
- **Input**: tier3_raw_v2.h5 + chr22_position_labels.npy
- **Script**: `scripts/14e_probing_and_metric_pca.py` (--skip-D for B only)
- **Output**: `results/analysis_BD/`
  - `per_layer_auroc.csv` + `.png` — splice_donor-vs-intron + 5 other context-vs-intron curves
- **Findings**: splice_donor AUROC L=0 0.78 → L=27 **0.980 PEAK** → L=29 **0.799 CRASH** → L=31 0.82. M3 curvature trough at L=27 matches.

### §B2 γ q50/q70/q90 ablation — DONE (v2 fixed)
- **Input**: tier2_scalars_subset_v2.h5 + gamma_calibration_v2.json
- **Script**: `scripts/20_gamma_ablation.py` (v2 with `end_k=min(ell+W-1, max_layer)` boundary clip)
- **Output**: `results/gamma_ablation/`
  - `cell_d_under_gamma.csv` + `.png` — 17 cells × 3 γ × splice-vs-intron Cohen d
  - `range_under_gamma.csv` — settling dynamic range per (cell, γ)
- **Findings**: 12/15 cells robust. M3/M4 family all preserve sign+magnitude. Only M1_dir_refC, M5_tau_refC flip near zero (\|d\|<0.1, statistically meaningless). M1_dir_refA d strengthens from +0.41 (q50) → +0.54 (q70) → **+0.61 (q90)** — possible γ recommendation upgrade.

---

## §C PCA interpretability framework (D + T1+T2+T3) — DONE

### §C1 D — metric ↔ PCA correlation
- **Script**: `scripts/14e_probing_and_metric_pca.py`
- **Output**: `results/analysis_BD/metric_pca_corr.{csv,png,pdf}`, `pca_explained_variance.json`
- **Findings**: PC1 explains **75.7%** of post-layer-centering variance. PC1 \|r\|=0.85 with M1_dir_refC at L=4. PC1+ encodes Def 1 (M3_geo), PC1− encodes Def 2 (M1_dir, M2, M5_tau_refB). Bidirectional settling has geometric origin.

### §C2 T1 — PC-alone probing
- **Script**: `scripts/14f_pc_biological_meaning.py`
- **Output**: `results/analysis_T123/T1_pc_alone_auroc.{csv,png,pdf}`
- **Findings**: PC1 alone AUROC max **0.706 at L=30** (vs full 4096-D 0.980 at L=27). PC1 is NOT the context axis — context info distributed across many PCs.

### §C3 T2 — Per-context PC distribution
- **Script**: same
- **Output**: `results/analysis_T123/T2_pc_context_distribution.{csv,png,pdf}`
- **Findings**: at L=27, PC1 separates contexts into **transcribed (splice_acceptor +2.22, coding +1.46, splice_donor +1.07, 5utr +0.72) vs non-transcribed (3utr −0.72, intergenic −0.49, intron −0.26)**. d_donor-intron(PC4) = −0.43 (PC4 is best single-PC separator).

### §C4 T3 — Position confounder check
- **Script**: same
- **Output**: `results/analysis_T123/T3_pc_position_correlation.{csv,png,pdf}`
- **Findings**: PC1 max \|r\| with token position = 0.339 (single spike at L=2; otherwise <0.1). Confounder REJECTED for L>5. PC2-5 essentially independent.

---

## §D chr17 replication — DONE ★★★★

- **Input**: `chr17/tier1_settling_v2.parquet` (27,586 windows, completed 2026-05-24 21:02) + `chr17_position_labels.npy`
- **Uses chr22-frozen γ_v2 thresholds** (no re-calibration — the whole point of transferability)
- **Script**: `scripts/22_chr17_replication.py`
- **Output**: `results/chr17_replication/`
- **Headline findings**:
  - **Spearman ρ(chr22_d, chr17_d) = 0.989** across 13 valid cells (excluding 4 degenerate M2/M4 refB/C)
  - **Median retention = 97.2%** (gDTR Paper 1 reported 94.6% on a single cell — TDiG generalizes to 17-cell taxonomy)
  - **Sign preserved: 13/13**
  - M5_tau_refB retention 97% (Paper 1 baseline metric equivalent)
  - M3_geo cells 73-90% (slight effect-size attenuation on chr17 but ordering preserved)
  - M1, M4_set cells 105-118% (chr17 effects STRONGER than chr22)
  - chr17 donor n=490,458 (2.6× chr22), intron n=94.9M (2.3× chr22)

---

## §E Bootstrap CIs on chr22 d-values — RUNNING

- **Input**: tier1_settling_v2.parquet (chr22) + pos_labels
- **Script**: `scripts/23_bootstrap_chr22_ci.py`
- **Output (pending)**: `results/bootstrap_chr22_ci/`
  - `bootstrap_d_ci.csv` — 17 cells × {mean_d, ci_low, ci_high, std, n=200}
  - `bootstrap_distributions.png` — histograms with 95% CI bars
- **What it answers**: How wide are the 95% CIs on headline d-values like M3_geo_a0.5_b1.0 d=−0.85? Window-level bootstrap respects window independence.

---

## §G Interpretability experiments (pivoted from variant scoring 2026-05-25)

User reframe: "research goal is interpretability and new discrimination capabilities, not variant calling AUROC chase." This section captures the experiments designed to support that goal.

### §G1 Variant 17-cell ΔC scorer comparison — DONE (negative result)
- **Input**: variant_h_ell_ref/alt h5 (loads 11GB) + γ + Σ_ref
- **Script**: `scripts/24_variant_settling_cells.py`
- **Output**: `results/variant_settling_cells/`
- **Findings**: All 17 cells' |Δc| AUROC for P_LP vs B_LB falls in **0.50-0.64 range**. Best: M5_tau_refC = 0.642, M4_set_refA = 0.629. Scalar ΔH_norm_L2 (§A1) reaches 0.855 — **17-cell |Δc| is inferior as a scorer** because it discards per-layer magnitude information.
- **Paper implication**: TDiG settling cells are valuable as **interpretability/mechanism features**, NOT scorer replacements. Headline scorer remains scalar ΔH norm; TDiG explains/visualizes WHERE in the network the variant effect emerges.

### §G2 Variant mechanism clustering — DONE
- **Input**: variant_scalars.parquet + consequence labels
- **Script**: `scripts/26_variant_clustering.py`
- **Output**: `results/variant_clustering/`
  - `umap_coordinates.csv` — UMAP coords per variant + cluster_id + metadata
  - `cluster_summary.csv` — per-cluster (n, % P_LP, % B_LB, % VUS, dominant gene, dominant consequence)
  - `cluster_signatures.csv` — per-cluster mean ΔH per layer (the "mechanism signature")
  - `clustering_overview.png` — 3-panel UMAP (by category, by consequence, by HDBSCAN cluster)
  - `cluster_signatures.png` — per-cluster layer profile
- **Method**: 64-D feature per variant (32-D log(ΔH norm L2) + 32-D Δcos), StandardScaler → UMAP(n=30, min_dist=0.1) → HDBSCAN(min_cluster_size=50)
- **Findings**: 15 clusters + 1908 noise points (17.5% noise rate). 4 BLB-enriched clusters identified (clusters 1, 2, 3, 5). No PLP-enriched clusters with >70% purity — P_LP variants don't form pure clusters, distributed across multiple mechanism modes. Suggests pathogenic mechanism is heterogeneous; benign signature is more uniform.

### §G3 VUS reclassification — DONE ★★★★
- **Input**: variant_scalars.parquet (8,008 labeled train + 2,902 VUS)
- **Script**: `scripts/27_vus_reclassification.py`
- **Output**: `results/vus_reclassification/`
  - `vus_predictions.csv` — 2,902 VUS with prob_PLP + prediction class + baseline-ΔH agreement
  - `classifier_metrics.csv` — CV metrics: LR(C=1) 0.949, LR(C=0.1) 0.946, GBM 0.950 — **all beat baseline ΔH at L=8 (0.855)**
  - `vus_prob_distribution.png` — bimodal distribution + per-consequence boxplot
  - `summary.json`
- **Headline finding**: **5-fold CV AUROC = 0.949 (best: gbm_n100)**, +9.4 percentage points over scalar ΔH baseline (0.855). Layer-resolved features substantially improve over any single layer.
- **VUS predictions** (2,902 VUS):
  - 1,303 Likely Pathogenic (prob > 0.7)
  - 853 Uncertain (0.3 ≤ prob ≤ 0.7)
  - 746 Likely Benign (prob < 0.3)
  - Baseline ΔH agreement = 67.9%
- **By consequence median VUS prob**: synonymous 0.05 (almost all benign, n=12), intron 0.27, 5utr 0.28, noncoding 0.32, 3utr 0.20, **missense 0.70 (mostly pathogenic, n=2,506)**

### §G4 Cryptic synonymous splice candidates — RUNNING
- **Input**: variant_scalars.parquet + consequence labels (synonymous + intron reference)
- **Script**: `scripts/28_cryptic_synonymous_splice.py`
- **Output (pending)**: `results/cryptic_synonymous/`
  - `synonymous_signature.csv` — per-variant shape features
  - `cryptic_candidates.csv` — top 10% splice-like score variants (candidate cryptic splice)
  - `shape_examples.png` — ΔH curves: typical synonymous (L27 peak) vs cryptic (L8 peak)
  - `summary.json` — P_LP enrichment fold in candidates vs non-candidates
- **What it answers**: Of 1,796 synonymous variants, which have splice-like Δh profiles (L8 peak like intron variants instead of typical L27 peak)? These are candidates for cryptic splice site disruption — a "new discrimination" task SpliceAI/Pangolin may miss.

### §G5 GPU random-alt biological validation — RUNNING (after bfloat16 fix)
- **Input**: 300 P_LP + 300 B_LB variants + hg38 fasta + Evo 2 7B
- **Script**: `scripts/25_random_alt_control.py`
- **Output (pending)**: `results/random_alt_control/`
  - `random_alt_delta_h.parquet` — per (variant, k, layer) ΔH norm for real + 3 random alt
  - `comparison_summary.csv` + `comparison.png` — real vs random ΔH per layer per category
- **What it answers**: Does ΔH at L=8 distinguish *specific ClinVar variants* from *any random mutation at the same position*? If real >> random → biology beyond position-sensitivity.

---

## §H Roadmap — designed but not started

### §H1 Per-pair 7×7 context separation matrix
- All 7 contexts × all 7 contexts → 21 unique Cohen d per (layer, cell)
- L=27 snapshot heatmap = "context hierarchy" figure

### §H2 Intron-outlier functional element discovery
- Within "intron" tokens, top 1% with splice-like settling
- Cross-reference to ENCODE cCRE / TFBS / GWAS loci
- *Unsupervised functional element discovery* — paper highlight candidate

### §H3 L29 phase transition mechanism (SVD)
- L28→L29 and L29→L30 as linear maps, SVD for rotation structure
- Connects §B1, §C1, §A1 findings

### §H4 Per-position multi-task functional prediction
- TDiG features → classifier(is_splice / is_TFBS / is_cCRE / is_GWAS)
- Per-task AUROC quantifies TDiG's *discovery* value

### §H5 Layer-targeted activation patching (GPU)
- Per-variant, patch h_alt → h_ref at one layer, measure downstream Δc
- Causal critical layer identification per variant

### §H6 Composition-matched variant control (GPU, expansion of §G5)
- Full GC + dinucleotide matching (not just random ALT)

### §H7 Cross-architecture (HyenaDNA, NT-v2)
- Generality test for L29 phase transition + bidirectional settling

---

## Reproducibility recipe

```bash
# 1. Pull all tier1/2 caches (chr22 + chr17 + variants) — ~120 GB total
bash scripts/00_pull_cache.sh  # (needs editing for chr17/variants paths)

# 2. Re-run every analysis (scripts run independently; output to local results/):
python scripts/19_variant_analysis_scalars.py --out-dir results/variant_analysis_scalars
python scripts/20_gamma_ablation.py             --out-dir results/gamma_ablation
python scripts/21_variant_per_consequence.py    --out-dir results/variant_per_consequence
python scripts/22_chr17_replication.py          --out-dir results/chr17_replication
python scripts/23_bootstrap_chr22_ci.py         --out-dir results/bootstrap_chr22_ci
python scripts/24_variant_settling_cells.py     --out-dir results/variant_settling_cells

# GPU validation (requires Evo 2 7B):
python scripts/25_random_alt_control.py         --out-dir results/random_alt_control

# Calibration regeneration (if γ_v2 needs re-derivation):
python scripts/10b_calibrate_v2.py  # writes population_stats/gamma_calibration_v2.json
```

## Server reference

- SSH alias: `digitalocean-gpu` → `root@129.212.184.148`
- Project root: `/root/TDiG/`
- Cache: `/root/TDiG/data/cache/` (chr22_v2, chr17, variants, population_stats, _v2_analysis)
- venv: `/root/gDTR/venv/bin/python` (gDTR project's venv reused)
- Logs: `/root/TDiG/data/cache/_v2_analysis/*_run.log`
