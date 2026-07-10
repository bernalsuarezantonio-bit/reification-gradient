# POWER.md — Stage R0: análisis de potencia por simulación

**Objetivo:** justificar **R** (repeticiones por celda) para el prerregistro. Simulación pura
(sin GPU): generamos puntuaciones de rúbrica bajo un modelo dosis-respuesta y corremos la MISMA
familia de tests que quedará prerregistrada, y leemos potencia vs R.

Código: [`power_sim.py`](power_sim.py) · semilla `20260710` · 1000 simulaciones por punto ·
salidas: [`power_curves.csv`](power_curves.csv), [`sensitivity.csv`](sensitivity.csv),
[`chosen_R.txt`](chosen_R.txt).

> **La regla de decisión y la rejilla de efectos de abajo se fijaron ANTES de correr la simulación.**
> Son independientes de los resultados (§6–§7).

---

## 1. Hipótesis que R debe soportar

- **H1 (tendencia):** en `DN_plausible`, la puntuación sube monótona a lo largo de L1→L5.
- **H2 (interacción):** pendiente `DN` > pendiente `incoherente` (reificación, no mera sycophancy).
  **Es la que carga el paper** → la regla de decisión se ancla en H2.

## 2. Modelo generativo (proxy continuo de la rúbrica, escala ~0–4)

Nivel centrado `c_k = -2..2` (L1..L5):

```
Y_{i,k,cond,r} = mu_cond + u_i + slope_{cond,i}·c_k + e_{i,k,cond,r}
slope_{cond,i} = beta_cond + s_i + ss_{cond,i}
u_i  ~ N(0, σ_u²)    intercepto de viñeta      (se cancela en un test de pendiente intra-viñeta)
s_i  ~ N(0, σ_s²)    pendiente aleatoria COMPARTIDA  → limita H1 (R NO la reduce)
ss   ~ N(0, σ_sc²)   pendiente aleatoria por CONDICIÓN → limita H2 (R NO la reduce)
e    ~ N(0, σ_e²)    residual por repetición (estocasticidad de temperatura) → R SÍ la reduce
```

Como cada viñeta se ve en **todos** los niveles, el test de tendencia es **intra-viñeta**: la
pendiente OLS por viñeta es `slope_i + N(0, σ_e²/(10R))` (10 = Σc_k²). Por eso más repeticiones
solo encogen el término residual; **σ_s y σ_sc fijan techos irreducibles**. La puntuación es un
proxy continuo; el análisis prerregistrado usará GLMM por-DV (logística/Poisson), para lo que un
compuesto continuo es un proxy estándar y algo **conservador** (⇒ la R elegida es cota superior segura).

## 3. Rejilla de tamaños de efecto (a priori, en unidades SD de la rúbrica)

Efecto = cambio medio L1→L5 en unidades SD (con SD total ≈ 1.0 en el escenario primario, 1 punto ≈ 1 SD).
Anclada a la literatura de efectos de **framing / autoridad / credibilidad de fuente**, que suelen
caer en Cohen *d* pequeño–medio:

| etiqueta | efecto L1→L5 (SD) | analogía justificatoria |
|---|---|---|
| pequeño | **0.2** | efecto de framing típico mínimo (d≈0.2) |
| medio   | **0.5** | persuasión por credibilidad de fuente / autoridad (d≈0.5) — **escenario de referencia** |
| grande  | **0.8** | manipulación de autoridad fuerte (d≈0.8) |

Misma rejilla para H1 y H2 (según encargo).

## 4. Rangos de varianza (justificación) y ausencia de piloto utilizable

**No hay dato piloto interno utilizable para calibrar la varianza del DV confirmatorio.** La sonda
de reconocimiento (phase2/recognition_probe) es una **tarea distinta** (preguntas de conocimiento,
sin viñetas, sin niveles, sin puntuación de rúbrica), así que no permite estimar σ_e/σ_s/σ_sc del
DV de diagnóstico *sin* mirar estructura irrelevante. Lo único que informa —débilmente— es que a
temperatura 0.7 hay estocasticidad no trivial entre repeticiones (justifica σ_e alto). Por tanto:
**rejilla conservadora**, con σ_e alto en el escenario primario.

| escenario | σ_e (rep) | σ_s (pend. compartida) | σ_sc (pend. por cond.) | σ_u |
|---|--:|--:|--:|--:|
| **primary** (referencia, conservador) | 1.0 | 0.10 | 0.08 | 0.5 |
| low_noise | 0.7 | 0.10 | 0.08 | 0.5 |
| high_slopevar | 1.0 | 0.15 | 0.12 | 0.5 |
| low_slopevar | 1.0 | 0.05 | 0.04 | 0.5 |

(σ_u no entra en el test de pendiente intra-viñeta; se incluye por completitud.)

## 5. Tests y α

Two-stage que replica el modelo mixto prerregistrado para este diseño balanceado (equivalente
asintótico a un LMM con viñeta como efecto aleatorio; algo conservador):
- **H1:** t de una muestra, `media(pendiente DN por viñeta) > 0` (una cola).
- **H2:** t de una muestra pareada, `media(pendiente DN − pendiente INC por viñeta) > 0` (una cola;
  la viñeta compartida cancela σ_s).

α base 0.05; **corrección Bonferroni** por las hipótesis primarias direccionales que declare
`PLAN.md`. Reportamos tres: `0.05` (sin corregir), **`0.0125` (Bonf/4, H1–H4)** ← α de decisión,
y `0.01` (Bonf/5, H1–H5).

## 6. REGLA DE DECISIÓN (pre-fijada)

> **R\* = el mínimo R ∈ {1,2,3,5,8,10} que alcanza ≥80% de potencia para el efecto MEDIO en H2**,
> a α = 0.0125 (Bonf/4), en el escenario de varianza **primary**, **sujeto al tope presupuestario**
> declarado en §8. Si el R que da la potencia excede el tope, se reporta la tensión: la decide el PI.

## 7. Resultados

### Potencia H2 (interacción) — escenario primary

| α | efecto | R=1 | R=2 | R=3 | R=5 | **R=8** | R=10 |
|---|---|--:|--:|--:|--:|--:|--:|
| 0.05 | medio | .42 | .62 | .75 | **.90** | .96 | .97 |
| **0.0125** | medio | .22 | .35 | .54 | .71 | **.86** | .91 |
| 0.01 | medio | .19 | .36 | .50 | .69 | .85 | .87 |
| 0.0125 | pequeño | .05 | .07 | .10 | .13 | .19 | .23 |
| 0.0125 | grande | .51 | .82 | .94 | .99 | 1.0 | 1.0 |

### Potencia H1 (tendencia) — escenario primary

| α | efecto | R=1 | R=2 | R=3 | **R=5** | R=8 | R=10 |
|---|---|--:|--:|--:|--:|--:|--:|
| 0.0125 | medio | .41 | .60 | .76 | **.87** | .95 | .97 |

**H1 medio ya está powered a R=5; H2 medio (más exigente) necesita R=8.** H2 es más costosa porque
el diseño pareado cancela σ_s pero mantiene el doble de ruido residual y σ_sc.

### Sensibilidad (H2 medio, α=0.0125) — el techo irreducible

| escenario | R=1 | R=2 | R=3 | R=5 | **R=8** | R=10 |
|---|--:|--:|--:|--:|--:|--:|
| primary | .21 | .40 | .51 | .72 | **.88** | .91 |
| low_noise | .37 | .68 | .81 | .92 | .97 | .98 |
| **high_slopevar** | .20 | .35 | .45 | .60 | **.72** | .77 |
| low_slopevar | .20 | .41 | .61 | .83 | .96 | .98 |

⚠️ **Si σ_sc es alto (`high_slopevar`), H2 se estanca por debajo de 0.80 incluso a R=10 (.77).** Ese
componente (variabilidad de la *respuesta a la autoridad* entre viñetas, específica de condición)
**no lo reduce R**: fija un techo. Riesgo real a vigilar; ver §9.

(Error Monte-Carlo ≈ ±1.5pp a 1000 sims; las dos estimaciones del punto primary-medio-R8, .86 y .88
en tablas distintas, son consistentes.)

## 8. Presupuesto de GPU por R

Llamadas del modelo = 4 cond × 5 niveles × 30 viñetas × 2 familias × R = **1200·R** (600·R por
familia). Latencias **medidas** en la sonda (qwen ≈ 30× mistral; ojo, domina qwen), extrapoladas a
respuestas clínicas más largas (~512 tok): mistral ~5 s, qwen ~40 s. El "optimista" usa el 2–5 s del
encargo (solo realista para mistral).

| R | llamadas | optimista | **medido (mistral+qwen)** |
|--:|--:|--:|--:|
| 1 | 1 200 | ~1.2 h | **~7.5 h** |
| 2 | 2 400 | ~2.3 h | ~15 h |
| 3 | 3 600 | ~3.5 h | ~22.5 h |
| **5** | 6 000 | ~5.8 h | **~37.5 h** |
| **8** | 9 600 | ~9.3 h | **~60 h** |
| 10 | 12 000 | ~11.7 h | ~75 h |

**Tope presupuestario declarado (asunción, ajústalo):** ~**48 GPU-hours** para el confirmatorio sobre
una GPU compartida e intermitente. Con las latencias medidas, **R=8 (~60 h) EXCEDE el tope**; R=5
(~37.5 h) cabe.

## 9. Recomendación (la R la fija el PI, no Code)

- **Por la regla pura de potencia:** R\* = **8** (H2 medio, .86 a α=0.0125). Pero **~60 GPU-hours**,
  por encima del tope asumido.
- **Tensión potencia↔presupuesto** (a resolver por el PI). Opciones:
  1. **R=8** (~60 h): cumple la regla; requiere ampliar el tope/ventanas de GPU.
  2. **R=5** (~37.5 h): entra en presupuesto y da H1 medio .87 y H2 medio **.90 a α=0.05** pero solo
     **.71 a α=0.0125** (por debajo del umbral tras corrección). Aceptable si se asume efecto ≥ medio-grande
     o se prerregistra α=0.05 para H2.
  3. Reducir el nº de hipótesis primarias corregidas (α menos punitivo) — decisión de diseño del PI.
- **Caveat que ninguna R resuelve:** si la varianza de pendiente por condición (σ_sc) es alta, H2 no
  llega a 0.80 ni con R=10. Mitigaciones (a valorar por el PI, no implementadas): más de 30 viñetas,
  o modelar la heterogeneidad de viñetas explícitamente.
- **Cuello de botella operativo:** qwen es ~30× más lento que mistral y copa >85% del tiempo. Afecta a
  la planificación de ventanas de GPU (R1/R2).

## 10. Reproducir

```bash
.venv/bin/python phase2/power_analysis/power_sim.py   # seed 20260710, 1000 sims/punto
```

---
*Stage R0. STOP tras entregar este informe: la fijación de R, la elección de ancla (DPDR),
la salvaguarda anti-colisión léxica en la rúbrica, la limitación "sin frontier comercial" y el
`git tag -a prereg-v1` los hace el PI — no Code.*
