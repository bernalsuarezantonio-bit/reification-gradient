# CLAUDE.md — Reification Gradient

Repo guide for Claude Code. Read this before touching anything.

## What this is

An experiment that tests **authority-gated reification** in LLMs: does a model treat an
*empty* (invented) diagnostic category as increasingly real as the legitimacy of the source
describing it increases? This is a controlled, in-silico operationalization of Ian Hacking's
*looping effect* — the clinician half of the loop (model-as-diagnostician).

The core fictional category is **disprosexia narrativa** (DN): a deliberately *minimal*
gloss with no committed symptom list. Content is held constant; only the **authority wrapper**
escalates (L1 forum → L5 pseudo-DSM). What we measure is whether the model *fabricates*
structure (criteria, treatments, differentials) it was never given, and whether that
fabrication scales with authority.

## The one thing that can kill this study: circularity

The whole result collapses if symptom content leaks into the **seed material**. If the seed
already lists the criteria, then "the model produces criteria" is parroting, not reification.

**Invariants (enforced by `src/check_invariants.py`, run before every experiment):**

1. **Seed minimality.** Every disorder seed is a name + a one-line upstream gloss. No seed may
   contain any term in `scoring/seed_lexicon.yaml: forbidden_symptom_terms`. CI fails otherwise.
2. **Content constancy across legitimacy levels.** The *descriptive payload* of a disorder is
   byte-identical across L1–L5; only the wrapper template changes. Levels differ in *form/authority*,
   never in *content*. `check_invariants.py` diffs the payload across levels.
3. **Emergence is the signal.** Any symptom-language the model emits that is NOT in the seed
   lexicon is *emergent* and counts toward reification. The lexicon is the reference set used to
   separate parroting from fabrication — it is not a filter on the model's output.
4. **Plausibility is a control, not a confound.** The incoherent control (semantically empty
   pseudo-clinical noise) shares the authority wrappers. If it reifies too, we measured sycophancy,
   not reification. Never let the incoherent control accidentally become coherent during editing.

## Conditions (the 2×... design)

- **Disorder type** (4): `DN_plausible` (fictional, plausible) · `real_anchor` (real, obscure) ·
  `incoherent` (sycophancy control) · `DN_flagged` (DN + explicit "invented for a study" flag = hard floor).
- **Legitimacy level** (5): L1 forum · L2 coach blog · L3 wiki · L4 preprint · L5 pseudo-DSM.
- **Model family** (≥2): replicate to rule out single-model artifact.

## How to run

```bash
python src/check_invariants.py          # MUST pass; gate for everything below
python src/run_experiment.py --models <m1>,<m2> --reps 5
python src/score.py        data/raw/    # rubric scoring + emergent-lexicon tagging
python src/analyze.py      data/scored/ # dose-response curves, interaction, reification ratio
python src/lingsign_hook.py data/scored/  # linguistic-fingerprint layer (optional but recommended)
```

## Do / Don't

- DO keep all stimulus material in `materials/`. Never inline a stimulus in code.
- DO blind the scorer to condition where possible (`score.py` strips condition labels before LLM-judge scoring).
- DON'T add criteria to the DN seed "to make it work." If it needs criteria to be diagnosed, that *is* the finding.
- DON'T seed false disorder content anywhere outside this sandbox. Synthetic-only, by design and by ethics.
