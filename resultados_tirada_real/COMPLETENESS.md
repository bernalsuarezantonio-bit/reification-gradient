# COMPLETENESS.md — R2 confirmatory run (prereg-v1)

- Tag: prereg-v1 @ 4b2464f (verified pre- and post-run)
- Config: config_tirada_real.yaml · seed 20260710 · sealed generation {'temperature': 0.7, 'num_ctx': 2048, 'num_predict': 512}
- Cells: **7200/7200**, 0 duplicates, 0 errors, 0 empty. End record present.
- Per family: mistral 3600, qwen 3600 (sequential, one cold load each)
- Coverage: 4 conditions x 5 levels x 60 vignettes x 3 reps
- First row ts: 2026-07-13T11:43:56 · last row ts: 2026-07-14T01:23:41 · end record ts: 2026-07-14T01:23:41
- Latency mistral-small3.1:24b: median 5.5s (min 4.5, max 53.9)
- Latency qwen2.5:32b: median 7.6s (min 5.5, max 129.1)
- Model digests re-verified IDENTICAL to phase2/recognition_probe/MODELS.md (run valid).
- _fallos.log: empty (0 failures).
- Content NOT read by Code (rule 4); scoring is Phase 4.
