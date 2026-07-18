# Knowledge Patterns

Patrones de conocimiento: soluciones reutilizables (entidad `Pattern`) para representar y organizar Knowledge Objects. Cada patrón implementa la Reference Architecture y es trazable al KOM. No redefinen la Foundation; la aplican.

## Formato de un patrón

Todo patrón declara: **Problema**, **Solución**, **Estructura**, **Aplicabilidad**, **Trazabilidad** y **Ejemplo**.

## Catálogo

| ID | Patrón | Resuelve |
|---|---|---|
| [PAT-001](PAT-001-knowledge-object-front-matter.md) | Knowledge Object Front-Matter | Cómo representar cualquier KO de forma canónica y validable |
| [PAT-002](PAT-002-typed-relation.md) | Typed Relation | Cómo enlazar KOs respetando la Ontología |
| [PAT-003](PAT-003-versioning-supersession.md) | Versioning & Supersession | Cómo evolucionar y reemplazar un KO sin perder historia |
| [PAT-004](PAT-004-derived-representation.md) | Derived Representation | Cómo derivar vistas (humana, IA, Hub) sin duplicar la verdad |
| [PAT-005](PAT-005-specialization.md) | Specialization | Cómo un tipo concreto especializa el esquema del KO |

## Plantillas

Las plantillas que materializan estos patrones están en `core/framework/templates/knowledge/`.
