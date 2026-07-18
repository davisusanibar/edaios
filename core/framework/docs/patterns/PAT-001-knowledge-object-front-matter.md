---
id: PAT-001
tipo: Pattern
titulo: Knowledge Object Front-Matter
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: KO-KOM
---

# PAT-001 — Knowledge Object Front-Matter

## Problema

Un documento sin metadatos estructurados no puede validarse ni relacionarse de forma fiable. Cada autor describiría los mismos campos de forma distinta.

## Solución

Representar cada Knowledge Object como Markdown con un bloque de front-matter al inicio, conforme al esquema del KOM. El front-matter es la capa legible por máquina; el cuerpo, la legible por humanos.

## Estructura

Campos obligatorios: `id`, `tipo`, `titulo`, `version`, `estado`, `autoridad`, `idioma`, `owner`. Opcionales: `deriva_de`, `relaciones`, `impacto`, `representaciones`.

## Aplicabilidad

Todo KO normativo de la Foundation. Recomendado para KOs de implementación del Framework.

## Trazabilidad

Implementa el esquema del KOM y lo hace verificable mediante las reglas KOM-VR-01..04.

## Ejemplo

```text
id: ART-006
tipo: Article
estado: Ratificado
autoridad: Foundation
```

## Historial

- 2026-06-26 — FWK-004: ratificación del patrón.
