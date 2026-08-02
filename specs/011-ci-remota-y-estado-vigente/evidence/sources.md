# Registro de fuentes · Feature 011

Observación local fechada el 2026-08-01 sobre el worktree del commit `0c60544`
más los cambios de gobernanza de RFC-0003/ADR-0017..0020 (sin commit todavía).
Las observaciones prueban el estado de este workspace; no son assessment de
producción.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | Instrucción humana de esta sesión | 2026-08-01 | Owner aprueba el plan de evolución (RFC-0003) y ordena continuar con la feature 011 | No acepta por anticipado artefactos aún no presentados |
| SRC-002 | `.specify/gates.json` | 2026-08-01 | 14 gates declaran `ci` dentro de su campo `scope`; ninguno se ejecuta hoy en un remoto (no existe `.github/workflows/` y el remoto es GitHub) | No observa configuración del remoto ni branch protection |
| SRC-003 | `core/framework/pyproject.toml` y `bitbucket-pipelines.yml` | 2026-08-01 | Contrato `requires-python >=3.11,<3.14`; la superficie Bitbucket ya declara matriz 3.11/3.12/3.13 con clone completo y verificación de commit | Solo runs efectivos aportan evidencia por versión |
| SRC-004 | `governance/ADR-0017-hogar-canonico-github-y-ci-remota.md` | 2026-08-01 | Hogar canónico `github.com/davisusanibar/edaios`; exige historia completa, integridad `GITHUB_SHA == HEAD` y job informativo no bloqueante | La aceptación del ADR no constituye evidencia remota |
| SRC-005 | `.specify/feature.json`, `specs/009-*/spec.md`, `specs/010-*/spec.md` vs `program-office/context/CURRENT_STATE.md` y `NEXT_ITERATION.md` | 2026-08-01 | Handoff real: 009 Cerrado como última cerrada, 010 Propuesto, foco activo nulo; la superficie diaria declara 008 cerrada y hogar Bitbucket | La corrección de contenido no se mecaniza: el check solo detecta contradicción |
| SRC-006 | `core/framework/core/profiles/review-policy.json` | 2026-08-01 | `review_unit: "one independently reversible change"`, `approval_actor_type: "human"` | La política no fija cifras de líneas; ningún umbral numérico tiene baseline propio |
| SRC-007 | API de GitHub (`repos/{actions/checkout,actions/setup-python}/releases/latest` y `git/ref/tags`) | 2026-08-01 | checkout v7.0.1 = commit `3d3c42e5aac5ba805825da76410c181273ba90b1`; setup-python v7.0.0 = commit `5fda3b95a4ea91299a34e894583c3862153e4b97` | Pins observados hoy; el primer run remoto verde es la verificación efectiva |
