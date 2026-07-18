# ADR-0007 — Catálogos de gobierno como proyecciones compiladas

**Estado:** Aceptado
**Fecha:** 2026-07-16
**Owner:** Principal Architect

## Contexto

`ADR_CATALOG.md` y `RFC_CATALOG.md` son tablas editadas a mano con conteos
escritos literalmente. Con decisiones concurrentes de múltiples iniciativas,
cada alta colisiona en la misma tabla y dos ramas pueden tomar el mismo número
con slugs distintos sin conflicto de merge en Git.

## Decisión

La fuente de verdad son los documentos individuales `governance/ADR-NNNN-*.md`
y `governance/RFC-NNNN-*.md`. Los catálogos pasan a ser proyecciones derivadas
que `tools/publishing/compile_catalogs.py` regenera leyendo únicamente
metadatos explícitos de cabecera (heading canónico, Estado, Fecha, Owner,
resolved_by); nada se infiere. El gate `CATALOG-PROJECTION` verifica con
`--check` que el catálogo comprometido coincide byte a byte con la
recompilación y falla cerrado ante números duplicados, cabeceras no canónicas,
estados fuera del dominio o drift.

## Alternativas

- mantener edición manual con verificación cruzada: conserva la contención y
  la doble captura de un mismo hecho;
- índice central como autoridad: invierte Git-first; la fila no puede mandar
  sobre el documento que resume.

## Consecuencias

Una decisión nueva es un archivo nuevo más una recompilación; la colisión de
números se detecta en el gate, no en el merge. El patrón es el mismo que
`FND-PROJECTION` aplica a la Constitución: una fuente, muchas vistas.

## Evidencia y frontera del claim

El compilador y su gate prueban consistencia local documento↔catálogo. No
prueban la calidad de una decisión ni sustituyen la firma humana que acepta un
ADR.

## Aprobación

Principal Architect · 2026-07-16 · instrucción humana expresa de ejecutar los
pendientes del roadmap multi-iniciativa.
