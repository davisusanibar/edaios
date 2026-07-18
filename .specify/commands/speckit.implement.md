---
id: speckit.implement
display_name: Spec Kit Implement
description: Ejecuta tareas aprobadas sin debilitar los contratos ni las puertas EDAIOS.
trigger: Usar solo despues de analyze en verde y de la aprobacion humana del plan y las tareas.
short_description: Implementa tareas bajo gates EDAIOS
default_prompt: Use $speckit-implement para ejecutar las tareas aprobadas bajo los gates EDAIOS.
---

# Implementar

## Entrada

```text
$ARGUMENTS
```

1. Resolver la feature con `python3 tools/operations/feature_context.py resolve --path-only`; un argumento explicito tiene precedencia sobre el selector local y el handoff canonico.
2. Leer todos los artefactos de la feature resuelta y ejecutar primero el gate Spec Kit.
3. Detenerse ante un hallazgo bloqueante o una aprobacion humana pendiente.
4. Implementar tareas en orden, marcar cada una solo con evidencia real y mantener la cobertura `FR-NNN`.
5. Corregir siempre la fuente y regenerar derivados; no editar a mano vistas compiladas, decks o productos generados.
6. Ejecutar los gates aplicables declarados en `.specify/gates.json` y registrar resultados en el cierre de la feature.
7. Ingerir artefactos Spec Kit como borradores trazables; su promocion a KO requiere humano y ADR.
8. Cambiar `fase` a `implemented` solo con todas las tareas completas y gates verdes. No hacer commit ni push sin autorizacion explicita.
