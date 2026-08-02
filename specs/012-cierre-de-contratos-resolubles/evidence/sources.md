# Registro de fuentes · Feature 012

Observación local fechada el 2026-08-01 sobre el commit `3debcad` (worktree
limpio tras la feature 011). Reproducciones locales; no assessment de
producción.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | Instrucción humana de esta sesión | 2026-08-01 | Owner aprobó RFC-0003/ADR-0018 y ordenó continuar con la feature 012 | No acepta artefactos aún no presentados |
| SRC-002 | Ejecución de la regex `ONTOLOGY_ENTITY` de `tools/validation/kom_gate.py:49` sobre `core/foundation/ontology/EDAIOS_ONTOLOGY.md` | 2026-08-01 | 38 tokens capturados: 28 entidades + 10 nombres de relaciones (`governs`, `consumes`, `implements`, `decides`, `resolves`, `supersedes`, `projects`, `references`, `validates`, `represents`); solo los nombres con guion bajo escapan | Reproducción local; el fix debe demostrarse por regresión |
| SRC-003 | `core/framework/core/profiles/control-registry.json` y `core/framework/modules/conformance-core/src/edaios_conformance/resources/control-registry.json` | 2026-08-01 | La fila `kom` cita `core/framework/tests/test_kom_gate.py`, archivo inexistente; los tests KOM reales viven en `core/framework/tests/test_governance_conformance.py` (carga `kom_gate.py` en su línea 90) | Ningún check actual resuelve esos paths |
| SRC-004 | `grep -rn` de los tres nombres fantasma en `core/foundation/` | 2026-08-01 | 6 líneas `**Deriva de:**` citan archivos inexistentes: identity/README.md:18, values/README.md:18, vision/README.md:18, mission/README.md:18, constitution/CONSTITUTION_SCHEMA.md:18, manifesto/README.md:18 | Menciones sin backtick-md (tabla de constitution/README.md:13) quedan fuera del contrato |
| SRC-005 | `core/foundation/ontology/EDAIOS_ONTOLOGY.md` | 2026-08-01 | Secciones `## Entidades` (línea 15), `## Relaciones` (línea 48), `## Invariantes` (línea 65); 28 entidades y 12 relaciones vigentes | El conteo se re-verifica por el contrato bidireccional, no por este registro |
| SRC-006 | `core/foundation/strategy/README.md` | 2026-08-01 | Front matter `id: KO-STRATEGY`, `tipo: Strategy`, `estado: Ratificado` — estrategia viva del árbol | La equivalencia con `FOUNDATION_STRATEGY.md` histórica es resolución de renombre, no linaje nuevo |
