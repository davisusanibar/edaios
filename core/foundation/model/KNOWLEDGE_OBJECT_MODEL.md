---
id: KO-KOM
tipo: Standard
titulo: Knowledge Object Model (KOM)
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: core/foundation/ontology/EDAIOS_ONTOLOGY.md
---

# Knowledge Object Model (KOM)

**Capa:** Foundation v1.0
**Estado:** Ratificado (modelo canónico v1.0.0)
**Idioma oficial:** Español
**Actualizado:** 2026-06-26
**Deriva de:** `core/foundation/ontology/EDAIOS_ONTOLOGY.md`, Constitución (`core/foundation/constitution/`)

## Resumen ejecutivo

El Knowledge Object Model define el **modelo canónico** con el que EDAIOS representa el conocimiento. Convierte las entidades y relaciones de la Ontología en **Knowledge Objects** con metadatos, ciclo de vida y reglas de validación. El KOM hace operable la Ontología.

## Contexto y problema

La Ontología dice *qué cosas existen*; pero mientras el conocimiento viva solo como documentos sueltos, cada documento compite por ser la fuente de verdad y la consistencia no es verificable. Se necesita una unidad canónica única y un contrato uniforme.

## Tesis

> Ningún documento es la fuente de verdad por sí solo. La fuente de verdad es el **Knowledge Object**; Markdown, README, contexto para IA y páginas de una vista derivada son representaciones derivadas de él.

## 1. El Knowledge Object

Un **Knowledge Object (KO)** es la unidad canónica de conocimiento. Todo concepto definido en la Ontología se materializa como un KO. Cada KO declara un contrato uniforme de metadatos.

### 1.1 Esquema canónico (metadatos obligatorios y opcionales)

| Campo | Obligatorio | Descripción |
|---|---|---|
| `id` | Sí | Identificador único y estable en todo el repositorio. |
| `tipo` | Sí | Una entidad de la Ontología (`Article`, `Principle`, `ADR`, `Pattern`, …). |
| `titulo` | Sí | Nombre del objeto. |
| `version` | Sí | Versión semántica (`MAJOR.MINOR.PATCH`). |
| `estado` | Sí | Estado del ciclo de vida (ver §2). |
| `autoridad` | Sí | Capa que lo gobierna (`Foundation`, `Framework`, `Consumer`). |
| `idioma` | Sí | `es` por defecto para conocimiento normativo. |
| `owner` | Sí | Responsable del objeto. |
| `deriva_de` | Sí (salvo raíz) | KO de origen normativo (relación `derives_from`). |
| `relaciones` | No | Relaciones tipadas hacia otros KO (ver §3). |
| `impacto` | No | Qué capas o decisiones quedan obligadas. |
| `representaciones` | No | Renderizaciones derivadas (Markdown, AIContext, página de Hub). |
| `historial` | Sí | Registro de cambios; en la representación Markdown canónica lo materializa Git para la ruta del KO. |
| `cuerpo` | Sí | Contenido narrativo no vacío después del front matter. |

En la representación Markdown de referencia, `historial` y `cuerpo` son
propiedades verificables aunque no se repitan como claves de front matter:
Git conserva el historial de la ruta y el cuerpo es el contenido posterior al
cierre `---`. Antes del primer commit, el cambio pendiente pertenece al
historial que se está promoviendo y no constituye por sí mismo evidencia
ratificada.

`deriva_de` usa preferentemente el `id` estable. Una ruta solo es válida como
referencia de representación cuando existe dentro del scope declarado, contiene
exactamente un KO y se normaliza a su `id`; una ruta rota o ambigua falla
cerrado. `Foundation` es el único sentinel de raíz permitido y no representa
una relación hacia un KO inexistente.

### 1.2 El `Article` como especialización

El `CONSTITUTION_SCHEMA` es una especialización de este esquema: un artículo constitucional es un KO con `tipo: Article`. Sus campos (`id`, `titulo`, `version`, `estado`, `tipo`, `autoridad`, `deriva_de`, `dependencias`, `impacto`) conforman al contrato del KO. La Constitución es, por tanto, un conjunto de Knowledge Objects de tipo `Article`.

## 2. Ciclo de vida

Todo KO transita por estados gobernados:

```text
Borrador → Propuesto → Ratificado → Derogado
```

| Estado | Significado |
|---|---|
| `Borrador` | En redacción; sin autoridad normativa. |
| `Propuesto` | Sometido a revisión (RFC). |
| `Ratificado` | Vigente y normativo. |
| `Derogado` | Reemplazado; conserva su `id`, no se reutiliza. |

Transiciones válidas: `Borrador→Propuesto→Ratificado`; `Ratificado→Derogado` únicamente mediante un KO que lo `supersedes`. Toda transición estructural exige un `ADR` o `RFC` (`derives_from`).

Los tipos especializados normalizan al ciclo común sin reescribir su fuente:
un ADR `Aceptado` y una feature `Cerrado` equivalen a `Ratificado`; un RFC
`Rechazado` equivale a `Derogado`. El mapeo completo y las expresiones regulares
de identidad se publican en la gramática ejecutable de Core, que debe coincidir
con este contrato.

## 3. Relaciones tipadas

Las relaciones de un KO son exactamente las definidas por la Ontología, con su dominio → rango:

`derives_from`, `governs`, `consumes`, `implements`, `verified_by`, `decides`,
`resolves`, `supersedes`, `projects`, `references`, `validates`, `represents`.

Cada relación apunta al `id` de otro KO existente y debe respetar el dominio y rango declarados en la Ontología.

## 4. Representaciones

El KO es canónico; sus representaciones son derivadas y nunca autoritativas:

- **Markdown / README** — representación legible por humanos (representación v1.0.0 por defecto).
- **AIContext** — representación para agentes de IA.
- **Página de KnowledgeHub** — representación navegable (una vista derivada).

Toda representación `represents` exactamente un KO. El Markdown canónico
representa implícitamente al único `id` de su front matter; las vistas derivadas
declaran `represents` de forma explícita. Editar una representación no cambia la
verdad; cambia el KO y la representación se regenera.

### 4.1 Representación de referencia (v1.0.0)

En v1.0.0 un KO se representa como un documento Markdown con un bloque de metadatos al inicio. De forma ilustrativa (agnóstica de tecnología):

```text
id: ART-006
tipo: Article
titulo: Principios
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: core/foundation/principles/README.md
```

## 5. Reglas de validación (normativas)

El KOM define las reglas que `edaios validate` deberá comprobar (su implementación es VAL-004, en el Framework):

| Regla | Comprobación |
|---|---|
| KOM-VR-01 | `id` único en todo el repositorio. |
| KOM-VR-02 | `tipo` pertenece a las entidades de la Ontología. |
| KOM-VR-03 | Metadatos obligatorios presentes (`id`, `tipo`, `titulo`, `version`, `estado`, `autoridad`, `idioma`, `owner`, `historial`, `cuerpo`). |
| KOM-VR-04 | `estado` ∈ {`Borrador`, `Propuesto`, `Ratificado`, `Derogado`}. |
| KOM-VR-05 | Cada relación apunta a un `id` de KO existente. |
| KOM-VR-06 | Cada relación respeta el dominio → rango de la Ontología. |
| KOM-VR-07 | `deriva_de` apunta a un KO de autoridad igual o mayor (no inversión de dependencia). |
| KOM-VR-08 | Ningún KO de Core/Consumer `governs` a uno de Foundation. |
| KOM-VR-09 | Toda `Decision` estructural tiene un `ADR` asociado. |
| KOM-VR-10 | Las transiciones de `estado` son válidas. |
| KOM-VR-11 | Cada representación `represents` exactamente un KO. |

## 6. Consecuencias arquitectónicas

- El conocimiento deja de depender de documentos individuales; depende de objetos con contrato.
- La consistencia (trazabilidad, no inversión, ciclo de vida) se vuelve verificable por máquina.
- La Consumer podrá publicar Knowledge Objects; los consumidores derivados podrán consumirlos vía `SDKContract`.

## Lo que este modelo no pretende decir

- No implementa el validador (eso es VAL-004, en el Framework).
- No define el almacenamiento ni el pipeline de publicación (eso es la Consumer).
- No fija un formato propietario: Markdown con metadatos es la representación de referencia, no una atadura tecnológica.

## Preguntas abiertas

- ¿`AIContext` se modela como KO propio o solo como representación derivada?
- ¿Qué campos del esquema se vuelven obligatorios para tipos no normativos (`Example`, `Template`)?
