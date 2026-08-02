# Registro de fuentes · Feature 015

Observación local fechada el 2026-08-02 sobre el commit `82a6126` (worktree
limpio tras cerrar 014). Reproducciones locales; no assessment de producción.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | Instrucción humana de esta sesión | 2026-08-02 | Owner ordena continuar con la feature 015 del roadmap RFC-0003 | No acepta artefactos aún no presentados |
| SRC-002 | `tools/validation/spec_kit_gate.py` (líneas 193-200) | 2026-08-02 | El propio gate declara que la tabla del Constitution Check es declarativa: "la máquina no puede verificar que un PASS sea verdad" | La única defensa actual es el checkpoint humano sin refutación preparada |
| SRC-003 | `tools/publishing/sync_spec_kit_integrations.py` | 2026-08-02 | Mundo cerrado operativo para el namespace `speckit.*` (fuentes → 5 superficies, lock sha256, huérfanos fallan); no existe namespace de agentes | La extensión reusa el mismo contrato de frontmatter y lock |
| SRC-004 | `core/framework/core/profiles/review-policy.json` | 2026-08-02 | `approval_actor_type: "human"` — el único aprobador es humano | Los agentes preparan; ninguna salida de agente constituye aprobación |
| SRC-005 | Episodio Vanishing Gradients 2026-07-30 (RFC-0003) y capítulo "Los agentes pueden escribir cientos de pruebas que no demuestran casi nada" | 2026-08-02 | Motivación externa del checker de calidad de tests | Referencia verificada, no promesa |
| SRC-006 | `tools/validation/spec_kit_gate.py:594` y `specs/archive/00*/feature.spec.yaml` | 2026-08-02 | Idioma de versionado vigente: la exigencia de matriz de verificación aplica solo a `edaios.sdd.feature/v2`; las features v1 quedaron exentas por contrato declarado | El mismo idioma exime a las v2 de la exigencia de findings del v3 |
