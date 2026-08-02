# Matriz de verificación · Feature 009

Estado: `tasked`; las rutas de evidencia se llenan al ejecutar la tarea y no
constituyen un resultado anticipado.

| SC | FR | Tarea | Test/marker | Gate | Evidencia de cierre |
|---|---|---|---|---|---|
| SC-001 | FR-001 | T003–T004 | `test_conformance_harness.py::HarnessContractTests.test_permission_guard_positive_and_negative` | TEST, CORE-CONFORMANCE | `evidence/sc-001-authority.json` |
| SC-002 | FR-002 | T005–T006 | `test_conformance_harness.py::ReceiptAndHumanAcceptanceTests` | TEST, CORE-CONFORMANCE | `evidence/sc-002-receipts.json` |
| SC-003 | FR-003 | T007 | `test_conformance_harness.py::SchemaAndProfileTests.test_policy_diff_rejects_weakening` | TEST, CORE-CONFORMANCE | `evidence/sc-003-policy.json` |
| SC-004 | FR-004 | T008 | `test_conformance_harness.py::SchemaAndProfileTests.test_profile_inheritance_is_cumulative_and_cycle_fails` | CORE-CONFORMANCE, CLAIM-SURFACE | `evidence/sc-004-controls.json` |
| SC-005 | FR-005 | T009–T011 | `test_gate_runner.py` y `test_kom_gate.py` | SDD-CONTRACT, KOM, TEST | `evidence/sc-005-gates.json` |
| SC-006 | FR-006 | T002, T016–T019 | `test_feature_handoff.py` y traceability gate | SDD-CONTRACT, TRACEABILITY, CATALOG-PROJECTION | `evidence/sc-006-sdd.json` |
| SC-007 | FR-007 | T012 | `test_working_memory.py` y CLI boundary tests | TEST, CORE-CONFORMANCE | `evidence/sc-007-privacy.json` |
| SC-008 | FR-008 | T013–T015 | `test_memory_adapter_and_setup.py`, receipt/artifact tests | TEST, CLAIM-SURFACE | `evidence/sc-008-io.json` |
| SC-009 | FR-009 | T020 | `test_release_distribution.py` y pipeline matrix | CORE-DISTRIBUTION, TEST | `evidence/sc-009-python.json` |
| SC-010 | FR-010 | T021–T024 | suite completa y failure-injection markers | TEST, VALIDATE, CORE-RELEASE-SEAL | `evidence/sc-010-close.json` |
