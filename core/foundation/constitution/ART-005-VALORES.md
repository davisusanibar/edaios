---
id: ART-005
tipo: Article
titulo: ART-005 — Valores
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: core/foundation/values/README.md
---

# ART-005 — Valores

| Campo | Valor |
|---|---|
| id | ART-005 |
| titulo | Valores |
| version | 1.0.0 |
| estado | Ratificado |
| tipo | Artículo Constitucional |
| autoridad | Foundation v1.0 |
| deriva_de | Foundation v1.0.0 (STR-001/CNS-001) |
| dependencias | ART-000 |
| impacto | Criterios de decisión exigibles en todas las capas |

## Tesis

> Ante una disyuntiva, EDAIOS elige el lado izquierdo de cada par.

## Desarrollo

1. **Claridad** sobre complejidad accidental.
2. **Conocimiento explícito** sobre conocimiento tribal.
3. **Decisiones trazables** sobre opiniones sueltas.
4. **Arquitectura gobernada** sobre implementación improvisada.
5. **Humanos responsables** sobre automatización ciega.
6. **Evolución versionada** sobre reinvención constante.

Un cambio que viole un valor requiere justificación explícita; si es estructural, requiere ADR.

## Representación semántica

- Entidades: `Value`.
- Relaciones: `constrains`, `governs`.

## Lo que este artículo no pretende decir

- No prohíbe la complejidad necesaria ni la automatización; prohíbe la complejidad accidental y la automatización sin responsabilidad.
