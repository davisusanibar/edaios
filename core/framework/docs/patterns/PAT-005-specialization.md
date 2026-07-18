---
id: PAT-005
tipo: Pattern
titulo: Specialization
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: KO-KOM
---

# PAT-005 — Specialization

## Problema

Tipos concretos (un artículo constitucional, un ADR) necesitan campos propios sin romper el contrato común del KO.

## Solución

Especializar el esquema del KO: un tipo declara `tipo` fijo y añade o restringe campos, conformando siempre al esquema base. El `CONSTITUTION_SCHEMA` es la especialización del KO para `tipo: Article`.

## Estructura

Esquema del KO (base) ← esquema especializado (p. ej. Article, ADR).

## Aplicabilidad

Cualquier tipo de la Ontología que requiera un contrato más específico.

## Trazabilidad

Implementa la sección "Article como especialización" del KOM.

## Ejemplo

Un `Article` es un KO con `tipo: Article` y los campos del `CONSTITUTION_SCHEMA`.

## Historial

- 2026-06-26 — FWK-004: ratificación del patrón.
