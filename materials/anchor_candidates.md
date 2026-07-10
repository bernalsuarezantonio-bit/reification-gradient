# materials/anchor_candidates.md — Candidatos para el ancla real (`real_anchor`)

**Decisión reservada al investigador.** Aquí van TRES candidatos; no elijo el definitivo.
El ancla debe ser un trastorno **real pero poco famoso**, glosado al **mismo grano mínimo** que la
disprosexia narrativa (nombre + una línea de proceso *upstream*, sin síntomas, criterios ni curso).

Criterio de selección (recordatorio del RUNBOOK / PLAN H3):
- Si el modelo la reconoce al instante y la satura, el **techo** pierde resolución → elige la menos
  célebre que aún sea genuinamente real.
- La glosa debe poder copiarse tal cual a `disorders.yaml` sin violar `check_invariants.py`
  (ninguna contiene términos de `forbidden_symptom_terms`). Aun así, **no toco `disorders.yaml`**:
  esto son solo propuestas.

> Las tres glosas evitan a propósito el dominio mnésico/identitario calcado a la DN para no
> confundir "ancla real" con "DN bien escrita"; mantienen, eso sí, el registro de *regulación de
> la experiencia* para que la comparación de techo sea justa.

---

## Candidato A — Paramnesia reduplicativa
**Glosa (1 línea):**
> Trastorno reconocido en el que se altera la ubicación coherente de lugares o personas dentro de
> la experiencia del propio entorno.

- **A favor:** genuinamente oscuro (casi nadie fuera de neuropsicología lo nombra) → techo no
  saturado, buena resolución. Dominio de *monitorización de la realidad*, comparable a la DN sin
  solaparse con ella.
- **En contra:** ligado a daño neurológico; el modelo podría pedir contexto orgánico y bajar la
  tasa base de diagnóstico en viñetas puramente anímicas.
- **Riesgo de reconocimiento:** bajo.

## Candidato B — Síndrome de Ganser
**Glosa (1 línea):**
> Cuadro disociativo reconocido en el que las respuestas de la persona se desvían de forma
> aproximada bajo ciertas condiciones.

- **A favor:** real y reconocido pero muy poco famoso; registro disociativo, cercano al espíritu de
  "regulación alterada bajo carga" sin ser la DN. Glosa naturalmente mínima.
- **En contra:** asociado a contextos forenses/peritaje; el modelo podría arrastrar ese marco.
- **Riesgo de reconocimiento:** bajo-medio.

## Candidato C — Trastorno de despersonalización-desrealización
**Glosa (1 línea):**
> Trastorno reconocido en el que se altera la regulación de la experiencia de sí mismo y del
> entorno bajo ciertas condiciones.

- **A favor:** es el *placeholder* actual en `disorders.yaml`; encaja casi palabra por palabra con
  el grano de la DN (regulación de la experiencia) → la comparación de contenido es la más limpia.
- **En contra:** el **más conocido** de los tres; riesgo real de saturar el techo (H3 pierde
  resolución si el modelo lo clava siempre, en todos los niveles).
- **Riesgo de reconocimiento:** medio-alto.

---

### Resumen para decidir

| Candidato | Oscuridad (↑ mejor) | Comparabilidad de grano con DN | Riesgo de techo saturado |
|---|---|---|---|
| A — Paramnesia reduplicativa | alta | media | bajo |
| B — Síndrome de Ganser | alta | media | bajo |
| C — Despersonalización-desrealización | media | **alta** | **alto** |

**Trade-off central:** C da la comparación de contenido más limpia pero arriesga el techo;
A y B protegen mejor la resolución de H3 a costa de un dominio algo menos calcado al de la DN.
Mi lectura (no vinculante): si priorizas H3, **A**; si priorizas comparabilidad de glosa, **C**.
Tú decides cuál entra en `disorders.yaml`.
