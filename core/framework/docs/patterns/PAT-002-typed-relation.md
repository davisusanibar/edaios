---
id: PAT-002
tipo: Pattern
titulo: Typed Relation
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: KO-ONTOLOGY
---

# PAT-002 — Typed Relation

## Problema

Enlazar conocimiento con texto libre ("ver también…") impide razonar sobre dependencias, gobierno o impacto.

## Solución

Expresar cada vínculo entre KOs con una relación tipada de la Ontología (`derives_from`, `governs`, `implements`, `constrains`, `references`, `explains`, `supersedes`, `validates`, `represents`, `publishes`, `consumes`), respetando su dominio → rango.

## Estructura

Una relación apunta al `id` de otro KO existente y declara su tipo. El validador podrá comprobar existencia (KOM-VR-05) y dominio/rango (KOM-VR-06).

## Aplicabilidad

Cualquier dependencia o gobierno entre KOs.

## Trazabilidad

Implementa la sección de Relaciones de la Ontología y prepara las reglas KOM-VR-05/06.

## Ejemplo

`ART-003 derives_from KO-VISION`; `Framework implements Article`.

## Historial

- 2026-06-26 — FWK-004: ratificación del patrón.
