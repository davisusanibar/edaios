# Registro de fuentes · Feature 013

Observación local fechada el 2026-08-02 sobre el commit `5e48b9c` (worktree
limpio tras cerrar 011 y 012). Reproducciones locales; no assessment de
producción.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | Instrucción humana de esta sesión | 2026-08-02 | Owner ordena continuar con la feature 013 del roadmap RFC-0003 aprobado | No acepta artefactos aún no presentados |
| SRC-002 | `tools/operations/feature_context.py` | 2026-08-02 | `resolve()` retorna `active_feature` del handoff, que es `None` en idle v3 (línea 156); ninguna rama imprime estado estructurado; subcomandos actuales: select/resolve/clear | El comportamiento idle sin manejo se corrige en esta feature |
| SRC-003 | `core/framework/modules/harness-core/src/edaios_core_harness/resources/phase-dag.json` | 2026-08-02 | Schema `edaios.phase-dag/v1`, cadena lineal constitution→specify→clarify→checklist→plan→tasks→analyze→implement | El DAG es fuente canónica; esta feature lo lee, no lo redefine |
| SRC-004 | `specs/*/spec.md` del corpus | 2026-08-02 | Valores de `fase` observados en features reales: specified, clarified, planned, tasked, implemented; la fase checklist no persiste marcador propio | El mapeo fase→token debe cubrir exactamente ese dominio observado |
| SRC-005 | `.specify/commands/speckit.*.md` y `tools/publishing/sync_spec_kit_integrations.py` | 2026-08-02 | 8 fuentes canónicas proyectadas a 5 superficies con lock sha256 (AGENT-PARITY) | Toda edición pasa por la fuente y regeneración; jamás por las vistas |
