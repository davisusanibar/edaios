---
id: KO-ONTOLOGY
tipo: Ontology
titulo: EDAIOS Ontology
version: 1.1.0
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
| `Constraint` | restricción tipificada verificable del dominio |

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

Cada restricción es una instancia de `Constraint`: declara su ámbito dentro
del dominio de entidades y el enforcement que la verifica. Una restricción sin
verificador resoluble no existe en esta ontología (ADR-0021).

| Id | Regla | Aplica a | Verificado por |
|---|---|---|---|
| `INV-001` | La cadena de autoridad Foundation → Core → Consumer nunca se invierte. | `Foundation`, `Core`, `Consumer` | `KOM`, `BASELINE-SURFACE` |
| `INV-002` | Un derivado no gobierna su fuente y se regenera desde ella. | `DerivedView` | `FND-PROJECTION`, `CATALOG-PROJECTION`, `AGENT-PARITY`, `CORE-BASE-DEMO` |
| `INV-003` | Evidencia técnica no acepta decisiones ni outcomes. | `Evidence`, `Gate`, `Outcome` | `SDD-CONTRACT`, `TRACEABILITY` |
| `INV-004` | Una extensión futura no existe por estar documentada. | `FutureExtension` | `CLAIM-SURFACE`, `BASELINE-SURFACE` |
| `INV-005` | Un KO derogado conserva identidad y trazabilidad. | `KnowledgeObject` | `KOM`, `TRACEABILITY` |
| `INV-006` | La identidad de un KO es única dentro de su namespace. | `KnowledgeObject` | `KOM-VR-01` |
| `INV-007` | Un KO declara exactamente un tipo y ese tipo pertenece al dominio de entidades. | `KnowledgeObject`, `Ontology` | `KOM-VR-02` |
| `INV-008` | El estado de un KO pertenece al ciclo de vida declarado y sus transiciones al contrato. | `KnowledgeObject` | `KOM-VR-09`, `KOM-VR-10` |
| `INV-009` | Un RFC Ratificado se resuelve por ADR Aceptado. | `RFC`, `ADR` | `TRACEABILITY`, `CATALOG-PROJECTION` |
| `INV-010` | Toda referencia de linaje en prosa resuelve o está anotada como histórica. | `KnowledgeObject` | `DERIVA-PROSA` |
| `INV-011` | Un cambio estructural declara trazas ADR resolubles. | `Feature`, `ADR` | `SDD-CONTRACT` |

`KO` en las tablas de relaciones es el supertipo de los tipos de conocimiento
enumerados. `Foundation`, `Core` y `Consumer` son capas de autoridad; no son
aliases para IDs de KO. Los ámbitos de `Aplica a` y los ids de
`Verificado por` se verifican contra el contrato ejecutable de la gramática de
gobierno; la lista crece por decisión, nunca por documentación.
