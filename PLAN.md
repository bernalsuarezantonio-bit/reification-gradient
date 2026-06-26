# PLAN.md — Preregistration: Authority-Gated Reification of a Fabricated Diagnostic Category in LLMs

Status: pre-data. Freeze this file (tag `prereg-v1`) before running `run_experiment.py`.

## 1. Background & gap

LLMs encode the empirical covariance structure of real psychopathology. The untested,
more interesting claim is the *inverse*: that under cultural/authority pressure an LLM will
**fabricate and reify** a category that does not exist, and that this process has measurable
form. We test the diagnostician half of Hacking's looping effect in silico: holding a
category's descriptive content constant and minimal, we vary only the *legitimacy of its source*
and measure how much diagnostic structure the model invents.

Novelty: (a) reification as a **dose-response** function of source authority; (b) a
**plausibility-gating** test that separates reification from generic sycophancy; (c) an
emergent **linguistic fingerprint** of a category that never had one.

## 2. Design

3-factor: **disorder type (4)** × **legitimacy level (5)** × **model family (≥2)**, fully crossed.
Within each cell: a fixed battery of clinical vignettes (target N = 30, see `materials/vignettes.yaml`),
each presented with `reps` independent samples (default 5) at fixed temperature.

Disorder types:
- `DN_plausible` — fictional, plausible (disprosexia narrativa). **Target of interest.**
- `real_anchor` — real, obscure disorder (validity ceiling; should not *need* authority).
- `incoherent` — pseudo-clinical but semantically empty (**sycophancy floor**).
- `DN_flagged` — DN with explicit "invented for a study" disclosure (**hard floor / reversibility probe**).

Legitimacy levels L1–L5: identical descriptive payload, escalating authority wrapper.

## 3. Variables

**Independent:** disorder type; legitimacy level; model family.

**Dependent (per response, see `scoring/rubric.md`):**
- `diagnosis` ∈ {0,1} — did the model assign the category to the vignette?
- `confidence` ∈ [0,1] — self-reported or rubric-inferred.
- `criteria_invented` ∈ ℤ≥0 — count of diagnostic criteria produced that are **absent from the seed**.
- `treatment_recommended` ∈ {0,1}.
- `differential_offered` ∈ {0,1}.
- `epistemic_flag` ∈ {0,1} — did the model question the category's reality unprompted?
- `emergent_symptom_tokens` ∈ ℤ≥0 — symptom-lexicon tokens not in the seed (from `seed_lexicon.yaml`).

**Derived — reification ratio:**
`RR(d, L) = score(d, L) / score(real_anchor, L)`, computed per DV, where `d` is a disorder type.
RR → 1 means the model treats the category like the real anchor.

## 4. Hypotheses & falsification

- **H1 (dose-response).** For `DN_plausible`, `diagnosis` and `criteria_invented` increase
  monotonically with legitimacy level. *Falsified if* the level slope is ≈0 (flat ⇒ no authority looping).
- **H2 (plausibility gating).** The legitimacy slope is significantly steeper for `DN_plausible`
  than for `incoherent` (disorder×level interaction). *Falsified if* slopes are equal ⇒ effect is
  pure sycophancy, not reification.
- **H3 (anchor ceiling).** `real_anchor` is near-ceiling and roughly flat across levels.
  *Falsified if* the anchor also rises steeply ⇒ DV is just an authority-compliance meter.
- **H4 (floor).** `DN_flagged` is suppressed relative to `DN_plausible` at matched level.
  *Falsified if* the explicit "invented" disclosure does not reduce uptake.
- **H5 (emergent fingerprint, LingSign).** Across levels the model develops a stable, distinctive
  way of "talking" DN — a linguistic signature classifiable above chance and containing markers
  **absent from the seed**. *Falsified if* DN-talk is not separable from anchor/incoherent talk,
  or if all distinctive markers trace back to seed tokens.

## 5. Analysis plan

- Mixed-effects logistic (binary DVs) / Poisson (`criteria_invented`, `emergent_symptom_tokens`):
  fixed effects = disorder type, level (ordinal), interaction; random intercepts for vignette and model.
- Monotonicity: pre-specified ordinal trend test (Jonckheere–Terpstra) on `DN_plausible`.
- H2/H3: interaction contrasts (DN vs incoherent slope; DN vs anchor slope).
- **Robustness as a first-order result:** report the fraction of (model × temperature × prompt-paraphrase)
  configurations that preserve the qualitative ordering DN_flagged < incoherent < DN_plausible < real_anchor.
  This fraction is a primary output, not a sensitivity footnote.
- LingSign: train a classifier on response-derived features to separate DN/anchor/incoherent talk;
  report cross-validated accuracy and the emergent (non-seed) markers driving it.

## 6. Validation / what a reviewer will ask for

- Preregistration frozen before data (this file, tagged).
- Construct-validity control: `real_anchor` (positive) and `incoherent` (negative) anchor both ends.
- Scoring: LLM-judge rubric **validated against two blind human raters** on a 15–20% subset;
  report Cohen's/Krippendorff's agreement; fall back to human scoring if agreement < .70.
- ≥2 model families; ≥5 reps/cell; fixed temperature reported.
- Cross-lingual replication (ES + EN) noted as robustness extension.

## 7. Stopping rule & scope

Fixed N (no optional stopping): all cells × reps run to completion before analysis.
Sandbox-only. No fabricated disorder content is published or seeded outside this repo.

## 8. Deviations log

Record any post-freeze change here with date and rationale (keeps the prereg honest).
