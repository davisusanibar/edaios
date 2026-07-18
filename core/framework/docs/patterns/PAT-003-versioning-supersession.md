---
id: PAT-003
tipo: Pattern
titulo: Versioning and Supersession
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: KO-KOM
---

# PAT-003 — Versioning & Supersession

## Problema

El conocimiento evoluciona. Sobrescribir sin rastro pierde el porqué; reemplazar sin marcar deja dos verdades activas.

## Solución

Versionar cada KO semánticamente. Una revisión incrementa `version`. Un reemplazo crea un KO nuevo que `supersedes` al anterior, que pasa a `estado: Derogado` conservando su `id`. Toda transición estructural se registra con un ADR.

## Estructura

`id` estable + `version` semántica + transición de `estado` gobernada.

## Aplicabilidad

Toda evolución de un KO ratificado.

## Trazabilidad

Implementa el ciclo de vida del KOM y el modelo de gobierno (ADR/RFC).

## Ejemplo

`ADR-0003 supersedes` a una decisión previa; el KO anterior queda `Derogado`, no se borra.

## Historial

- 2026-06-26 — FWK-004: ratificación del patrón.
