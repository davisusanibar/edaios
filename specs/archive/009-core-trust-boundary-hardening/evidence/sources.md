# Registro de fuentes · Feature 009

Observación local fechada el 2026-07-16 sobre el commit `dc3cb5b`, antes de
implementar la feature. Las reproducciones prueban comportamiento del baseline
en este workspace; no son un assessment de producción ni una promesa de mejora.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | Instrucción humana de esta tarea | 2026-07-16 | Principal Architect confirmado como owner y aprobador; solicita implementar las mejoras analizadas | No acepta por anticipado un ADR o plan aún no presentado |
| SRC-002 | `core/framework/modules/harness-core/src/edaios_core_harness/core.py` y `core/framework/core/profiles/security-policy.json` | 2026-07-16 | Divergencia local entre aliases de outcome y delegación sin prueba de no amplificación | No prueba identidad del actor fuera del fixture |
| SRC-003 | `core/framework/modules/harness-core/src/edaios_core_harness/receipts.py` | 2026-07-16 | PolicyProfile y AuthorityRegistry se aplican parcialmente al verificar receipts | Los hashes locales no son firma ni no repudio |
| SRC-004 | `core/framework/modules/conformance-core/src/edaios_conformance/profiles.py` y profiles versionados | 2026-07-16 | Monotonía limitada a controles y controles sin registry de implementación | No evalúa controles de una iniciativa real |
| SRC-005 | `.specify/gates.json`, `scripts/run-gates.py`, `scripts/install-hooks.sh` y `tools/validation/kom_gate.py` | 2026-07-16 | Scopes desplazables, hook centrado en worktree y transición dependiente de HEAD | No observa configuración remota ni branch protection |
| SRC-006 | `.specify/feature.json`, `tools/operations/feature_context.py` y `tools/validation/spec_kit_gate.py` | 2026-07-16 | Handoff sin reposo y cobertura FR→tarea sin cadena SC→evidencia | La aceptación humana no puede mecanizarse |
| SRC-007 | `core/framework/modules/ess-core/src/edaios_core/memory.py` y CLI del harness | 2026-07-16 | Persistencia local admite T2/T3 y expone valores sin instalar almacenamiento seguro | Permisos del host no equivalen a privacidad de producción |
| SRC-008 | `core/framework/pyproject.toml`, `bitbucket-pipelines.yml` y ADR-0014 | 2026-07-16 | Contrato observado `>=3.11`; la propuesta lo acota a `>=3.11,<3.14` y exige CI 3.11/3.12/3.13 | Solo las ejecuciones efectivas aportarán evidencia por versión |
| SRC-009 | `.specify/memory/constitution.md`, ADR-0002, ADR-0005 y ADR-0011 | 2026-07-16 | Gobierno aplicable a spec, autoridad, evidencia y memoria | Foundation permanece superior y sin cambios |
| SRC-010 | ADR-0014 propuesto | 2026-07-16 | Identidad de contrato Core 3.2.0 por superficies aditivas de control y lifecycle | No constituye tag, release o publicación |
