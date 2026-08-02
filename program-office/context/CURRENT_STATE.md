# CURRENT_STATE — Core 3.1.0 baseline day-zero

**Estado:** baseline portable instalado; feature 017 cerrada; programa sin foco activo
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
- La última feature cerrada es `specs/017-endurecimientos-de-revision`
  (contrato de pin también en specs y superficie diaria doble: cada escape
  encontrado por la revisión adversarial muere como clase). Cierre previo:
  `specs/archive/010-historical-archive-reorganization` (superficie curada
  con índice viejo→nuevo en `governance/ARCHIVE_INDEX.md`). El handoff conserva
  baseline 004 y foco activo nulo hasta que el owner seleccione el siguiente
  foco canónico.
- La dirección RFC-0003 (adopciones gentle-ai y práctica multi-agente) está
  RATIFICADA y ejecutada: sus seis features cerraron con evidencia remota. El
  Value Ledger tiene su primera entrada (VL-001, en observación). Pendientes
  de decisión del owner: vendor update de Spec Kit 0.12.11→0.15.x y receipts
  in-toto (RFC-0003, Recomendación).
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
