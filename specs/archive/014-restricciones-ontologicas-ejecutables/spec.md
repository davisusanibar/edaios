---
id: EDAIOS-RESTRICCIONES-ONTOLOGICAS-EJECUTABLES
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: ontology
trazas:
  - ADR-0021
  - ADR-0018
  - RFC-0003
spec_tipada: specs/archive/014-restricciones-ontologicas-ejecutables/feature.spec.yaml
fuentes:
  - core/foundation/ontology/EDAIOS_ONTOLOGY.md
  - core/framework/core/profiles/governance-grammar.json
  - .specify/gates.json
  - tools/validation/kom_gate.py
value_ledger: "N/A: tipificación de contratos internos sin outcome institucional propio"
hipotesis_valor: Una restricción declarada junto a su verificador convierte los invariantes de prosa aspiracional en lógica verificada y hace imposible retirar el enforcement sin romper el gate.
---

# Restricciones ontológicas ejecutables

La sección `## Invariantes` de la ontología es una lista de prosa numerada sin
tipo, ámbito ni enforcement declarado (SRC-002). ADR-0021 (Aceptado, por orden
expresa del owner sobre las recomendaciones de la charla de F. Coyle, SRC-004)
decide materializarla: entidad `Constraint`, tabla tipada `INV-NNN` con
`aplica_a` y `verificado_por` resolubles, y el contrato bidireccional de
ADR-0018 extendido a la sección.

## Requisitos

- **FR-001:** la ontología declara la entidad `Constraint` y su sección de
  invariantes es una tabla tipificada donde cada fila tiene id `INV-NNN`,
  regla, ámbito (`aplica_a` ⊆ dominio de entidades) y enforcement
  (`verificado_por`).
- **FR-002:** la gramática de gobierno lleva las restricciones como datos
  (`constraints`) y el gate KOM verifica correspondencia bidireccional por
  sección entre la tabla y el contrato: ids, ámbitos y enforcers; cualquier
  diferencia falla cerrado.
- **FR-003:** el dominio de `verificado_por` son los ids de gates de
  `.specify/gates.json` más las reglas `KOM-VR-01..11` y `DERIVA-PROSA`; una
  restricción con enforcement vacío o no resoluble falla cerrado.
- **FR-004:** solo se materializan restricciones con enforcement ya operativo:
  los cinco invariantes vigentes tipificados más restricciones que documentan
  verificación existente (unicidad, ciclo de vida, tipo único, resolución de
  RFC, linaje, cambio estructural con ADR); ninguna fila aspiracional.

## Criterios de éxito

- **SC-001:** regresión: restricción con enforcer desconocido o vacío falla
  cerrado; ámbito fuera del dominio de entidades falla cerrado.
- **SC-002:** regresión: desajuste de ids, ámbitos o enforcers entre tabla y
  contrato falla en ambas direcciones; el corpus vigente pasa.
- **SC-003:** un KO con `tipo: Constraint` es válido para KOM-VR-02 y la
  ontología versiona 1.1.0 con estado Ratificado conservado.
- **SC-004:** `scripts/test.sh`, `scripts/validate.sh` y los 14 gates
  pre-push permanecen en verde.

## Límites

No se migra a RDFS/OWL ni se añade razonador (sin runtime, stdlib); las
restricciones cubren el dominio de gobierno, no dominios de datos de
consumidores; no se declaran restricciones sin verificador existente; las
relaciones (12) no cambian.

## Clarifications

Revisión del 2026-08-02: sin ambigüedades bloqueantes — el owner ordenó
expresamente la materialización y ADR-0021 fija mecanismo y límites. Decisión
técnica registrada: el dominio de enforcement se resuelve dinámicamente contra
`.specify/gates.json` para que retirar un gate con restricciones a cargo rompa
el gate KOM (acoplamiento deliberado).

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256 `45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86`.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
