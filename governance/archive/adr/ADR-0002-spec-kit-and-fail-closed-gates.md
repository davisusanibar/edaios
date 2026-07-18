# ADR-0002 — Delivery gobernado por Spec Kit y gates fail-closed

**Estado:** Aceptado
**Fecha:** 2026-07-15
**Owner:** Principal Architect

## Contexto

La velocidad sin contrato desplaza decisiones a código y conversación.

## Decisión

Todo cambio gobernado recorre: constitution → specify → clarify → checklist →
plan → tasks → analyze → implement. La cadena trazable es intención → FR/SC →
plan → tarea → diff → gate → evidencia. Una decisión estructural requiere ADR
aceptado antes de implementar; un RFC se usa solo si hay alternativas abiertas.
Warnings, referencias rotas, claims sin evidencia y gates incompletos bloquean.
La IA prepara y verifica; el owner firma. Commit y push no son implícitos.

## Consecuencias

Cada feature conserva spec tipada, checklist, plan, tareas y evidencia. Ningún
gate reemplaza aceptación humana ni verdad aportada por su owner.

## Evidencia y frontera

Spec Kit y scripts prueban coherencia mecánica; no prueban valor ni producción.

## Aprobación

Principal Architect · 2026-07-15 · instrucción humana de congelar Core Base.
