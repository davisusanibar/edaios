---
id: EDAIOS-HISTORICAL-ARCHIVE-REORGANIZATION
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: governance
trazas:
  - ADR-0001
  - ADR-0002
  - ADR-0007
  - ADR-0014
spec_tipada: specs/archive/010-historical-archive-reorganization/feature.spec.yaml
fuentes:
  - governance/ADR_CATALOG.md
  - .specify/gates.json
value_ledger: "N/A: reorganización de archivo sin outcome institucional"
hipotesis_valor: Una superficie diaria curada reduce carga cognitiva sin eliminar autoridad ni trazabilidad histórica.
---

# Reorganización del archivo histórico

## Requisitos

- **FR-001:** los artefactos históricos se identifican mediante una lista explícita y permanecen recuperables.
- **FR-002:** catálogos, referencias, Spec Kit y gates siguen resolviendo después de la reorganización.
- **FR-003:** la superficie diaria distingue Core vigente de archivo histórico sin borrar decisiones ni evidencia.

## Criterios de éxito

- **SC-001:** cada archivo archivado tiene índice, autoridad, ruta anterior y ruta nueva resolubles.
- **SC-002:** `scripts/test.sh` y `scripts/validate.sh` pasan sin referencias rotas.
- **SC-003:** onboarding enlaza primero la superficie Core y explica cómo consultar el archivo.

## Límites

No se borran ADRs, specs, tests, CI, gobierno ni documentación contractual.

## Clarifications

Revisión del 2026-08-02 al retomar la feature (propuesta el 2026-07-16): sin
ambigüedades bloqueantes del owner. Decisiones técnicas registradas: (a) la
regla de superficie es sostenible, no una lista congelada — en `specs/` viven
solo las features abiertas y la última cerrada; todo cierre anterior se
reubica bajo `specs/archive/` con frontmatter reescrito (patrón SRC-003);
(b) el contrato tipado se eleva a `edaios.sdd.feature/v3`: esta feature cierra
con revisión adversarial materializada como las demás de la serie.

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
