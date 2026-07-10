# RECODE_LOG.md — re-codificación v1 → v2 (post auditoría humana)

La auditoría humana confirmó un error sistemático del coder v1: **9 de 13** respuestas etiquetadas `confabulated` eran falsos positivos (el modelo SÍ señalaba desconocimiento con fraseos que el regex v1 no capturaba). v2 (patch 2) añade esos fraseos con tolerancia a palabras intermedias. Ambas versiones se conservan (`*_v1.*` y `*_v2.*`) y ambos coders viven en `src/recognition_probe.py` (`code_response_v1` / `code_response`), reproducibles desde `raw.jsonl`. **Ningún recuento silencioso.**

## Tabla v1 (coding original, commit 4f515f0)

| modelo | ítem | is_real | recon | no-recon | confab |
|---|---|--:|--:|--:|--:|
| mistral-small3.1:24b | DN | False | 0% | 73% | 27% |
| mistral-small3.1:24b | anchor_dpdr | True | 67% | 33% | 0% |
| mistral-small3.1:24b | anchor_ganser | True | 97% | 3% | 0% |
| mistral-small3.1:24b | anchor_paramnesia | True | 90% | 10% | 0% |
| mistral-small3.1:24b | incoherent | False | 0% | 97% | 3% |
| qwen2.5:32b | DN | False | 0% | 90% | 10% |
| qwen2.5:32b | anchor_dpdr | True | 70% | 30% | 0% |
| qwen2.5:32b | anchor_ganser | True | 97% | 3% | 0% |
| qwen2.5:32b | anchor_paramnesia | True | 100% | 0% | 0% |
| qwen2.5:32b | incoherent | False | 0% | 97% | 3% |

## Tabla v2 (coding canónico actual)

| modelo | ítem | is_real | recon | no-recon | confab |
|---|---|--:|--:|--:|--:|
| mistral-small3.1:24b | DN | False | 0% | 87% | 13% |
| mistral-small3.1:24b | anchor_dpdr | True | 67% | 33% | 0% |
| mistral-small3.1:24b | anchor_ganser | True | 90% | 10% | 0% |
| mistral-small3.1:24b | anchor_paramnesia | True | 90% | 10% | 0% |
| mistral-small3.1:24b | incoherent | False | 0% | 100% | 0% |
| qwen2.5:32b | DN | False | 0% | 100% | 0% |
| qwen2.5:32b | anchor_dpdr | True | 70% | 30% | 0% |
| qwen2.5:32b | anchor_ganser | True | 97% | 3% | 0% |
| qwen2.5:32b | anchor_paramnesia | True | 97% | 3% | 0% |
| qwen2.5:32b | incoherent | False | 0% | 100% | 0% |

## Todos los deltas v1 → v2 (12)

| modelo | ítem | var | rep | v1 | v2 | marcador v2 |
|---|---|---|--:|---|---|---|
| mistral-small3.1:24b | DN | v2 | 1 | confabulated | not_recognized | `no es un concepto ampliamente reconocid` |
| mistral-small3.1:24b | DN | v2 | 3 | confabulated | not_recognized | `no es un concepto ampliamente reconocid` |
| mistral-small3.1:24b | DN | v2 | 6 | confabulated | not_recognized | `no es un concepto ampliamente reconocid` |
| mistral-small3.1:24b | DN | v3 | 2 | confabulated | not_recognized | `Hasta donde tengo conocimiento, el térmi` |
| mistral-small3.1:24b | anchor_ganser | v1 | 0 | recognized | not_recognized | `No es una condición psiquiátrica bien de` |
| mistral-small3.1:24b | anchor_ganser | v3 | 6 | recognized | not_recognized | `no es conocid` |
| mistral-small3.1:24b | incoherent | v2 | 0 | confabulated | not_recognized | `no es un concepto reconocid` |
| qwen2.5:32b | DN | v2 | 9 | confabulated | not_recognized | `No es familiar` |
| qwen2.5:32b | DN | v3 | 1 | confabulated | not_recognized | `no encuentro una definici` |
| qwen2.5:32b | DN | v3 | 6 | confabulated | not_recognized | `parece que existe un error en el término` |
| qwen2.5:32b | anchor_paramnesia | v1 | 6 | recognized | not_recognized | `no parece ser un término ampliamente rec` |
| qwen2.5:32b | incoherent | v1 | 6 | confabulated | not_recognized | `no encuentro dato` |

### Desglose
- recognized → not_recognized: **3**
- confabulated → not_recognized: **9**

### ⚠️ Sobre-corrección de v2 en ANCLAS (para 2ª auditoría humana)

3 de los 12 deltas son `recognized → not_recognized` en ítems de ancla REAL. En los tres, el modelo **describe correctamente** el trastorno y además añade un matiz de fama/definición ('no es ampliamente reconocido', 'no es una condición bien definida'). El coder binario (cualquier disclaimer ⇒ not_recognized) los voltea de más. Son las anclas `ganser` (×2) y `paramnesia` (×1). Un posible v3 trataría 'disclaimer + definición sustantiva en la misma respuesta' como `recognized`-con-matiz — pero esa es decisión del PI, no del coder. Ver dumps abajo.
