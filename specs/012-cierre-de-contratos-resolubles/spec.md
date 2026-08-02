---
id: EDAIOS-CIERRE-DE-CONTRATOS-RESOLUBLES
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: ontology
trazas:
  - ADR-0018
  - ADR-0014
  - RFC-0003
spec_tipada: specs/012-cierre-de-contratos-resolubles/feature.spec.yaml
fuentes:
  - core/foundation/ontology/EDAIOS_ONTOLOGY.md
  - core/framework/core/profiles/governance-grammar.json
  - core/framework/core/profiles/control-registry.json
  - tools/validation/kom_gate.py
value_ledger: "N/A: corrección de contratos internos sin outcome institucional propio"
hipotesis_valor: Un dominio de tipos ejecutable y punteros resolubles convierten la ontología de tabla decorativa en contrato verificado y eliminan la clase de fallos fail-open silenciosos.
---

# Cierre de contratos resolubles

RFC-0003 verificó (D1) que KOM-VR-02 es fail-open: el raspado de la ontología
acepta 10 nombres de relaciones como tipos de entidad (SRC-002) y un KO con
`tipo: governs` pasa el gate hoy. Además, la fila `kom` del registro de
controles cita un archivo de tests inexistente en ambas copias (SRC-003) —
contradiciendo el contrato que la feature 009 declaró entregar — y seis KOs de
Foundation citan en prosa archivos que no existen en esta genealogía (SRC-004).
ADR-0018 (Aceptado) habilita el cierre.

## Requisitos

- **FR-001:** el dominio de tipos de entidad que valida KOM-VR-02 proviene del
  contrato ejecutable de la gramática de gobierno, nunca del raspado del
  Markdown; un KO cuyo `tipo` sea un nombre de relación falla cerrado.
- **FR-002:** la correspondencia entre las tablas de la ontología (secciones
  Entidades y Relaciones, SRC-005) y el contrato JSON es bidireccional y por
  sección; cualquier diferencia, en cualquier dirección, falla cerrado.
- **FR-003:** todo control declarado en el registro resuelve `implementation` y
  `tests` a archivos existentes del árbol; un puntero no resoluble falla
  cerrado.
- **FR-004:** la fila `kom` del registro de controles cita, en sus dos copias
  byte-idénticas, el archivo real donde se ejecutan los tests KOM.
- **FR-005:** toda referencia `*.md` citada en las líneas de prosa
  `**Deriva de:**` de los KOs de Foundation resuelve a un archivo del árbol de
  Foundation o está anotada explícitamente como histórica; las referencias
  fantasma vigentes quedan corregidas sin inventar linaje nuevo.

## Criterios de éxito

- **SC-001:** una regresión con KO de `tipo: governs` falla KOM (hoy pasa) y el
  corpus vigente permanece en verde.
- **SC-002:** una regresión con desajuste grammar↔ontología en cada dirección
  (entidad extra o faltante en cualquiera de los dos lados) falla cerrado.
- **SC-003:** una regresión con un control cuyo `tests` no resuelve falla
  CORE-CONFORMANCE; las dos copias corregidas del registro siguen
  byte-idénticas y en verde.
- **SC-004:** una regresión con referencia de prosa no resoluble falla KOM; las
  líneas corregidas del corpus pasan y ninguna referencia anotada como
  histórica resuelve a un archivo vivo.
- **SC-005:** `scripts/test.sh`, `scripts/validate.sh` y los 14 gates pre-push
  permanecen en verde tras el cierre.

## Límites

No se añaden entidades ni relaciones a la ontología (las 28 y 12 vigentes se
conservan); no se modela dominio de ingeniería de datos; no se migra la
gramática a un formato externo (LinkML queda anotado en RFC-0003 como camino
futuro separado); no se decide el sucesor de las referencias históricas cuya
continuidad es ambigua — se anotan, no se inventan.

## Clarifications

Revisión del 2026-08-01: sin ambigüedades bloqueantes del owner. La única
decisión de dominio — el sucesor de `FOUNDATION_STRATEGY.md` — se resuelve sin
inventar: el KO `core/foundation/strategy/README.md` (id `KO-STRATEGY`) es la
estrategia viva del árbol (SRC-006); las referencias sin sucesor claro
(`EDAIOS_FOUNDATION_SPECIFICATION.md`, `FOUNDATION_DOCUMENT_STANDARD.md`) se
anotan como históricas de la genealogía anterior, decisión reversible por el
owner cuando exista sucesor.

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256 `45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86`.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
