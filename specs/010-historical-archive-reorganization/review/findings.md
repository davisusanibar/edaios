# Revisión adversarial · Feature 010

Ejecutada el 2026-08-02 por los subagentes reales `edaios-refutador` y
`edaios-lente-riesgo` en paralelo, una pasada exhaustiva cada uno. Hallazgos
duplicados entre lentes consolidados; el ciclo de corrección se aplicó antes
del cierre.

| Id | Lente | Severidad | Estado | Hallazgo | Refs |
|---|---|---|---|---|---|
| RA-001 | refutador | HIGH | corregido | Cifra sin fuente propagada por el propio censo: "ocho cerradas" cuando la enumeración y el archivo real suman siete. Corregido en sources (SRC-002), plan (Contexto y Principio IV) y tasks (T001) — Regla IV aplicada contra su aplicador. | plan.md, evidence/sources.md, tasks.md |
| RA-002 | refutador | HIGH | corregido | NEXT_ITERATION declaraba "En cola: 016" contradiciendo handoff y CURRENT_STATE (016 cerrada); el reemplazo del cierre anterior no coincidió y quedó texto obsoleto. Corregido con el estado real del programa. Ambos lentes lo reportaron (dedup con lente RA-001). | program-office/context/NEXT_ITERATION.md |
| RA-003 | refutador | MEDIUM | corregido | La spec de la 010 citaba una huella de 62 caracteres hex — longitud imposible para sha256 — heredada de su autoría original; la propagación de pines no la tocó porque el patrón no coincidía. Corregida al pin vigente (45af1fa8…). El control PIN_LINE solo valida plan.md; queda anotado como endurecimiento futuro. | spec.md Constitution Check |
| RA-004 | refutador | MEDIUM | corregido | La demo declaraba "Foco activo · specs/archive/016-…" con el handoff en `active: null` — el trío generador/config/check coaccionaba idle al último cierre desde el baseline. Corregido: idle explícito ("Foco activo · ninguno (handoff idle)"), config con `active_feature: null`, y el check lo exige. | generate_day_zero_demos.py, day_zero_demo_check.py, demo config |
| RA-005 | lente-riesgo | MEDIUM | corregido | El check de frescura solo lee CURRENT_STATE: la contradicción de NEXT_ITERATION escapaba en silencio. El contenido quedó corregido (RA-002); extender validate_program_surface a NEXT_ITERATION queda anotado como endurecimiento futuro, no como fila aspiracional. | traceability_check.py:244 |
| RA-006 | refutador | LOW | corregido | La "Regla de superficie" del índice era transitoriamente falsa (016 archivada antes del cierre de 010, raíz sin última cerrada). Este cierre la satisface: 010 queda como última cerrada en raíz. | governance/ARCHIVE_INDEX.md, .specify/feature.json |

Lo que se intentó refutar y resistió (ambos lentes): 14 pares spec/typed
reescritos, 15 rutas del índice y tombstone resolubles, autoridades
consistentes, menciones de gobernanza resueltas, globs de descubrimiento
recursivos sin vacíos silenciosos, quick-start conforme.

Veredicto humano: aceptado por el owner en el cierre (autorización expresa de
la sesión del 2026-08-02); los agentes prepararon y bloquearon hasta la
corrección, no aprobaron.
