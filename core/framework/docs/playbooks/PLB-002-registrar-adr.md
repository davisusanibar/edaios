---
id: PLB-002
tipo: Playbook
titulo: Registrar un ADR
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: KO-ADR-PROCESS
---

# PLB-002 — Registrar un ADR

## Objetivo
Documentar una decisión arquitectónica de forma trazable.

## Cuándo usarlo
Ante cualquier cambio estructural: capas, fuente de verdad, esquema, validador.

## Pasos
1. Usa la plantilla `core/framework/templates/knowledge/adr.md`.
2. Asigna el siguiente número libre del ledger correspondiente (programa o Framework); no reutilices números.
3. Redacta Contexto, Decisión y Consecuencias. Si supersede a otro ADR, decláralo.
4. Estado inicial `Propuesto`; al aceptarse, `Aceptado`.
5. Añade la fila a `governance/ADR_CATALOG.md`.
6. Ejecuta `./scripts/validate.sh` (comprueba unicidad de IDs).

## Verificación
Sin `ADR_DUPLICATE_ID`; el ADR figura en el catálogo.

## Trazabilidad
Implementa `core/foundation/governance/ADR_PROCESS.md`.

## Historial
- 2026-06-26 — FWK-007: ratificación.
