# Registro de fuentes · Normalización del baseline portable

| Fuente | Fecha | Alcance | Uso y límite |
|---|---|---|---|
| Instrucción humana del Principal Architect en esta tarea | 2026-07-16 | Eliminar historia Git previa, conservar el conocimiento final y crear `edaiosv/main` por SSH | Autoriza el bootstrap de `main`; no equivale a tag, release sellada ni Engram operativo |
| `git ls-remote --symref git@bitbucket.org:data_and_ia/edaiosv.git` | 2026-07-16 | Remoto destino antes del cutover | Observó cero refs, sin `HEAD`, `main` o tags; debe repetirse inmediatamente antes del push |
| ADR-0013 y `CoreReleaseState` v2 | 2026-07-16 | Genealogía `single-root` portable | Evita autorreferencia y deriva un único root; la identidad remota exacta se observa después del commit |
| `./scripts/test.sh` | 2026-07-16 | Snapshot Core 3.1.0 con memoria e integración Engram opcional | Demuestra contratos locales; no instala el runtime Engram |
| `./scripts/validate.sh` | 2026-07-16 | Registro completo de gates `core-release` | Demuestra coherencia local y debe repetirse desde el root y un clon remoto limpio |
| `.specify/gates.json` | 2026-07-16 | Registro ejecutable vigente | Define los gates; Bitbucket Pipelines solo puede delegar en su runner |

Estas observaciones T0 no demuestran adopción, rendimiento, publicación,
protección remota, firma externa ni valor institucional. El hash del root se
reporta después de crearlo y no se predeclara dentro de su propio árbol.
