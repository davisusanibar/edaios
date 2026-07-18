---
id: PAT-004
tipo: Pattern
titulo: Derived Representation
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: KO-KOM
---

# PAT-004 — Derived Representation

## Problema

Si Markdown, contexto para IA y páginas de hub derivado son cada uno "la verdad", se contradicen.

## Solución

El KO es canónico. Toda otra forma (Markdown legible, `AIContext`, página de `KnowledgeHub`) es una representación derivada que `represents` al KO. Editar una representación no cambia la verdad: se cambia el KO y la representación se regenera.

## Estructura

`KnowledgeObject` (canónico) → N representaciones (`represents`).

## Aplicabilidad

Publicación y consumo de conocimiento en cualquier canal.

## Trazabilidad

Implementa la vista de Representación de la Reference Architecture y la relación `represents`.

## Ejemplo

La misma Constitución se lee como Markdown, se sirve como contexto a un agente y se navega en hub derivado: tres representaciones, un KO.

## Historial

- 2026-06-26 — FWK-004: ratificación del patrón.
