# Prompt para Claude Code — FASE 6: análisis
# (solo después de mi validación humana del juez)

Repo `reification-gradient`. El scoring ya está validado. Ejecuta el análisis y prepáralo para lectura.

1. Corre:
   python src/analyze.py
   python src/lingsign_hook.py

2. Para el modelo confirmatorio, añade en `analyze.py` (sin borrar lo existente) un modelo de efectos
   mixtos con statsmodels: logístico para DVs binarios y Poisson para conteos, con efectos fijos
   disorder*level (nivel ordinal) y efectos aleatorios para viñeta y modelo. Reporta los contrastes
   de interacción para H2 (DN vs incoherente) y H3 (DN vs ancla).

3. Genera una tabla legible que cruce cada hipótesis (H1–H5) con su resultado y su criterio de
   falsación de `PLAN.md`, marcando soportada / falsada / no concluyente.

4. Resume `tests.txt`, `reification.csv` y la separabilidad del fingerprint, y dime explícitamente
   qué fracción de los marcadores discriminativos del fingerprint están AUSENTES de la semilla
   (ese es el resultado anticircular de H5).

PROHIBICIONES:
- NO cambies datos ni materiales. Si un resultado sale "feo" o negativo, repórtalo tal cual:
  un resultado negativo limpio es publicable.
