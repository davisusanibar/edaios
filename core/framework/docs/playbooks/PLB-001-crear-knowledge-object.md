---
id: PLB-001
tipo: Playbook
titulo: Crear un Knowledge Object
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: KO-KOM
---

# PLB-001 — Crear un Knowledge Object

## Objetivo
Autoría de un KO nuevo, consistente por construcción y validable.

## Cuándo usarlo
Al introducir cualquier conocimiento normativo o de implementación.

## Pasos
1. Elige la plantilla adecuada en `core/framework/templates/knowledge/` (base, article, adr, rfc, pattern).
2. Copia la plantilla a su ubicación de capa correcta y reemplaza los placeholders `<...>`.
3. Completa el front-matter conforme a PAT-001: `id` único, `tipo` de la Ontología, `estado: Borrador`, `autoridad`, `deriva_de` hacia un artefacto de igual o mayor autoridad.
4. Redacta el cuerpo y la sección `Historial`.
5. Ejecuta `./scripts/validate.sh` y corrige hasta `0 errors`.
6. Cuando se ratifique, cambia `estado` a `Ratificado` (ver PLB-003/PLB-002 si requiere RFC/ADR).

## Verificación
`edaios validate` sin errores; el KO aparece descubierto por el validador.

## Trazabilidad
Implementa el KOM y los patrones PAT-001, PAT-002.

## Historial
- 2026-06-26 — FWK-007: ratificación.
