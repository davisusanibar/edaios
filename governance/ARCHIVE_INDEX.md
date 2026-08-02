# Índice de archivo histórico

Este índice reduce la carga cognitiva de la superficie diaria sin borrar
fuentes canónicas. Todo lo listado sigue siendo resoluble desde Git y conserva
autoridad e historial.

## Regla de superficie

En `specs/` viven solo las features abiertas o propuestas y la última cerrada.
Todo cierre anterior vive bajo `specs/archive/` con su frontmatter reescrito a
la ruta nueva (`spec_tipada` y `artifact`). La lista se deriva del estado; no
es una lista congelada (specs/010, FR-001/FR-003).

## Decisiones de proceso archivadas

- ADR-0002: delivery Spec Kit y gates fail-closed.
- ADR-0007: catálogos de gobierno como proyecciones.
- ADR-0008: superficie CLI de consumo.
- ADR-0009: consumo y federación extremo a extremo.
- ADR-0010: release reproducible y cutover.
- ADR-0012: baseline day-zero y genealogía.

## Features archivadas

| Feature | Autoridad | Ruta anterior | Ruta vigente |
|---|---|---|---|
| 001-core-base-initial | ADR-0001 | `specs/001-core-base-initial` | `specs/archive/001-core-base-initial` |
| 002-operating-system-cycle-interactions | ADR-0002 | `specs/002-operating-system-cycle-interactions` | `specs/archive/002-operating-system-cycle-interactions` |
| 003-operating-system-glossary | ADR-0002 | `specs/003-operating-system-glossary` | `specs/archive/003-operating-system-glossary` |
| 004-core-multi-initiative-scale | ADR-0004 | `specs/004-core-multi-initiative-scale` | `specs/archive/004-core-multi-initiative-scale` |
| 005-catalog-projection-and-consumption-cli | ADR-0007 | `specs/005-catalog-projection-and-consumption-cli` | `specs/archive/005-catalog-projection-and-consumption-cli` |
| 006 (retirada) | ADR-0012 | `specs/006-*` | tombstone en `specs/tombstones.json` |
| 007-agent-working-memory-and-derived-index | ADR-0011 | `specs/007-agent-working-memory-and-derived-index` | `specs/archive/007-agent-working-memory-and-derived-index` |
| 008-core-baseline-normalization | ADR-0013 | `specs/008-core-baseline-normalization` | `specs/archive/008-core-baseline-normalization` |
| 009-core-trust-boundary-hardening | ADR-0014 | `specs/009-core-trust-boundary-hardening` | `specs/archive/009-core-trust-boundary-hardening` |
| 010-historical-archive-reorganization | ADR-0014 | `specs/010-historical-archive-reorganization` | `specs/archive/010-historical-archive-reorganization` |
| 011-ci-remota-y-estado-vigente | ADR-0017 | `specs/011-ci-remota-y-estado-vigente` | `specs/archive/011-ci-remota-y-estado-vigente` |
| 012-cierre-de-contratos-resolubles | ADR-0018 | `specs/012-cierre-de-contratos-resolubles` | `specs/archive/012-cierre-de-contratos-resolubles` |
| 013-sdd-status-maquina | ADR-0002 | `specs/013-sdd-status-maquina` | `specs/archive/013-sdd-status-maquina` |
| 014-restricciones-ontologicas-ejecutables | ADR-0021 | `specs/014-restricciones-ontologicas-ejecutables` | `specs/archive/014-restricciones-ontologicas-ejecutables` |
| 015-revision-adversarial-preparada | ADR-0019 | `specs/015-revision-adversarial-preparada` | `specs/archive/015-revision-adversarial-preparada` |
| 016-onboarding-de-consumer-real | ADR-0020 | `specs/016-onboarding-de-consumer-real` | `specs/archive/016-onboarding-de-consumer-real` |

## Regla de mantenimiento

Reubicar exige, en la misma feature gobernada: `git mv`, reescritura de los
dos campos de ruta del frontmatter, fila en esta tabla, y actualización de
handoff, superficie diaria, demo y menciones de gobernanza. Los gates validan
el resultado; una reubicación parcial falla cerrado. Este índice no sustituye
las fuentes ni modifica su autoridad.
