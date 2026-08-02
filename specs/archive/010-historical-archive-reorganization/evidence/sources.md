# Registro de fuentes · Feature 010

Censo original al proponerse la feature (2026-07) y re-censo del 2026-08-02
sobre el commit `60b228b`, al ejecutarla. Observación local; no assessment de
producción.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | `governance/ARCHIVE_INDEX.md` | 2026-08-02 | El índice declara la regla: "una futura reubicación requiere actualizar catálogos, referencias, gates y derivados en una feature gobernada separada" — esta feature. Su prosa dice que las features 001-008 "permanecen bajo specs/", pero ya viven en `specs/archive/` — el índice está desactualizado | La reorganización debe corregir también al índice |
| SRC-002 | `ls specs/` | 2026-08-02 | Siete features cerradas en la raíz de specs (`009`, `011`, `012`, `013`, `014`, `015`, `016`) más la `010` abierta: la superficie diaria mezcla vigente con histórico | El censo crece con cada cierre; la regla debe ser sostenible, no una lista congelada |
| SRC-003 | `specs/archive/004-core-multi-initiative-scale/spec.md` | 2026-08-02 | Patrón vigente de feature archivada: el frontmatter (`spec_tipada`) y el contrato tipado (`artifact`) declaran la ruta completa bajo `specs/archive/` — mover exige reescribir ambos campos | El gate SDD valida esos paths; una reescritura parcial falla cerrado |
| SRC-004 | `tools/validation/traceability_check.py` (validate_program_surface) y `tools/validation/spec_kit_gate.py` | 2026-08-02 | La superficie diaria debe citar el directorio literal de la última feature cerrada y toda ruta `specs/` mencionada debe resolver; el gate revalida cada feature en su ubicación declarada | Mover sin actualizar CURRENT_STATE, handoff o menciones de gobernanza rompe gates — por diseño |
| SRC-005 | `governance/{RFC-0002,RFC-0003,ADR-0020}` y `.specify/feature.json` | 2026-08-02 | La gobernanza menciona rutas de features por path (`specs/011-…`, `specs/016-…`) y el handoff apunta a `specs/016-…` como última cerrada | Las menciones se actualizan a las rutas de archivo como corrección factual; las decisiones no cambian |
