---
id: speckit.checklist
display_name: Spec Kit Checklist
description: Genera y evalua una lista de calidad para la especificacion activa.
trigger: Usar despues de aclarar requisitos y antes del plan para comprobar completitud, testabilidad y gobierno.
short_description: Genera controles de calidad de requisitos
default_prompt: Use $speckit-checklist para generar una lista de calidad de la especificacion activa.
---

# Checklist de requisitos

## Entrada

```text
$ARGUMENTS
```

1. Resolver la feature con `python3 tools/operations/feature_context.py resolve --path-only`; un argumento explicito tiene precedencia sobre el selector local y el handoff canonico.
2. Leer `spec.md`, `feature.spec.yaml` y la Constitucion de la feature resuelta.
3. Crear o actualizar `checklists/requirements.md`.
4. Evaluar, no solo enumerar: alcance acotado, requisitos testables, criterios medibles, trazas resolubles, owner, valor, fuentes, sensibilidad y ausencia de detalles de implementacion.
5. Regla IV: verificar que toda cifra citada por la especificacion tenga fila en el registro de fuentes (`fuentes-estado-del-arte.md`) con rotulo y fecha; una cifra sin fuente es un item critico pendiente.
6. Dejar sin marcar todo incumplimiento y explicar la correccion necesaria.
7. No permitir plan mientras exista un item critico pendiente.
