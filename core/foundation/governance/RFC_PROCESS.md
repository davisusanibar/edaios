---
id: KO-RFC-PROCESS
tipo: Standard
titulo: RFC Process
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: core/foundation/governance/GOVERNANCE_MODEL.md
---

# RFC Process

**Capa:** Foundation v1.0 · GOV-001
**Estado:** Ratificado
**Deriva de:** `GOVERNANCE_MODEL.md`

## Qué es un RFC

Un Request for Comments es una propuesta de cambio en discusión, previa a la decisión. Abre la transición `Borrador → Propuesto` de un Knowledge Object.

## Estructura mínima

1. **Título** — `RFC-NNNN — <propuesta>`.
2. **Motivación** — por qué se propone.
3. **Propuesta** — qué se propone cambiar.
4. **Alternativas** — opciones consideradas.
5. **Impacto** — capas y objetos afectados.

## Reglas

- Un RFC aprobado se materializa en un `ADR` (`Decision`).
- Un RFC rechazado se conserva como conocimiento, no se borra.
- Los cambios menores y no estructurales no requieren RFC.

## Estados y mapeo al KOM

Un RFC usa identificador de cuatro dígitos y uno de estos estados:
`Borrador`, `Propuesto`, `Ratificado`, `Rechazado` o `Derogado`. Para el ciclo
de vida común, `Borrador`, `Propuesto` y `Ratificado` conservan su nombre;
`Rechazado` y `Derogado` normalizan a `Derogado`. Un RFC `Ratificado` declara
`resolved_by` hacia uno o más ADR aceptados; el RFC explora y el ADR decide.
