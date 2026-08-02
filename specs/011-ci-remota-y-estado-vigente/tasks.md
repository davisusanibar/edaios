# Tareas · Feature 011

- [x] [T001] [FR-001] [SC-001] [INGEST] Registrar la aceptación del alcance por el owner (plan de evolución aprobado y orden de continuar, SRC-001).
- [x] [T002] [FR-004] [SC-002] Implementar el check de frescura de superficie diaria en `tools/validation/traceability_check.py` (handoff canónico + VERSION + estados de features). Evidencia: `validate_program_surface` detectó la contradicción real (008 vs 009) antes del refresh.
- [x] [T003] [FR-004] [SC-002] Añadir regresión en `core/framework/tests/`: fixture con superficie obsoleta falla el check; corpus vigente pasa. Evidencia: `core/framework/tests/test_program_surface.py`, 5 casos OK.
- [x] [T004] [FR-005] [SC-002] Actualizar `program-office/context/CURRENT_STATE.md` y `program-office/context/NEXT_ITERATION.md` a la genealogía y hogar reales (009 cerrada, 010 propuesta, GitHub por ADR-0017, dirección RFC-0003).
- [x] [T005] [FR-001] [FR-002] [SC-001] Crear `.github/workflows/ci.yml`: job `gates` con matriz Python 3.11/3.12/3.13, checkout pineado con `fetch-depth: 0`, paso de integridad `GITHUB_SHA == git rev-parse HEAD` y ejecución de `./scripts/ci.sh`. Evidencia local; el run remoto queda en T008.
- [x] [T006] [FR-003] [SC-004] Añadir job `pr-size` informativo al workflow: tamaño del diff contra la base + `review_unit` (leído de review-policy.json, no duplicado) en el step summary, sin condición de bloqueo.
- [x] [T007] [SC-003] [GATES] [LEDGER] Ejecutar `scripts/test.sh`, `scripts/validate.sh` y `scripts/run-gates.py --scope pre-push` en verde; confirmar el vínculo `value_ledger` declarado (N/A justificado). Evidencia: suites OK (155 tests) y 14 gates pre-push OK el 2026-08-01.
- [ ] [T008] [FR-001] [SC-001] [SEAL] Preparar el cierre para revisión: el push al hogar canónico y el archivo del primer run remoto (URL + commit) en `evidence/` requieren autorización expresa del owner.
