# Tabla resumen — sonda de reconocimiento (ítem × modelo)

Codificación mecánica (sin juez). `recognized`/`confabulated` según la verdad-terreno del ítem cuando NO hay disclaimer explícito; `not_recognized` = disclaimer explícito de desconocimiento. Sin comentario interpretativo (lectura y decisión del PI).

| modelo | ítem | is_real | N | recon. | no-recon. | confab. | %recon | %no-recon | %confab |
|---|---|---|--:|--:|--:|--:|--:|--:|--:|
| mistral-small3.1:24b | DN (`disprosexia narrativa`) | False | 30 | 0 | 26 | 4 | 0% | 87% | 13% |
| mistral-small3.1:24b | anchor_dpdr (`trastorno de despersonalización-desrealización`) | True | 30 | 20 | 10 | 0 | 67% | 33% | 0% |
| mistral-small3.1:24b | anchor_ganser (`síndrome de Ganser`) | True | 30 | 27 | 3 | 0 | 90% | 10% | 0% |
| mistral-small3.1:24b | anchor_paramnesia (`paramnesia reduplicativa`) | True | 30 | 27 | 3 | 0 | 90% | 10% | 0% |
| mistral-small3.1:24b | incoherent (`síndrome de regresión alotrópica vespertina`) | False | 30 | 0 | 30 | 0 | 0% | 100% | 0% |
| qwen2.5:32b | DN (`disprosexia narrativa`) | False | 30 | 0 | 30 | 0 | 0% | 100% | 0% |
| qwen2.5:32b | anchor_dpdr (`trastorno de despersonalización-desrealización`) | True | 30 | 21 | 9 | 0 | 70% | 30% | 0% |
| qwen2.5:32b | anchor_ganser (`síndrome de Ganser`) | True | 30 | 29 | 1 | 0 | 97% | 3% | 0% |
| qwen2.5:32b | anchor_paramnesia (`paramnesia reduplicativa`) | True | 30 | 29 | 1 | 0 | 97% | 3% | 0% |
| qwen2.5:32b | incoherent (`síndrome de regresión alotrópica vespertina`) | False | 30 | 0 | 30 | 0 | 0% | 100% | 0% |

N por celda = 30 (3 variantes × 10 reps). Total = 300 respuestas, 0 errores.
