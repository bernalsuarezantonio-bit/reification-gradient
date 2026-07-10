# POWER_R0b.md — diagnóstico de latencia de qwen + rejilla conjunta N×R

Dos encargos previos a la decisión de R: (1) diagnóstico de por qué qwen va lento y opciones con
impacto; (2) Stage R0b: potencia en la rejilla conjunta **N_viñetas ∈ {30,45,60} × R ∈ {3,5,8}**,
mismos escenarios (incl. `high_slopevar`), misma regla de decisión, con **GPU-horas por celda**
usando la latencia del diagnóstico.

Código: [`power_sim_r0b.py`](power_sim_r0b.py) · semilla `20260710` · 1000 sims/punto ·
salida [`r0b_grid.csv`](r0b_grid.csv). Modelo/tests/efectos idénticos a R0 (ver [POWER.md](POWER.md)).

---

## 1. Diagnóstico de latencia de qwen (con GPU)

Prompt representativo tipo tirada (266 tok in, `num_predict=512` out), midiendo `/api/ps` **durante**
la llamada.

### Causa: offload a CPU por KV-cache de contexto grande

| config | footprint (`size`) | en VRAM (`size_vram`) | split | throughput | s/llamada (512 tok) |
|---|--:|--:|--:|--:|--:|
| **contexto por defecto** | 46.34 GB | 31.18 GB | **67% GPU / 33% CPU** | 8.8 tok/s | **~70 s** |
| **`num_ctx=2048`** | 21.43 GB | 21.43 GB | **100% GPU** | 70 tok/s | **~7.5 s (caliente)** |

Los pesos de qwen2.5:32b (Q4_K_M) ocupan ~19.85 GB; con la ventana de contexto por defecto, el
KV-cache infla el footprint a **46 GB**, que no cabe en los **32 GB** de la 5090 → ~15 GB caen a
CPU/RAM → las capas en CPU van ~10× más lentas (8.8 vs 70 tok/s).

### Opciones concretas (con impacto estimado)

| opción | acción | impacto s/llamada | coste de calidad | veredicto |
|---|---|---|---|---|
| **A (recomendada)** | fijar `num_ctx=2048` en la config de generación | **~70 → ~7.5 s (~9×)** | ninguno (266 in + 512 out = 778 ≪ 2048) | **usar** |
| B | `num_ctx=1024` | ~7 s (marginal sobre A) | riesgo de truncar si prompt+salida crece | innecesaria |
| C | dejar contexto por defecto | ~70 s | — | descartar (×10 presupuesto) |
| D | usar solo `num_ctx` justo (p. ej. 1536) | ~7.5 s | poco margen | A ya es holgada |

**Recomendación:** **opción A**. Requisito verificable antes del tag: `num_ctx ≥ max_prompt_tokens +
num_predict` con margen; con `num_ctx=2048` y `num_predict=512`, el prompt ensamblado más largo (semilla
+ wrapper L5 + viñeta) debe quedar < ~1500 tok (holgado). mistral (24B, ~15.6 GB) ya entra 100% en GPU;
medido **~5.4 s/llamada** (caliente, ~98 tok/s) en las mismas condiciones.

> Esto es un **parámetro de generación** → va fijado en la config **antes** del `git tag prereg-v1`
> y registrado (regla dura 3). No toca `materials/`.

### Latencias usadas en el presupuesto de R0b (num_ctx=2048, num_predict=512, 100% GPU)

`mistral ≈ 5.4 s/llamada` · `qwen ≈ 7.5 s/llamada` (calientes). Carga en frío ~6–9 s **una vez por
familia** (despreciable sobre miles de llamadas). GPU-horas por celda =
`(4 cond × 5 niveles × N × R) × (5.4 + 7.5) s / 3600`.

---

## 2. Stage R0b — rejilla conjunta N×R (H2 medio, α=0.0125)

`*` = potencia ≥ 0.80. Cada celda: **potencia H2 medio** / **GPU-horas**.

### Escenario primary (referencia, conservador)
| | R=3 | R=5 | R=8 |
|---|---|---|---|
| **N=30** | 0.52 / 6.5h | 0.71 / 10.8h | 0.87* / 17.2h |
| **N=45** | 0.74 / 9.7h | 0.91* / 16.1h | 0.98* / 25.8h |
| **N=60** | 0.86* / 12.9h | 0.96* / 21.5h | 0.99* / 34.4h |

### Escenario high_slopevar (el techo que R sola NO vencía)
| | R=3 | R=5 | R=8 |
|---|---|---|---|
| **N=30** | 0.45 / 6.5h | 0.60 / 10.8h | 0.72 / 17.2h |
| **N=45** | 0.68 / 9.7h | 0.82* / 16.1h | 0.90* / 25.8h |
| **N=60** | 0.81* / 12.9h | 0.90* / 21.5h | 0.96* / 34.4h |

### low_noise / low_slopevar (optimistas)
| escenario | N=30,R=3 | N=45,R=3 | N=60,R=3 |
|---|---|---|---|
| low_noise | 0.82* / 6.5h | 0.94* / 9.7h | 0.98* / 12.9h |
| low_slopevar | 0.60 / 6.5h | 0.80* / 9.7h | 0.90* / 12.9h |

### Celda más barata (mín. GPU-h) que alcanza ≥0.80, por escenario
| escenario | celda | potencia | GPU-h |
|---|---|--:|--:|
| primary | **N=60, R=3** | 0.86 | **12.9** |
| low_noise | N=30, R=3 | 0.82 | 6.5 |
| high_slopevar | **N=60, R=3** | 0.81 | 12.9 |
| low_slopevar | N=45, R=3 | 0.80 | 9.7 |

## 3. Frontera potencia / presupuesto — lecturas

1. **Con el fix de `num_ctx`, el presupuesto deja de ser el problema.** Toda la rejilla cabe en
   6.5–34.4 GPU-h (antes R=8/N=30 se estimaba ~60 h por el offload). Muy por debajo de cualquier
   tope razonable.
2. **N (viñetas) es la palanca contra el techo σ_sc, no R.** En `high_slopevar`, N=30 no llega a 0.80
   ni con R=8 (0.72); pero **N=60, R=3 sí (0.81)** — y cuesta **menos** (12.9 h vs 17.2 h). Añadir
   viñetas reduce el SE del promedio (~√N) y ataca la varianza de pendiente entre viñetas, que más
   repeticiones no tocan.
3. **Más viñetas y menos reps domina a menos viñetas y más reps** en los escenarios con techo:
   N=60/R=3 (12.9 h) ≥ potencia que N=30/R=8 (17.2 h) en primary y high_slopevar, y es más barato.
4. **Robustez a la incertidumbre de varianza:** solo **N=60** (a R≥3) alcanza ≥0.80 en *todos* los
   escenarios conservadores incluido high_slopevar. Si el PI quiere blindar H2 frente al peor caso
   plausible, N=60 es la elección robusta; R puede quedarse bajo (R=3–5).

## 4. Caveat que la decisión debe incorporar (no es de Code)

**Aumentar N por encima de 30 significa AMPLIAR el conjunto de viñetas, que está congelado desde
Fase 1** (`materials/vignettes.yaml`, 30 viñetas, balance 10/10/10). Eso es un cambio de materiales
**pre-freeze** y una decisión del PI: habría que redactar 15 (→45) o 30 (→60) viñetas nuevas
manteniendo el balance y las reglas anti-circularidad, y re-pasar `check_invariants.py`, **antes** del
tag. Code **no** toca `materials/`. Si N se queda en 30, la lectura es la de R0: R=8 para primary
(0.87) y H2 no llega a 0.80 en high_slopevar con ninguna R.

## 5. Reproducir
```bash
.venv/bin/python phase2/power_analysis/power_sim_r0b.py   # seed 20260710, 1000 sims/punto
```

---
*Stage R0b. Sin tag `prereg-v1` → R1/R2 siguen bloqueados. La fijación de N y R, el ancla, la
salvaguarda de rúbrica y el freeze los hace el PI.*
