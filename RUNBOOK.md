# RUNBOOK.md — Cómo ejecutar el estudio, paso a paso

Lee esto de arriba abajo. Cada fase dice: **qué haces TÚ**, **qué hace CODE**, **qué documento se usa**
y **el candado** (la decisión que NO puedes delegar). Los mensajes literales para Claude Code están en
`prompts/`. No le des el repo entero de golpe: ve fase por fase y revisa entre cada una.

Regla de oro: **el preregistro (`PLAN.md`) se congela ANTES de la primera corrida real.** Si corres y
luego cierras el prereg, deja de ser preregistro.

---

## FASE 0 — Setup (TÚ · ~15 min)

- [ ] Coloca el repo y entra: `cd reification-gradient`
- [ ] `git init && git add -A && git commit -m "scaffold"`
- [ ] `pip install -r requirements.txt`
- [ ] `python src/check_invariants.py` → debe decir **All hard invariants pass**.
- **Documento:** `README.md`, `CLAUDE.md`.
- **Candado:** si el gate NO pasa, para. Algo en `materials/` se rompió; arréglalo antes de seguir.

---

## FASE 1 — Materiales + juez (CODE hace · TÚ revisas)

- [ ] Pásale a Code **`prompts/phase1_materials.md`**.
- Code: amplía `materials/vignettes.yaml` a **30 viñetas balanceadas** (10 high / 10 neutral / 10 low),
  redacta el **prompt del juez cegado** en `scoring/judge_prompt.md`, y propone **3 candidatos de ancla real**.
- **Documentos que toca:** `vignettes.yaml`, `rubric.md`, `seed_lexicon.yaml`, `disorders.yaml`.
- **Candado (TÚ decides, no Code):**
  - [ ] **Ancla real:** elige una real pero *poco famosa* y glósala al mismo grano mínimo que la DN
        (si el modelo la reconoce al instante, el techo se satura y pierdes resolución).
  - [ ] **Balance de viñetas:** revisa que las `low` sean de verdad no relacionadas (miden falsos positivos).
  - [ ] **Juez cegado:** confirma que el prompt del juez NO menciona nivel de legitimidad ni tipo de trastorno.
- [ ] Vuelve a correr `python src/check_invariants.py` (sigue en verde).
- [ ] Commit: `git commit -am "phase1 materials + judge"`.

---

## FASE 2 — Cableado + piloto (CODE hace · TÚ revisas)

- [ ] Pásale a Code **`prompts/phase2_wire_and_pilot.md`**.
- Code: implementa `query_model()` (run_experiment), `judge_response()` (score), `lingsign_features()`
  (lingsign_hook), y corre un **PILOTO**: 1 modelo × 2 viñetas × todas las condiciones/niveles.
- **Documentos que toca:** `src/run_experiment.py`, `src/score.py`, `src/lingsign_hook.py`.
- **Candado (TÚ revisas la salida del piloto):**
  - [ ] ¿El juez devuelve los 6 DVs en formato parseable? Lee 4–5 respuestas crudas a mano.
  - [ ] ¿El tag de tokens emergentes está contando lo razonable? (mira `emergent_symptom_tokens`).
  - [ ] ¿El prompt al modelo llega bien ensamblado (semilla + caso)? Revisa un `prompt` en `data/raw`.
- **Por qué piloto:** la corrida completa son 4×5×30×5×2 = **6.000 llamadas** + 6.000 de juez. Un bug en
  el prompt del juez te quema el presupuesto. El piloto lo caza barato.

---

## FASE 3 — Congelar el preregistro (TÚ · decisión)

- [ ] Cierra los dos huecos abiertos en `PLAN.md`:
  - [ ] Umbral de acuerdo inter-juez (placeholder: **α ≥ .70**; sube/baja con criterio).
  - [ ] **Cross-lingual ES+EN:** ¿confirmatorio o robustez? (recomiendo robustez para no inflar el N).
- [ ] Revisa que H1–H5 y sus criterios de falsación siguen reflejando el diseño real tras la Fase 1.
- [ ] **Congela:** `git commit -am "freeze prereg" && git tag prereg-v1`
- **Documento:** `PLAN.md`.
- **Candado:** a partir de aquí, cualquier cambio va al **log de desviaciones** (§8 de PLAN.md), con fecha y motivo.

---

## FASE 4 — Corrida completa (CODE ejecuta)

- [ ] Pásale a Code **`prompts/phase4_full_run.md`**.
- Code: `run_experiment.py --models m1,m2 --reps 5` y luego `score.py`.
- **Documentos:** salidas a `data/raw/` y `data/scored/`.
- **Candado:** Code **NO** valida su propio scoring (eso es la Fase 5, y es tuya). Code para tras `score.py`.

---

## FASE 5 — Validación humana del juez (TÚ + 2º rater · NO delegable)

- [ ] Toma un **15% aleatorio** de respuestas y puntúalas a ciegas con `rubric.md`.
- [ ] Segundo rater independiente (otra persona, o como mínimo un 2º modelo NO usado como juez).
- [ ] Calcula Krippendorff's α juez-vs-humano por cada DV.
  - Si **α ≥ umbral** → el scoring automático vale.
  - Si **α < umbral** → ese DV pasa a scoring humano-only. Documéntalo en el log de desviaciones.
- **Documento:** `rubric.md`.
- **Candado:** Code puede ser el juez, pero **no puede ser quien lo valida** — sería circular. Por eso esta fase es humana.

---

## FASE 6 — Análisis (CODE ejecuta · TÚ lees)

- [ ] Pásale a Code **`prompts/phase6_analyze.md`**.
- Code: `analyze.py` + `lingsign_hook.py`; genera `summary.csv`, `reification.csv`, `tests.txt`.
- **Lee tú:**
  - [ ] H1: ¿tendencia monótona creciente en DN_plausible? (`tau`, `p`)
  - [ ] **H2 (el resultado que carga el paper):** ¿slope_DN ≫ slope_incoherente? Reificación, no sycophancy.
  - [ ] H3: ¿el ancla real está cerca de techo y plana?
  - [ ] H4: ¿DN_flagged suprimido vs DN_plausible?
  - [ ] H5: ¿separabilidad del fingerprint por encima del azar y marcadores ausentes en la semilla?
  - [ ] **Robustez:** fracción de slices que preservan el orden. Es un resultado de primer orden, repórtalo.
- **Documentos:** `data/scored/tests.txt`, `reification.csv`.

---

## FASE 7 — Interpretación y escritura (TÚ)

- [ ] Mapea cada resultado a su hipótesis y a su criterio de falsación (un resultado negativo limpio es publicable).
- [ ] Decide venue: **Computational Psychiatry** como primaria; filosofía de la psiquiatría/STS si el ángulo Hacking domina.
- [ ] Declara la limitación reflexiva (looping effects de Hacking aplican también a TU instrumento — es honestidad, no debilidad).

---

## Las 5 cosas que JAMÁS delega a Code (resumen)

1. Congelar `PLAN.md` antes de correr (orden temporal).
2. La validación humana del juez (Fase 5).
3. Tocar `disorders.yaml` para "que funcione" la DN → eso ES el resultado (no-generatividad).
4. "Mejorar" el control incoherente hasta que suene clínico → mata el contraste H2.
5. La elección del ancla real (real pero poco famosa, grano mínimo).
