# Registro de fuentes · Feature 017

Observación local fechada el 2026-08-02 sobre el commit `9369b72`.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | `specs/010-historical-archive-reorganization/review/findings.md` (RA-003, RA-005) | 2026-08-02 | Dos endurecimientos anotados como futuros por la revisión adversarial: PIN_LINE solo valida plan.md (una huella de 62 hex vivió en spec.md de la 010 desde su autoría); validate_program_surface solo lee CURRENT_STATE (la contradicción de NEXT_ITERATION escapó dos veces en la sesión) | Anotación sin código es prosa aspiracional — la clase de fila que INV/ADR-0021 prohíbe en la ontología |
| SRC-002 | `tools/validation/spec_kit_gate.py` (PIN_LINE y el check de frescura del plan) | 2026-08-02 | El contrato de pin existe y opera para plan.md; specs 010..017 llevan la misma línea por convención sin validación | El endurecimiento reusa el contrato existente; no inventa formato |
| SRC-003 | `tools/validation/traceability_check.py` (validate_program_surface) | 2026-08-02 | Chequea solo `program-office/context/CURRENT_STATE.md`; NEXT_ITERATION.md declara hoy "está en ejecución" para la 010 ya cerrada — tercer escape de la misma clase, vivo al escribir esta spec | El corpus debe corregirse en esta feature para que la regresión positiva pase |
