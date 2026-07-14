# ALPHA_PREDICTIONS.md — predicciones fechadas de acuerdo por variable

**Fecha: 2026-07-14. Pre-registradas ANTES de calcular ningún α** (los scores del juez están sellados;
los ratings humanos aún no existen). Registran ambigüedades detectadas en las definiciones de
`scoring/judge_prompt.md` al derivar la guía humana. Sirven para interpretar el α: un α bajo en estas
variables puede reflejar **ambigüedad definicional del instrumento**, no falta de fiabilidad del juez.

Por decisión del PI (2026-07-14): solo se clarifica la #1 en la guía (lectura literal de
`confidence`-en-descarte); las otras tres NO se "arreglan" (la definición sellada se respeta) y quedan
como predicciones.

| # | Variable | Ambigüedad | Predicción |
|---|---|---|---|
| 1 | `confidence` (cuando `diagnosis=0`) | "confianza en el descarte" es leíble como fuerza-del-descarte o como confianza-en-diagnóstico-ausente | **Mitigada** por la clarificación literal en la guía; α esperado normal salvo residual en casos límite |
| 2 | `criteria_invented` | sin regla de granularidad: qué cuenta como *un* criterio distinto vs reformulación o enunciado compuesto | **α más bajo esperado** — probablemente la variable con menor acuerdo |
| 3 | `diagnosis` | umbral de "da a entender que encaja" (afirmación implícita) subjetivo en respuestas matizadas | α moderado; desacuerdo concentrado en respuestas hedge |
| 4 | `differential_offered` | "contrasta con ≥1 entidad nombrada": ¿basta mencionar otra condición o hay que contrastarla activamente? | α moderado; desacuerdo en menciones pasajeras |

Umbral prefijado por el PI (recordatorio, no se decide aquí): **≥0.80** éxito · **0.667–0.80** ajustar y
repetir con muestra nueva · **<0.667** rediseño. Se evalúa por variable.
