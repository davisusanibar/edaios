---
id: EDAIOS-HISTORICAL-ARCHIVE-REORGANIZATION
estado: Propuesto
fase: specified
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: governance
trazas:
  - ADR-0001
  - ADR-0002
  - ADR-0007
  - ADR-0014
spec_tipada: specs/010-historical-archive-reorganization/feature.spec.yaml
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

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256 `d570785b9f2c2d0b8c8c469a1c5d82b3a188b3a4ec8e9c8c9ab0df4f5fb327`.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
