# Prompt para Claude Code — FASE 2: cableado + piloto
# (solo después de que yo haya aprobado la Fase 1)

Repo `reification-gradient`. Ya tienes materiales aprobados. Ahora cablea el pipeline y corre SOLO
un piloto. NO corras la batería completa.

1. Implementa `query_model(model, prompt, temperature)` en `src/run_experiment.py` usando
   [INDICA AQUÍ TU PROVEEDOR: Anthropic / OpenAI / local]. Maneja reintentos y errores con gracia.

2. Implementa `judge_response(...)` en `src/score.py` usando `scoring/judge_prompt.md`. El juez debe
   recibir SOLO el payload de la semilla como referencia y devolver el JSON estricto con las 6 claves.
   Respeta el cegado: usa los textos ya aliaseados que la función recibe; no recuperes el nombre real.

3. Implementa `lingsign_features(text)` en `src/lingsign_hook.py` [conéctalo a mi extractor LingSign
   si lo tengo a mano; si no, deja el placeholder y avísame].

4. PILOTO: corre el pipeline en modo reducido — 1 modelo, 2 viñetas, todas las condiciones y niveles
   (haz un flag temporal o un subset; no modifiques el N del prereg). Luego `score.py` sobre ese piloto.

5. Devuélveme para revisión manual: (a) 4–5 respuestas crudas de `data/raw`, (b) sus puntuaciones del
   juez, (c) un `prompt` ensamblado completo para verificar que la semilla + el caso llegan bien.

PROHIBICIONES:
- NO toques `disorders.yaml`, ni el control incoherente, ni el N del preregistro.
- NO valides el scoring del juez tú mismo: la validación humana es una fase aparte y la hago yo.
- NO corras la batería completa todavía.
