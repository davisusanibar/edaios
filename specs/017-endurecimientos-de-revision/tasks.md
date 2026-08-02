# Tareas · Feature 017

- [x] [T001] [FR-001] [SC-001] [INGEST] Registrar la orden del owner y las refs exactas de los hallazgos origen (SRC-001); tercer escape verificado vivo (SRC-003).
- [x] [T002] [FR-001] [SC-001] Extender `spec_kit_gate.py`: contrato de pin (64 hex + frescura) sobre la línea `Constitucion verificada` de `spec.md` cuando existe. Evidencia: contrato de pin en spec con disparador laxo + contrato estricto, ámbito strip_fences y NFC; 8 specs normalizadas al formato del plan.
- [x] [T003] [FR-002] [SC-002] Extender `traceability_check.py`: helper por-archivo aplicado a CURRENT_STATE y NEXT_ITERATION + regla "cerrada no figura en cola/en ejecución". Evidencia: superficie doble con normalización total, límite de oración '. ', ambigüedad fail-closed; el check cazó vivo el tercer escape.
- [x] [T004] [FR-003] [SC-002] Corregir `NEXT_ITERATION.md` al estado real del programa. Evidencia: NEXT_ITERATION corregido dos veces (estado del programa + conteos veraces tras RA-007).
- [x] [T005] [FR-003] [SC-001] [SC-002] Regresiones: pin malformado/obsoleto en spec (governance_conformance) y los tres casos de NEXT_ITERATION (program_surface); corpus en verde. Evidencia: 7 regresiones nuevas entre ambos archivos (variantes de pin, cierre falso envuelto, punto interno, ambigüedad, VL benigno); 196 tests OK.
- [x] [T006] [FR-003] [SC-003] [GATES] [LEDGER] Suites y 14 gates en verde; `value_ledger` N/A confirmado. Evidencia: 196 tests + test-quality OK; 14 gates pre-push OK.
- [x] [T007] [FR-002] [SC-003] Revisión adversarial (v3) con ambos subagentes; findings materializado; bloqueantes corregidos. Evidencia: revisión real con ambos subagentes — 11 hallazgos únicos (1 HIGH), todos corregidos con código/tests/registro; la feature que endurece la revisión fue la más revisada.
- [x] [T008] [FR-001] [SC-003] [SEAL] Cierre con aceptación del owner; commit y push por la superficie CI. Evidencia: cierre con aceptación del owner; push por la superficie CI.
