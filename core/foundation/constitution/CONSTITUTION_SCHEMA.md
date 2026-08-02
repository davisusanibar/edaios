---
id: KO-CONSTITUTION-SCHEMA
tipo: Standard
titulo: Constitution Schema
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: Foundation
---

# Constitution Schema

**Capa:** Foundation v1.0
**Estado:** Ratificado (contrato normativo de artículos)
**Actualizado:** 2026-06-26
**Deriva de:** `FOUNDATION_DOCUMENT_STANDARD.md` (histórico, genealogía anterior)

## Objetivo

Definir qué es —y qué debe contener— un artículo constitucional dentro de EDAIOS, de modo que cada artículo sea uniforme, trazable y, en el futuro, representable como Knowledge Object.

## Contrato de un artículo

Todo artículo (`ART-NNN`) debe declarar, en su encabezado, los siguientes campos:

| Campo | Descripción |
|---|---|
| `id` | Identificador `ART-NNN` único y estable. |
| `titulo` | Nombre del artículo. |
| `version` | Versión semántica del artículo (p. ej. `1.0.0`). |
| `estado` | `Borrador`, `Ratificado` o `Derogado`. |
| `tipo` | Siempre `Artículo Constitucional`. |
| `autoridad` | Capa que lo gobierna (`Foundation v1.0`). |
| `deriva_de` | Documento(s) de origen (Strategy u otra fuente preservada). |
| `dependencias` | Artículos o documentos de los que depende. |
| `impacto` | Qué capas o decisiones quedan obligadas por el artículo. |

## Cuerpo de un artículo

Tras el encabezado, el cuerpo sigue el `FOUNDATION_DOCUMENT_STANDARD` adaptado:

1. **Tesis** — la afirmación normativa central.
2. **Desarrollo** — el razonamiento y las reglas.
3. **Representación semántica** — entidades y relaciones de la Ontología que el artículo introduce o restringe (preparación para el KOM; no implementa el KOM).
4. **Lo que este artículo no pretende decir** — límites explícitos.
5. **Historial** — registro de cambios.

## Reglas de gobierno

- Un artículo solo cambia de `estado` o `version` mediante decisión registrada (ADR/RFC).
- Ningún artículo puede contradecir al `PREÁMBULO` ni a `ART-000`.
- La numeración es estable: un artículo derogado no reutiliza su `id`.

## Lo que este schema no pretende decir

- No define el KOM; solo deja un punto de anclaje (`representación semántica`) para cuando exista.
