# Plan técnico · Restricciones ontológicas ejecutables

## Contexto técnico

Los invariantes son prosa (SRC-002) y su verificación real vive dispersa en
gates sin vínculo declarado. El mecanismo bidireccional MD↔JSON ya opera para
entidades y relaciones (SRC-005). El dominio de enforcement disponible son los
15 gates de `.specify/gates.json` más `KOM-VR-01..11` y `DERIVA-PROSA`
(SRC-003). ADR-0021 está Aceptado.

## Decisión de implementación

1. **Ontología (`EDAIOS_ONTOLOGY.md`, versión 1.0.0 → 1.1.0):**
   - fila nueva en Entidades: `Constraint` — restricción tipificada
     verificable del dominio (29 entidades);
   - `## Invariantes` pasa a tabla `| Id | Regla | Aplica a | Verificado por |`
     con los 5 invariantes vigentes tipificados (INV-001..005) y 6
     restricciones de enforcement ya operativo (INV-006..011): unicidad de
     identidad (KOM-VR-01), tipo único en dominio (KOM-VR-02), ciclo de vida y
     transiciones (KOM-VR-09/10), resolución de RFC por ADR aceptado
     (TRACEABILITY, CATALOG-PROJECTION), linaje en prosa resoluble
     (DERIVA-PROSA), cambio estructural con ADR (SDD-CONTRACT). Ámbitos y
     verificadores en backticks para parseo determinista.
2. **Gramática (`governance-grammar.json`):** `entities` += `Constraint`;
   bloque nuevo `constraints`: lista de `{id, aplica_a, verificado_por}`.
3. **Gate (`kom_gate.py`):**
   - `ONTOLOGY_SECTION` admite `Invariantes`; regex de fila de restricción
     captura id `INV-[0-9]{3}` y las celdas de ámbito y verificación (tokens
     backticked);
   - `load_contracts` verifica bidireccionalmente: conjunto de ids MD ==
     conjunto de ids del contrato; por id, ámbito MD == ámbito JSON ⊆
     entidades, y verificadores MD == JSON ⊆ dominio de enforcement (ids de
     `.specify/gates.json` ∪ `KOM-VR-01..11` ∪ `DERIVA-PROSA`); vacíos o
     desconocidos fallan cerrado; `gates.json` ausente falla cerrado.
4. **Regresiones** en `test_governance_conformance.py`
   (ResolvableContractsTests): enforcer desconocido falla; ámbito fuera de
   entidades falla; id solo-MD y solo-grammar fallan; KO `tipo: Constraint`
   pasa VR-02; corpus verde.
5. **Colaterales conocidos:** si FND-PROJECTION detecta drift tras editar el
   KO (la ontología no es fuente de la constitución, no se espera), se
   recompila y propaga el pin (rutina de specs/012). Renumeración de la cola
   del programa: revisión adversarial → 015, consumer real → 016
   (CURRENT_STATE, NEXT_ITERATION y Plan de evidencia de RFC-0003).

## Alternativas descartadas

- OWL/RDFS con razonador: runtime y dependencias fuera del contrato stdlib
  (ADR-0021);
- restricciones solo en el JSON sin tabla MD: invierte la autoridad
  (el MD normativo dejaría de declarar sus propias reglas);
- validar enforcement contra una lista congelada en el gate: duplicaría
  `.specify/gates.json`; la resolución dinámica acopla a propósito.

## Estructura afectada

```text
core/foundation/ontology/EDAIOS_ONTOLOGY.md        (v1.1.0: entidad + tabla)
core/framework/core/profiles/governance-grammar.json (entities + constraints)
tools/validation/kom_gate.py                        (sección + verificación)
core/framework/tests/test_governance_conformance.py (regresiones)
governance/RFC-0003-*.md · program-office/context/  (renumeración de cola)
specs/014-restricciones-ontologicas-ejecutables/    (artefactos)
```

## Estrategia de pruebas

Regresiones negativas por contrato nuevo, positiva del corpus, suites
completas y 14 gates (SC-001..004).

## Despliegue y reversa

Push por la superficie CI vigente. Reversa: commit que restaura ontología,
gramática y gate; no se reescribe `main`.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | ADR-0021 y la ontología preceden al código; el MD conserva autoridad. |
| II. Spec antes que artefacto | PASS | spec, checklist y plan existen antes de tocar fuente alguna. |
| III. El canon crece por decisión | PASS | ADR-0021 Aceptado con orden expresa del owner habilita la entidad y la sección. |
| IV. Cero cifras sin fuente | PASS | 5 invariantes, dominio de enforcement y recomendaciones con fila SRC fechada. |
| V. Una fuente, muchas vistas | PASS | Tabla MD autoritativa + contrato JSON verificado bidireccionalmente. |
| VI. La IA consume; el humano firma | PASS | Solo restricciones con enforcement existente; nada aspiracional; el owner firmó la dirección. |
| VII. Privacidad por diseño | PASS | T0; sin datos personales ni ruta LLM. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `KOM`: cambio principal — sección nueva del contrato bidireccional.
- `TEST`: regresiones nuevas.
- `TRACEABILITY`, `CATALOG-PROJECTION`: ADR-0021 ya proyectado; sin cambio de
  contrato.
- `FND-PROJECTION`: sin drift esperado (la ontología no es fuente de la
  constitución); rutina de recompilación disponible si aparece.
- Resto de gates: sin cambio; deben permanecer verdes.

## Impactos

- **Arquitectura:** ninguna pieza nueva de runtime.
- **Ontología:** +1 entidad (`Constraint`), sección Invariantes tipificada;
  12 relaciones intactas; cambio aditivo 1.1.0 decidido por ADR-0021.
- **Datos/privacidad:** T0.
- **IA:** sin ruta LLM; el validador sigue fuera del modelo (tesis
  neurosimbólica ya vigente).
- **Costo:** parseo adicional despreciable en KOM.
- **Blast radius:** ontología, gramática, un gate, tests y prosa de programa.
