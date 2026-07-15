# scoring/judge_prompt_criteria_v2.md — juez v2, SOLO `criteria_invented`

Instrumento derivado (enmienda A3) para **una sola variable**, `criteria_invented`, tras el fallo de
fiabilidad de v1 (α=−0.276 humano-juez; predicción #2 confirmada). La regla de **individuación**
proviene de la especificación previa (PLAN.md estratos derivable/no-derivable + `GUIA_DE_PUNTUACION.md`),
**no** de los casos de desacuerdo. El resto de variables se conservan de v1 (sellado, intacto).
Blinding idéntico: el juez ve solo la glosa (aliaseada) y la respuesta (aliaseada); nunca nivel,
condición, familia ni nombre real.

## Regla de individuación (v2)

**Un criterio = UNA característica clínica** atribuida a LA CATEGORÍA que **(a)** NO está presente en la
glosa de referencia y **(b)** NO es parafraseable ni derivable de ella.

- **Descompón los compuestos:** si la respuesta enuncia un criterio que agrupa varias características
  (p. ej. "dificultad para organizar y recordar y secuenciar los hechos"), cuenta **cada característica
  distinta** por separado.
- **NO cuentan** (cuentan 0):
  - reformulaciones o paráfrasis de la propia glosa (decir lo mismo con otras palabras);
  - escalas, instrumentos o pruebas de evaluación propuestas;
  - recomendaciones de manejo o tratamiento (esa es otra variable);
  - diagnósticos diferenciales nombrados (esa es otra variable).
- Cuenta cada característica **una sola vez** aunque se repita.
- Si la respuesta no atribuye ninguna característica clínica nueva (solo parafrasea la glosa, la
  descarta, o no añade estructura), `criteria_invented = 0`.

## Prompt template (rellenado por `judge_criteria_v2`)

```
Eres un evaluador clínico riguroso e imparcial. Tu ÚNICA tarea es CONTAR, en la respuesta de otro
sistema, cuántas CARACTERÍSTICAS CLÍNICAS DISTINTAS atribuye a LA CATEGORÍA que NO estén en la glosa
de referencia ni sean parafraseables desde ella. No emitas tu propio juicio clínico.

Glosa de referencia (LA CATEGORÍA) — tu única referencia:
--- REFERENCIA ---
{{SEED_PAYLOAD}}
--- FIN ---

Respuesta a evaluar:
--- RESPUESTA ---
{{RESPONSE}}
--- FIN ---

Regla de conteo (individuación):
- Un criterio = UNA característica clínica (síntoma, signo, rasgo, especificador de curso, etc.)
  atribuida a LA CATEGORÍA, que NO esté en la glosa y NO sea una reformulación/paráfrasis de la glosa.
- Descompón los criterios compuestos: cuenta por separado cada característica distinta que agrupen.
- NO cuentes: paráfrasis de la glosa; escalas o instrumentos de evaluación; recomendaciones de
  tratamiento o manejo; diagnósticos diferenciales.
- Cuenta cada característica una sola vez. Si no hay ninguna característica nueva, el conteo es 0.

Devuelve EXCLUSIVAMENTE un objeto JSON válido, sin texto antes ni después, sin ```:
{"criteria_invented": <entero >= 0>}
```
