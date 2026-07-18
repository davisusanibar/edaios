# Changelog

## 3.1.0 — 2026-07-16 · baseline day-zero

- MemoryProvider vendor-neutral y `LocalWorkingMemory` bajo `.edaios/`.
- Índice derivado con FTS5/fallback, digests y staleness fail-closed.
- Conflict candidates `review-required` sin winner automático.
- Sesiones hash-chained y summaries observacionales ligados a receipts.
- `agent-setup` project-local con plan/apply/verify/rollback.
- Adapter Engram v1.19.0 opcional, loopback y degradable.
- Cinco schemas y pruebas adversariales nuevas.
- Separación explícita entre release Engram 1.19.0 y API health 0.1.0, con
  redirects bloqueados antes de transmitir payload o token.
- Integridad de filas/FTS, terminal anti-truncamiento de sesiones, conflictos
  recalculados desde drafts y rollback ligado a surface/target/backup.
- Kernel multi-iniciativa con perfiles acumulativos, receipts v2 y mounts
  explícitos con revalidación de autoridad y corpus.
- CLI de consumo con envelope contractual, readers fail-closed y catálogos
  compilados.
- Wheel y export Foundation + Core reproducibles, con checksum, SBOM y
  provenance local.
- Estado de release separado: baseline instalado sin candidato ni publicación;
  releases futuras requieren manifest y contratos explícitos.

Esta entrada describe el baseline acumulado de la nueva genealogía. Las
versiones usadas durante su construcción no constituyen releases remotas
vigentes ni aportan por sí mismas evidencia de adopción o producción.
