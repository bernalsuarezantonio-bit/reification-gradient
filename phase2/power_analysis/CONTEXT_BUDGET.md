# CONTEXT_BUDGET.md — Parte B: presupuesto de contexto y `num_ctx` verificado

Objetivo: fijar el `num_ctx` mínimo (con margen) para la tirada real, con evidencia empírica de que
ambos modelos caben 100% en VRAM. Sin GPU pesada (medición con `num_predict=1`; verificación = 1
llamada por modelo). Código: [`context_budget.py`](context_budget.py) · datos:
[`context_budget.csv`](context_budget.csv).

## 1. Estímulos y tokenización (viñeta más larga del set de 60 = v12)

Los 20 estímulos completos = 4 condiciones × 5 niveles, ensamblados con `run_experiment.wrap` +
`build_prompt` (instrucción de tarea real incluida) sobre **v12** (la viñeta más larga). Tokens de
entrada exactos vía `prompt_eval_count` de **cada modelo**:

**Tokens de entrada — mistral-small3.1:24b**
| cond \ nivel | L1_forum | L2_coach | L3_wiki | L4_preprint | L5_pseudodsm |
|---|--:|--:|--:|--:|--:|
| DN_plausible | 612 | 585 | 557 | 581 | 549 |
| real_anchor | 603 | 582 | 553 | 578 | 545 |
| incoherent | 623 | 599 | 571 | 595 | 555 |
| DN_flagged | **650** | 604 | 576 | 600 | 568 |

**Tokens de entrada — qwen2.5:32b** (tokeniza el español ~2× más compacto)
| cond \ nivel | L1_forum | L2_coach | L3_wiki | L4_preprint | L5_pseudodsm |
|---|--:|--:|--:|--:|--:|
| DN_plausible | 305 | 276 | 246 | 267 | 243 |
| real_anchor | 293 | 270 | 240 | 261 | 237 |
| incoherent | 317 | 292 | 262 | 283 | 249 |
| DN_flagged | 351 | 299 | 269 | 290 | 266 |

**MÁXIMO GLOBAL de entrada = 650 tok** (mistral, `DN_flagged × L1_forum`). mistral es el que manda
(su tokenizador es ~2× menos compacto que el de qwen). Nota: el máximo cae en **L1_forum**, no en L5
— medido, no supuesto (el wrapper de foro resulta ser el más largo; DN_flagged añade la disclosure).

## 2. Propuesta de `num_ctx`

Regla: `num_ctx` = mínima potencia de 2 ≥ (máx_entrada + `num_predict` + 15% margen).

```
máx_entrada = 650 ;  num_predict = 512
650 + 512 = 1162 ;  ×1.15 = 1336
mínima potencia de 2 ≥ 1336  ->  num_ctx = 2048
```

**Propuesta: `num_ctx = 2048`.** (El PI anticipó ~4096; el dato lo baja a 2048. Holgura real: 2048 vs
1162 necesarios = **+76%**.) Alternativa conservadora `4096` si se quisiera más margen de salida (p.
ej. subir `num_predict`): también cabe en VRAM (~+2 GB de KV cache); es decisión del PI al sellar los
parámetros de generación.

## 3. Verificación empírica (1 llamada/modelo, estímulo máximo, `num_ctx=2048`, `num_predict=512`)

| modelo | footprint | en VRAM | split | out | throughput | latencia (caliente) |
|---|--:|--:|--:|--:|--:|--:|
| mistral-small3.1:24b | 15.59 GB | 15.59 GB | **100% GPU** | 512 tok | 97.4 tok/s | ~5.4 s (eval 5.3 s) |
| qwen2.5:32b | 21.43 GB | 21.43 GB | **100% GPU** | 512 tok | 69.7 tok/s | ~7.5 s (eval 7.3 s) |

**Ambos 100% GPU con `num_ctx=2048`.** Ningún modelo sale de VRAM → no se requiere KV-cache cuantizado
ni otras mitigaciones.

## 4. GPU-horas de la tirada real (N=60 × 4 × 5 × R=3 × 2 familias = 7 200 llamadas)

3 600 llamadas por familia. Con las latencias medidas (calientes, `num_ctx=2048`, `num_predict=512`):

| familia | llamadas | s/llamada | horas |
|---|--:|--:|--:|
| mistral | 3 600 | ~5.4 | **~5.4 h** |
| qwen | 3 600 | ~7.5 | **~7.5 h** |
| **total (secuencial)** | 7 200 | — | **~13.0 h** |

(+ una carga en frío por familia ~6–9 s, despreciable.) Consistente con la celda `N=60, R=3` de R0b
(~12.9 h). El scoring del juez (Fase 4) es aparte.

## 5. Para sellar en la config antes del tag (lo hace el PI)

`num_ctx = 2048` · `num_predict = 512` · `temperature = 0.7` · endpoint `/api/chat` `stream:false` ·
secuencial por familia. Digests de modelos en `phase2/recognition_probe/MODELS.md`.
