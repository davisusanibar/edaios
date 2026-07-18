# Tareas

## Aprobación y contrato

- [x] [T001] [FR-001] [SC-001] [SEAL] Registrar aceptación humana de ADR-0014, este plan y estas tareas antes de modificar fuentes de Core.
- [x] [T002] [FR-006] [SC-006] Crear la matriz `verification.md` con cada SC enlazado a FR, tarea, test/gate y evidencia esperada.

## P0 · autoridad y evidencia

- [x] [T003] [FR-001] [SC-001] Centralizar acciones/capabilities canónicas en la policy empaquetada y pública; rechazar aliases y capacidades reservadas a agentes en `core.py` y templates.
- [x] [T004] [FR-001] [SC-001] Hacer que delegación valide iniciativa, capability efectiva, scope y ventana sin amplificación ni re-delegación no autorizada; añadir regresiones negativas.
- [x] [T005] [FR-002] [SC-002] Validar `PolicyProfile` esperada completa en `receipts.py`, aplicando approval, max-age y sensibilidad como mínimos y permitiendo al caller solo endurecer.
- [x] [T006] [FR-002] [SC-002] Ligar ApprovalReceipt a receipt, feature run e iniciativa y exigir actor humano activo con rol y capability `approve` en `AuthorityRegistry`; cubrir iniciativa/actor incorrectos.

## P1 · perfiles y gates

- [x] [T007] [FR-003] [SC-003] Extender `diff_policy` y `require_monotonic_policy` a parent, approval, antigüedad, excepciones y sensibilidad; probar cada debilitamiento.
- [x] [T008] [FR-004] [SC-004] Crear y empaquetar `control-registry.json` con implementación, gate, test/marker y claim por control; rechazar controles ficticios, paths y markers ausentes.
- [x] [T009] [FR-005] [SC-005] Crear helper de registry de gates y exigir ids, comandos, scopes mínimos y paridad pre-push/ci antes de seleccionar gates; incluir `CATALOG-PROJECTION` y `CORE-RELEASE-SEAL`.
- [x] [T010] [FR-005] [SC-005] Modificar runner, hook instalado y `validate.sh` para consumir refs stdin de Git y verificar cada SHA local en worktree aislado, incluyendo root, borrado y múltiples refs.
- [x] [T011] [FR-005] [SC-005] Hacer que KOM reciba base/head explícitos y cubra dirty, commit con padre y root sin comparar `HEAD` consigo mismo.

## P1 · filesystem, privacidad y atomicidad

- [x] [T012] [FR-007] [SC-007] Bloquear T2/T3 antes de crear DB o archivos, fijar `.edaios` 0700 y archivos/locks 0600, y redactar `value/content` sensible en la CLI; probar modos y ausencia de bytes.
- [x] [T013] [FR-008] [SC-008] Unificar helper físico de contención para receipts, artifacts, attachments, setup, índices y adapters; rechazar traversal, symlinks, raíz y `.`.
- [x] [T014] [FR-008] [SC-008] Revalidar inode/bytes y precondiciones dentro del mismo lock antes de rollback; añadir failure-injection y conservar destino ante drift.
- [x] [T015] [FR-008] [SC-008] Convertir writers multiarchivo a staging+journal o compensación verificable, cubriendo initialize, setup, receipts/artifacts e índices sin publicación parcial.

## P1/P2 · gobierno SDD y trazabilidad

- [x] [T016] [FR-006] [SC-006] Implementar handoff v3 con `active_feature: null`, lectura compatible de v2, estado idle y pruebas de selección/resolución sin foco.
- [x] [T017] [FR-006] [SC-006] Crear `specs/tombstones.json` para 006 con autoridad y reemplazo explícitos sin inventar spec, y validar números retirados.
- [x] [T018] [FR-006] [SC-006] Tipar relaciones ADR `Amends`/`Supersedes`, validar targets/ciclos en catálogo, traceability y KOM, y proyectar la relación en catálogos.
- [x] [T019] [FR-006] [SC-006] Hacer que Spec Kit/traceability exija markers SC→task→TEST/GATE y paths de evidencia en fase implemented; fallar SC huérfano o evidencia ausente.

## P2 · distribución y cierre técnico

- [x] [T020] [FR-009] [SC-009] Acotar `requires-python`, manifests y export a `>=3.11,<3.14`; actualizar Bitbucket a 3.11/3.12/3.13 y verificar links internos.
- [x] [T021] [FR-010] [SC-010] Aislar fixtures de `.edaios`, añadir todas las regresiones adversariales y ejecutar pruebas de distribución en checkout/worktrees temporales.
- [x] [T022] [FR-010] [SC-010] [GATES] Regenerar Constitución, catálogos, recursos, demo y derivados; ejecutar `scripts/test.sh`, `scripts/validate.sh` y `scripts/ci.sh` con evidencia de cada gate.
- [x] [T023] [FR-010] [SC-010] [LEDGER] [INGEST] Registrar evidencia local, límites de claim, Core 3.2.0 propuesto y ausencia de tag/release/publicación.
- [x] [T024] [FR-010] [SC-010] [SEAL] Preparar cierre de la feature, dejar `active_feature: null` solo tras aceptación del owner y no crear commit, push, tag o release sin autorización separada.
