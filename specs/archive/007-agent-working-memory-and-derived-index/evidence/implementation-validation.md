# Evidencia importada al baseline · memoria operativa e índice derivado

Fecha de observación: **2026-07-16**

Scope: capacidades de feature 007 incorporadas al baseline portable Core 3.1.0;
T0 local, sin instalar Engram, sin sync remoto, tag, publicación o release
reclamada. ADR-0013 deriva el único root desde Git y evita copiar identidades de
otra genealogía dentro del snapshot.

| Control | Resultado | Evidencia observada |
|---|---|---|
| Contrato Spec Kit | PASS | Feature cerrada, ADR-0011 aceptado, requisitos y tareas cubiertos. |
| Estructura | PASS | Un módulo Core; ningún runtime, dominio, consumer, producto o iniciativa instalado. |
| Memoria | PASS | Records content-addressed, sensibilidad explícita, conflictos `review-required` y ausencia de operación de promoción. |
| Índice | PASS | FTS5/fallback, digest de corpus, staleness e integridad de filas/FTS fail-closed. |
| Sesiones | PASS | Cadena de digests, terminal anti-truncamiento y summaries observacionales. |
| Adapter | PASS | Engram opcional, loopback, versión API separada, redirects bloqueados y degradación segura. |
| Agent setup | PASS | Plan/apply/verify/rollback project-local, idempotente y ligado a receipt/target/backup. |
| Distribución | PASS | La superficie forma parte del wheel y export Core reproducibles. |

## Capacidades demostradas

- working memory local no autoritativa y reconstruible;
- búsqueda derivada con canal canónico por defecto;
- candidatos de conflicto sin winner automático;
- sesiones hash-chained cuyos resúmenes permanecen `unverified`;
- adapter opcional sin operaciones de gobierno;
- setup reversible y drafts con revisiones preservadas.

## Límite de la evidencia

Esta evidencia respalda la presencia y las fronteras técnicas de la capacidad en
el baseline. No es EvidenceReceipt firmado ni release seal. No demuestra Engram
instalado u operativo, sync, T2/T3, rendimiento, adopción, producción u
outcomes. ADR-0013 separa expresamente el baseline portable de cualquier
candidato o publicación futura.
