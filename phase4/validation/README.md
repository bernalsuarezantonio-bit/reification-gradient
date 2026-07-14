# phase4/validation/ — Fase 4a: validación del juez (piloto)

**SEALED — no abrir `SEALED_mapping.json` ni `SEALED_judge_scores.jsonl` hasta entregar los ratings humanos.**

Muestra del 15% (1.080 respuestas) de la tirada confirmatoria, estratificada, para validar el juez LLM.
El acuerdo se calcula en un prompt posterior, cuando el PI devuelva `ratings.csv`.

**Enmienda A2 (2026-07-14):** la validación humana pasa a **auditoría dirigida n=48** (celdas
DN_plausible|incoherent × L1|L5 × mistral|qwen × 6; solo `diagnosis` y `criteria_invented`). Se añade un
**co-rater LLM** de 4ª familia (`phi4:14b`) que puntúa las 1.080 con el mismo `judge_prompt`. Los lotes
de 1.080 quedan superseded (en git history); el paquete humano activo es `lote_audit.md`.

## Contenido

- `human_rating_package/` — **lo que usa el PI**: `GUIA_DE_PUNTUACION.md`, `CALENTAMIENTO.md` +
  `calentamiento.csv` (práctica, no cuenta), `lote_01.md`…`lote_12.md` (90 respuestas c/u, solo id ciego +
  texto), y `ratings.csv` (a rellenar). No contiene condición, nivel, familia, viñeta, rep ni scores del juez.
- `SEALED_mapping.json` — **SELLADO.** id ciego (H0001–H1080) → celda real (condición/nivel/familia/viñeta/rep).
  Semillas registradas: muestreo `40040`, orden ciego `80080`, calentamiento `12012`. **No abrir hasta
  entregar ratings** (ver una respuesta con su condición sesga el rating restante).
- `SEALED_judge_scores.jsonl` — **SELLADO.** Puntuaciones del juez (gemma2:27b) sobre las 1.080.
- `SEALED_audit_mapping.json` — **SELLADO.** id auditoría (A01–A48) → h_id/celda (semillas 48048/84084).
- `SEALED_corater_scores.jsonl` — **SELLADO.** Puntuaciones del co-rater (phi4:14b) sobre las 1.080.

## Flujo para el PI

1. Lee `GUIA_DE_PUNTUACION.md`. 2. Practica con `CALENTAMIENTO.md` → `calentamiento.csv`.
3. Puntúa `lote_01`…`lote_12` en `ratings.csv` (orden de ids = orden de lotes). 4. Entrega `ratings.csv`.
5. **Solo entonces** se abren los archivos SEALED y se calcula α (umbral prefijado: ≥0.80 éxito /
   0.667–0.80 ajustar y repetir con muestra nueva / <0.667 rediseño).
