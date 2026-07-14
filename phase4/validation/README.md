# phase4/validation/ — Fase 4a: validación del juez (piloto)

**SEALED — no abrir `SEALED_mapping.json` ni `SEALED_judge_scores.jsonl` hasta entregar los ratings humanos.**

Muestra del 15% (1.080 respuestas) de la tirada confirmatoria, estratificada, para validar el juez LLM
contra rating humano (Krippendorff's α por variable). El acuerdo se calcula en un prompt posterior,
cuando el PI devuelva `human_rating_package/ratings.csv` completo.

## Contenido

- `human_rating_package/` — **lo que usa el PI**: `GUIA_DE_PUNTUACION.md`, `CALENTAMIENTO.md` +
  `calentamiento.csv` (práctica, no cuenta), `lote_01.md`…`lote_12.md` (90 respuestas c/u, solo id ciego +
  texto), y `ratings.csv` (a rellenar). No contiene condición, nivel, familia, viñeta, rep ni scores del juez.
- `SEALED_mapping.json` — **SELLADO.** id ciego (H0001–H1080) → celda real (condición/nivel/familia/viñeta/rep).
  Semillas registradas: muestreo `40040`, orden ciego `80080`, calentamiento `12012`. **No abrir hasta
  entregar ratings** (ver una respuesta con su condición sesga el rating restante).
- `SEALED_judge_scores.jsonl` — **SELLADO.** Puntuaciones del juez sobre las 1.080. Se genera en el Paso 2
  (juez cegado); no mirar hasta tener los ratings humanos.

## Flujo para el PI

1. Lee `GUIA_DE_PUNTUACION.md`. 2. Practica con `CALENTAMIENTO.md` → `calentamiento.csv`.
3. Puntúa `lote_01`…`lote_12` en `ratings.csv` (orden de ids = orden de lotes). 4. Entrega `ratings.csv`.
5. **Solo entonces** se abren los archivos SEALED y se calcula α (umbral prefijado: ≥0.80 éxito /
   0.667–0.80 ajustar y repetir con muestra nueva / <0.667 rediseño).
