---
id: KO-ONTOLOGY
tipo: Ontology
titulo: EDAIOS Ontology
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: Foundation
---

# Ontología EDAIOS

## Entidades

| Entidad | Significado |
|---|---|
| `Foundation` | autoridad normativa |
| `Core` | materialización reusable de Foundation |
| `Consumer` | módulo que consume contratos públicos de Core |
| `KnowledgeObject` | unidad versionada de conocimiento |
| `ConstitutionArticle` | regla no negociable |
| `ADR` | decisión estructural |
| `RFC` | exploración de alternativas |
| `Feature` | contrato de cambio |
| `Gate` | verificación ejecutable |
| `Evidence` | observación con fuente y alcance |
| `Outcome` | efecto medido con owner y baseline |
| `DerivedView` | representación regenerable, no autoritativa |
| `FutureExtension` | especialización posible, inexistente hasta su promoción |
| `Identity` | identidad normativa de EDAIOS |
| `Manifesto` | compromisos compartidos |
| `Vision` | estado futuro deseado |
| `Mission` | actividad permanente |
| `Value` | criterio de decisión |
| `Principle` | regla orientadora |
| `Philosophy` | tesis y postura fundacional |
| `Strategy` | secuencia de evolución |
| `Constitution` | autoridad constitucional agrupada |
| `Article` | artículo constitucional versionado |
| `Ontology` | vocabulario y relaciones canónicas |
| `Standard` | contrato normativo verificable |
| `Governance` | modelo de autoridad y promoción |
| `Pattern` | solución reusable que materializa Foundation |
| `Playbook` | secuencia operativa gobernada |

## Relaciones

| Relación | Dominio → rango | Regla |
|---|---|---|
| `derives_from` | KO → KO | autoridad igual o superior |
| `governs` | Foundation/Core → KO | nunca se invierte |
| `consumes` | Consumer → Core | sin redefinir Core |
| `implements` | artefacto → spec/ADR | trazabilidad resoluble |
| `verified_by` | claim → gate/evidence | no eleva el scope |
| `decides` | ADR → pregunta | requiere firma |
| `resolves` | ADR → RFC | cierra alternativas |
| `supersedes` | KO → KO | conserva el objeto anterior |
| `projects` | DerivedView → KO | regenerable source-first |
| `references` | KO → KO | referencia resoluble |
| `validates` | Gate → KO | verificación sin autoridad normativa |
| `represents` | DerivedView → KO | exactamente un origen canónico |

## Invariantes

1. Foundation → Core → Consumer nunca se invierte.
2. Un derivado no gobierna su fuente.
3. Evidencia técnica no acepta decisiones ni outcomes.
4. Una extensión futura no existe por estar documentada.
5. Un KO derogado conserva identidad y trazabilidad.

`KO` en las tablas de relaciones es el supertipo de los tipos de conocimiento
enumerados. `Foundation`, `Core` y `Consumer` son capas de autoridad; no son
aliases para IDs de KO.
