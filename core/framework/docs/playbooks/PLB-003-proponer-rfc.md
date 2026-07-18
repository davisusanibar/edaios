---
id: PLB-003
tipo: Playbook
titulo: Proponer un cambio (RFC)
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: KO-RFC-PROCESS
---

# PLB-003 — Proponer un cambio (RFC)

## Objetivo
Proponer y discutir un cambio antes de decidirlo.

## Cuándo usarlo
Cuando el cambio afecta la Foundation o es ambiguo y merece deliberación previa al ADR.

## Pasos
1. Usa la plantilla `core/framework/templates/knowledge/rfc.md`.
2. Redacta Motivación, Propuesta, Alternativas e Impacto (capas y KOs afectados).
3. Estado `Propuesto`; recoge comentarios.
4. Si se ratifica, actualiza `governance/RFC_CATALOG.md` y deriva en un ADR
   (PLB-002) cuando exista una decisión estructural que registrar.

## Verificación
El RFC es un KO válido (`edaios validate` sin errores).

## Trazabilidad
Implementa `core/foundation/governance/RFC_PROCESS.md`.

## Historial
- 2026-06-26 — FWK-007: ratificación.
