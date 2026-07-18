---
id: KO-ADR-PROCESS
tipo: Standard
titulo: ADR Process
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: core/foundation/governance/GOVERNANCE_MODEL.md
---

# ADR Process

**Capa:** Foundation v1.0 · GOV-001
**Estado:** Ratificado
**Deriva de:** `GOVERNANCE_MODEL.md`, ART-006

## Qué es un ADR

Un Architecture Decision Record registra una decisión estructural: su contexto, la decisión y sus consecuencias. Es obligatorio para todo cambio arquitectónico (ART-006).

## Estructura mínima

1. **Título** — `ADR-NNNN — <decisión>`.
2. **Estado** — `Propuesto`, `Aceptado` o `Derogado`.
3. **Contexto** — qué problema o presión motiva la decisión.
4. **Decisión** — qué se decide, sin ambigüedad.
5. **Consecuencias** — qué queda obligado o afectado.

## Reglas

- El `id` es estable; un ADR derogado no reutiliza su número.
- Se registra en el ledger correspondiente a su alcance (programa o framework).
- Un ADR puede `supersedes` a otro; el anterior pasa a `Derogado`, no se elimina.
- Ningún ADR puede contradecir la Constitución.

## Mapeo al ciclo de vida KOM

El estado especializado del ADR no crea un segundo ciclo de vida. Para
validación y federación se normaliza así: `Propuesto → Propuesto`,
`Aceptado → Ratificado` y `Derogado → Derogado`. La palabra `Aceptado` conserva
el significado de decisión humana vigente; no puede ser emitida por un gate o
agente.
