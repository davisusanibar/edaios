# Tareas

- [x] [T001] [FR-001] Implementar `compile_catalogs.py` con colecta fail-closed
  y render determinista de ambos catálogos.
- [x] [T002] [FR-002] Registrar el gate `CATALOG-PROJECTION` en
  `.specify/gates.json` y regenerar los catálogos desde ADR-0001..0008.
- [x] [T003] [FR-003] Añadir `edaios-core kos list|get` con sobre
  `edaios.cli-output/v1`, frontera declarada y errores `blocked`.
- [x] [T004] [FR-004] Añadir `edaios-core query find|impact|neighborhood`
  read-only, latente sin instancia y fail-closed ante ids no resolubles.
- [x] [T005] [FR-005] Registrar claims enforced con markers, despinnear el
  catálogo en `day_zero_demo_check` y regenerar la demo derivada.
- [x] [T006] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [GATES] [LEDGER] [INGEST] [SEAL] Ejecutar tests y gates completos, registrar evidencia y cerrar la feature
  sin crear release, tag ni publicación.
