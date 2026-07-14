# MODELS.md — Provenance de los modelos de la sonda de reconocimiento

**Por qué esto existe:** los tags de Ollama (`mistral-small3.1:24b`, `qwen2.5:32b`) son *punteros
móviles* — un `ollama pull` posterior puede reapuntar el mismo tag a otros pesos. El **digest
sha256 es el hash real de los pesos**. Sin digest registrado no hay reproducibilidad: cualquiera
que quiera replicar debe poder verificar que corrió exactamente estos pesos.

Fuente: `GET http://<OLLAMA_BASE_URL>/api/tags` (host LAN, servido desde la RTX 5090; la URL vive
en `.env`, no se versiona). Consultado el 2026-07-10.

## Modelos usados (2 familias, todo local — sin API comercial)

| campo | mistral-small3.1:24b | qwen2.5:32b |
|---|---|---|
| **digest (sha256)** | `b9aaf0c2586a8ed8105feab808c0f034bd4d346203822f048e2366165a13f4ea` | `9f13ba1299afea09d9a956fc6a85becc99115a6d596fae201a5487a03bdc4368` |
| tamaño | 15 486 899 116 B (15.49 GB) | 19 851 349 669 B (19.85 GB) |
| familia | mistral3 | qwen2 |
| parámetros | 24.0B | 32.8B |
| cuantización | Q4_K_M | Q4_K_M |
| `modified_at` (servidor) | 2026-05-26T08:37:25+01:00 | 2026-07-10T10:47:53+01:00 |
| pull en esta sesión | no (preexistente en el servidor) | **sí** (`POST /api/pull` el 2026-07-10) |

## Parámetros de generación en la sonda

Idénticos para ambos modelos:

- endpoint: `POST /api/chat`, `stream: false`
- **temperatura: 0.7** (default del estudio)
- **tope de tokens: `num_predict` = 220** (suficiente para juzgar reconocimiento; acota el tiempo de GPU)
- diseño: 5 ítems × 3 variantes de pregunta × 10 reps = 150 llamadas/modelo (300 en total)
- ejecución **secuencial por familia** (mistral completo y luego qwen): una sola carga en frío por familia
- 0 errores en las 300 llamadas

## Nota de fallback (no aplicada)

El plan preveía bajar a `qwen2.5:14b` si `qwen2.5:32b` no cabía en VRAM. La llamada de prueba a
`qwen2.5:32b` cargó y respondió correctamente (carga en frío ~14 s; latencia de generación en la
sonda: mediana ~25 s/llamada, rango 17–41 s). **Fallback no necesario.**

## Justificación del diseño 100% local (para el log de fases)

Decisión del PI: ambas familias locales, sin modelos comerciales. Motivos registrados:
(1) **reproducibilidad** — pesos fijados y verificables por digest, no endpoints de API que
cambian sin aviso; (2) **coherencia con la línea representacional** del estudio. La limitación
correspondiente ("sin modelos frontier comerciales en la evidencia") la declarará el PI en
`PLAN.md` antes del freeze; aquí solo se registra la decisión, no se decide.

## Modelo JUEZ (Fase 4, enmienda A1 del PLAN — 2026-07-14)

Tercera familia, independiente de ambos generadores (evita auto-preferencia). Digest fijado por la
misma razón que arriba (los tags son punteros móviles).

| campo | gemma2:27b |
|---|---|
| **digest (sha256)** | `53261bc9c192c1cb5fcc898dd3aa15da093f5ab6f08e17e48cf838bb1c58abfe` |
| tamaño | 15 628 378 336 B (15.63 GB); footprint cargado 17.30 GB |
| familia | gemma2 · 27.2B · Q4_0 |
| pull | 2026-07-14 (`POST /api/pull`, esta sesión) |
| VRAM | **100% GPU** verificado a `num_ctx=2048` (17.30/17.30 GB) |
| params de scoring | temperature 0 · num_ctx 2048 · JSON estricto de 6 claves, reintentos acotados |

