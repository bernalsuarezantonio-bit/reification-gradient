# AGREEMENT_RESULTS.md — validación del juez (Fase 4a / 5)

Fecha: 2026-07-14. Calculado tras la entrega de los 48 ratings humanos. Krippendorff's α
(diagnosis/binarias = nominal; criteria_invented/confidence = intervalo) + IC95 bootstrap (5000,
semilla 20260714) + acuerdo crudo. Umbrales prefijados: **≥0.80** éxito · **0.667–0.80** ajustar y
repetir · **<0.667** rediseño (PLAN §6: si <.70, la DV pasa a scoring humano-only).

## Humano vs Juez (gemma2:27b) — auditoría dirigida n=48

| variable | α | IC95 | acuerdo crudo | veredicto |
|---|--:|---|--:|---|
| **diagnosis** | **0.830** | [0.604, 1.000] | 93.8% | **ÉXITO (≥.80)** |
| **criteria_invented** | **−0.276** | [−0.480, −0.065] | 22.9% (≤±1: 45.8%) | **REDISEÑO (<.667)** |

## Juez (gemma2:27b) vs Co-rater (phi4:14b) — n=1077 de 1080 (3 malformados del juez excluidos)

| variable | α | acuerdo crudo | veredicto |
|---|--:|--:|---|
| **diagnosis** | **0.958** | 98.0% | ÉXITO (≥.80) |
| confidence | −0.188 | 50.8% | REDISEÑO |
| **criteria_invented** | **−0.076** | 31.8% | REDISEÑO |
| treatment_recommended | 0.350 | 73.8% | REDISEÑO |
| differential_offered | 0.717 | 99.4% | AJUSTAR+REPETIR |
| epistemic_flag | 0.547 | 84.2% | REDISEÑO |

## Lectura (sin decidir — la decisión es del PI)

1. **`diagnosis` es fiable.** La DV binaria primaria de H1/H2 pasa: α=.83 humano-juez (aunque el IC
   es ancho por n=48 + desbalance: 37×0/11×1) y α=.96 juez-co-rater (raw 98%). El juez automático
   sirve para `diagnosis`.
2. **`criteria_invented` FALLA de forma robusta.** α **negativo** en ambas comparaciones
   (humano-juez −.28, juez-co-rater −.08): peor que el azar. Confirma la predicción #2 de
   `ALPHA_PREDICTIONS.md` (ambigüedad de granularidad: qué cuenta como *un* criterio distinto). El
   humano contó conservador (34/48 = 0), el juez más liberal. **Como es una DV central de reificación
   (H1/H2 la ponderan), esto es el hallazgo importante de la validación.** Por umbral → rediseño de la
   definición (regla de granularidad) + revalidar con muestra nueva, o scoring humano-only (PLAN §6).
3. **Paradoja de α con clases desbalanceadas** — a tener en cuenta al interpretar: `treatment`,
   `differential` y `epistemic` tienen **acuerdo crudo alto** (74–99%) pero **α bajo/medio** porque una
   categoría domina (α penaliza fuerte cuando casi todo es una clase). No sobre-interpretar su α como
   "no fiable" sin mirar el crudo; son DVs secundarias.
4. **`confidence`** (continua) muestra α negativo entre los dos LLMs: escalas de confianza no
   alineadas entre modelos (predicción #1, dimensión LLM-LLM).

## Predicciones vs resultado
Las predicciones fechadas de `ALPHA_PREDICTIONS.md` se cumplen: #2 (`criteria_invented`) es la peor;
`diagnosis` la más fiable. Registro honesto: el instrumento es fiable para *si* diagnostica, no para
*cuánta estructura* cuenta.
