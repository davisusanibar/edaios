---
id: ART-008
tipo: Article
titulo: ART-008 — Glosario
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: core/foundation/ontology/EDAIOS_ONTOLOGY.md
---

# ART-008 — Glosario

| Campo | Valor |
|---|---|
| id | ART-008 |
| titulo | Glosario |
| version | 1.0.0 |
| estado | Ratificado |
| tipo | Artículo Constitucional |
| autoridad | Foundation v1.0 |
| deriva_de | Foundation v1.0.0 (STR-001/CNS-001) |
| dependencias | ART-000 a ART-007; Ontología (ONT-001) |
| impacto | Fija el vocabulario común de la Constitución |

## Tesis

> El conocimiento compartido exige un vocabulario compartido.

## Desarrollo

Definiciones oficiales de los términos usados en la Constitución. Este glosario es la vista resumida del vocabulario; la fuente normativa completa de entidades y relaciones es la **Ontología** (`core/foundation/ontology/EDAIOS_ONTOLOGY.md`), que prevalece sobre este glosario en caso de discrepancia.

| Término | Definición |
|---|---|
| **Foundation** | Capa normativa que define identidad, estrategia, filosofía, Constitución, Ontología, KOM y reglas. Gobierna a todas las demás capas. |
| **Framework** | Implementación de la Foundation mediante patrones, arquitectura, templates, playbooks, ADRs y validaciones. |
| **Consumer** | Capa que publica, indexa, gobierna y permite consumir el conocimiento (Knowledge Repository + Knowledge Hub). |
| **Consumidores derivados** | SDK, CLI, una vista derivada, plugins, APIs, MCP y agentes IA. Consumen; no definen. |
| **Constitución** | Autoridad máxima de la Foundation; conjunto de artículos ratificados. |
| **Artículo** | Unidad normativa `ART-NNN` conforme al `CONSTITUTION_SCHEMA`. |
| **Knowledge Object** | Unidad canónica de conocimiento; futura fuente de verdad sobre la que las representaciones (Markdown, README, contexto IA) derivan. |
| **Knowledge First** | Paradigma en el que el conocimiento es el producto principal y el software su consecuencia. |
| **ADR** | Registro de decisión arquitectónica; requisito para todo cambio estructural. |
| **AI Context** | Representación del conocimiento preparada para ser consumida por agentes de IA. |
| **Knowledge Hub** | Exposición navegable del conocimiento (una vista derivada). No es la fuente de verdad; Git lo es. |

## Representación semántica

- Entidades: `GlossaryTerm`, definidas en la Ontología.
- Relaciones: `references`, `derives_from` (este artículo `derives_from` la Ontología).

## Lo que este artículo no pretende decir

- No reemplaza a la Ontología; es su vista resumida y se subordina a ella.
