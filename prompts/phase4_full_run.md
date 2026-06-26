# Prompt para Claude Code — FASE 4: corrida completa
# (solo después de congelar el prereg: git tag prereg-v1 debe existir)

Repo `reification-gradient`. El preregistro está congelado (verifica que existe el tag `prereg-v1`
con `git tag`; si no existe, PARA y avísame: no se corre sin prereg congelado).

1. Corre la batería completa:
   python src/check_invariants.py        # debe pasar
   python src/run_experiment.py --models [M1],[M2] --reps 5
   python src/score.py

2. Reporta: nº de trials escritos, nº de fallos/reintentos, y cualquier respuesta vacía o malformada.

PROHIBICIONES:
- NO modifiques materiales ni el N a mitad de corrida.
- PARA después de `score.py`. NO ejecutes `analyze.py` ni valides el juez: eso viene después y la
  validación humana la hago yo.
- Si algo falla a mitad, NO improvises cambios en las semillas para "arreglarlo": avísame.
