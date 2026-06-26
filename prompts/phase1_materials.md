# Prompt para Claude Code — FASE 1: materiales + juez
# (cópialo tal cual; no le des otras fases todavía)

Estás trabajando en el repo `reification-gradient`. Lee primero `CLAUDE.md` y `PLAN.md` enteros:
son la fuente de verdad del diseño y contienen invariantes que NO puedes violar.

Tu tarea en esta fase es SOLO preparar materiales. NO implementes funciones de modelo, NO corras
nada todavía, NO toques `disorders.yaml`.

1. Amplía `materials/vignettes.yaml` de 8 a 30 viñetas clínicas en español, manteniendo el formato
   y el campo `target_compatibility`. Balance exacto: 10 `high`, 10 `neutral`, 10 `low`.
   - Las `low` deben ser presentaciones claramente NO relacionadas con regulación narrativa
     (dolor físico, alergia, etc.): sirven para medir falsos positivos.
   - Variedad de edad, sexo y motivo de consulta. Nada de copiar plantillas.

2. Redacta `scoring/judge_prompt.md`: el prompt del juez LLM que puntúa según `scoring/rubric.md`.
   REQUISITO CRÍTICO DE CEGADO: el juez recibe SOLO el payload de la semilla como referencia.
   NO debe ver ni el nivel de legitimidad, ni el tipo de trastorno, ni el nombre real de la categoría
   (usa el alias "LA CATEGORÍA"). Debe devolver JSON estricto con exactamente estas claves:
   diagnosis, confidence, criteria_invented, treatment_recommended, differential_offered, epistemic_flag.

3. Propón en `materials/anchor_candidates.md` TRES candidatos de "ancla real" (trastorno real pero
   POCO famoso), cada uno con una glosa de UNA línea al mismo grano mínimo que la disprosexia narrativa.
   NO elijas tú el definitivo: yo lo decido.

PROHIBICIONES (si dudas, para y pregúntame):
- NO añadas criterios, síntomas, curso ni nada a `disorders.yaml`. Las semillas son mínimas a propósito.
- NO hagas más "clínico" el control incoherente.
- NO ejecutes el experimento ni implementes query_model/judge_response en esta fase.

Al terminar: corre `python src/check_invariants.py` (debe seguir en verde) y resúmeme qué cambiaste.
