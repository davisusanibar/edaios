# CURRENT_STATE — Core 3.1.0 baseline day-zero

**Estado:** baseline portable instalado; feature 014 cerrada; feature 010 propuesta en cola
**Versión:** 3.1.0
**Fecha:** 2026-08-01

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
  canónico es `github.com/davisusanibar/edaios`, rama `main` (ADR-0017, que
  enmienda la cláusula de hogar de ADR-0013 y autoriza la superficie de CI
  remota en `.github/workflows/`). La superficie Bitbucket se conserva como
  secundaria mientras el espejo exista.
- La última feature cerrada es
  `specs/014-restricciones-ontologicas-ejecutables` (invariantes tipificados
  como restricciones con enforcement resoluble; ontología v1.1.0 con entidad
  Constraint, ADR-0021). Cierres previos: `specs/013-sdd-status-maquina`,
  `specs/012-cierre-de-contratos-resolubles`,
  `specs/011-ci-remota-y-estado-vigente` y
  `specs/009-core-trust-boundary-hardening`. La feature
  `specs/010-historical-archive-reorganization` está propuesta en cola. El
  handoff conserva baseline 004 y foco activo nulo hasta que el owner
  seleccione el siguiente foco canónico.
- La dirección de programa vigente es RFC-0003: adopciones de gentle-ai y
  práctica multi-agente (en cola: 015 revisión adversarial preparada, 016
  primer consumer real).
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
