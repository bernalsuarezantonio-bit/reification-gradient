# Reification Gradient

Does an LLM treat an *invented* diagnostic category as increasingly real as the **authority**
of its source rises — and does it *fabricate* clinical structure it was never given? A controlled,
synthetic-only test of the clinician half of Hacking's looping effect.

See `PLAN.md` (preregistration) and `CLAUDE.md` (invariants + how to run).

## Quick start
```bash
pip install -r requirements.txt
python src/check_invariants.py            # anti-circularity gate (must pass)
python src/run_experiment.py --models m1,m2 --reps 5   # wire up query_model() first
python src/score.py                       # wire up judge_response() (blinded)
python src/analyze.py                     # H1–H4 + robustness
python src/lingsign_hook.py               # H5 linguistic fingerprint
```

## What you must wire up
- `src/run_experiment.py: query_model()` — your model provider.
- `src/score.py: judge_response()` — a blinded LLM judge (rubric in `scoring/rubric.md`).
- `src/lingsign_hook.py: lingsign_features()` — your real LingSign extractor.

## Design in one line
4 disorder types (plausible-fiction / real-anchor / incoherent-control / flagged-fiction)
× 5 legitimacy levels × ≥2 model families. Content held constant; only authority escalates.
The contrast **plausible-fiction vs incoherent-control** across levels is the core result
(reification vs sycophancy).

Sandbox-only: no fabricated disorder content leaves this repo.
