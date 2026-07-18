# CURRENT_STATE — Core 3.1.0 baseline day-zero

**Estado:** baseline portable instalado; feature 008 cerrada
**Versión:** 3.1.0
**Fecha:** 2026-07-16

- Foundation y Constitución permanecen sin cambios.
- Core 3.1 añade memoria local no autoritativa, índice derivado, conflictos
  `review-required`, sesiones observacionales, agent setup y adapter Engram
  opcional; Engram no está instalado.
- Un único módulo declarado: `edaios-core`.
- Perfiles `core-release`, `initiative-adoption` y `federation` disponibles como
  contratos acumulativos.
- Ninguna iniciativa, dominio, engine, consumer, producto, plataforma,
  connector, registry, cloud o release público instalado.
- Git conserva la autoridad. ADR-0013 gobierna una genealogía portable cuyo
  único root alcanzable se deriva y verifica en cada clon completo; el hogar
  canónico es `bitbucket.org/data_and_ia/edaiosv`, rama `main`.
- Las features 007 y 008 están cerradas y sus capacidades forman parte del
  baseline. El handoff conserva baseline 004, último cierre previo 007 y 008
  como foco cerrado hasta que una necesidad real seleccione la siguiente
  feature.
- La feature 006 y sus artefactos de release ligados a la genealogía retirada
  dejaron de ser estado operativo; ADR-0012 reemplaza ese cutover concreto.
- `.specify/release.json` v2 declara `status: baseline`, sin candidato activo y
  con `publication: not-claimed`. No existe tag, release, firma o sello
  reclamado.

La evidencia local puede demostrar contratos, schemas, no auto-promoción,
FTS5/fallback, staleness, hash-chain, degradación y setup reversible. No
demuestra un release sellado, Engram operativo, adopción,
runtimes consumidores, datos, identidad/firma externa, operación distribuida,
producción u outcomes.
