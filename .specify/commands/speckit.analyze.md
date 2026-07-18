---
id: speckit.analyze
display_name: Spec Kit Analyze
description: Analiza sin modificar la coherencia, cobertura y cumplimiento constitucional de los artefactos SDD.
trigger: Usar despues de tasks y antes de implement para detectar requisitos sin cobertura, tareas huerfanas y conflictos de gobierno.
short_description: Analiza coherencia antes de implementar
default_prompt: Use $speckit-analyze para verificar coherencia y cobertura antes de implementar.
---

# Analizar

## Entrada

```text
$ARGUMENTS
```

1. Resolver la feature con `python3 tools/operations/feature_context.py resolve --path-only`; un argumento explicito tiene precedencia sobre el selector local y el handoff canonico.
2. Operar en modo estrictamente solo lectura sobre spec, contrato tipado, checklist, plan y tasks.
3. Ejecutar `python3 tools/validation/spec_kit_gate.py . --feature <carpeta-resuelta>`.
4. Reportar conflictos constitucionales, ambiguedades, duplicados, requisitos sin tareas, tareas sin requisito, referencias rotas y gates ausentes.
5. Clasificar hallazgos como `CRITICAL`, `HIGH`, `MEDIUM` o `LOW` y citar archivo/seccion.
6. Bloquear implementacion con cualquier `CRITICAL`, `HIGH` o gate rojo; proponer correcciones sin aplicarlas automaticamente.
