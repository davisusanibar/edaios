# Arquitectura de información

| Orden | Pregunta | Fuente |
|---:|---|---|
| 01 | ¿Qué es y cómo inicio? | `README.md`, `AGENTS.md` |
| 02 | ¿Qué existe hoy? | `program-office/context/` |
| 03 | ¿Qué manda? | `core/foundation/` |
| 04 | ¿Qué se decidió? | `governance/` |
| 05 | ¿Cómo se cambia? | `.specify/`, `specs/` |
| 06 | ¿Qué aplica el gobierno? | `core/framework/` |
| 07 | ¿Qué contrato adopta una iniciativa? | `core/framework/core/profiles/`, `core/framework/core/templates/initiative/` |
| 08 | ¿Quién puede actuar y aprobar? | `core/framework/core/docs/SECURITY_AND_CONCURRENCY.md`, AuthorityRegistry y DelegationGrant |
| 09 | ¿Cómo se verifica? | `tools/`, `scripts/`, `core/framework/tests/` |
| 10 | ¿Cómo se federa sin mover autoridad? | `core/framework/core/docs/FEDERATION.md` |
| 11 | ¿Cómo se prepara y sella una release? | `core/framework/core/docs/COMPATIBILITY_AND_RELEASE.md`, `docs/core-release-cutover.md` |
| 12 | ¿Cómo se explica? | `docs/demos/` |
| 13 | ¿Cómo crecer sin contaminar Core? | `docs/add-extension.md`, `core/framework/core/docs/INITIATIVE_CONFORMANCE.md` |

Solo existe un módulo instalado: Core. Profiles y fixtures no son iniciativas.
Los consumers o especializaciones futuros conservan canon propio y se crean
cuando una necesidad gobernada lo justifica. Un candidato local no equivale a
un release Git sellado.
