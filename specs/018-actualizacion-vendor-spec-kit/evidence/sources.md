# Registro de fuentes · Feature 018

Observación local fechada el 2026-08-02 sobre el commit `5141f4a`.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | Instrucción humana de esta sesión | 2026-08-02 | Owner ordena "Procede con el vendor update" sobre la evaluación técnica completa presentada | La orden materializa la aprobación de ADR-0022 |
| SRC-002 | Evaluación técnica registrada (agente de investigación, sesión 2026-08-02; releases y código upstream v0.12.11↔v0.15.1) | 2026-08-02 | 19 releases; esquemas 1.0 de preset/extension/workflow/bundle sin cambio; 5 invocaciones CLI de inject-consumer.sh vigentes con la misma firma; novedades: events en init 0.15.x, verdict_input 0.15.1, preset ARG v0.3.3 | Verificación de lectura de código, no ejecución — el sandbox de FR-003 es la ejecución |
| SRC-003 | Superficie de acoplamiento local | 2026-08-02 | Pin en spec_kit.py:29 y sync:25 → lock; fixtures en test_memory_adapter_and_setup.py:256 y test_working_memory.py:202,211,221; pisos en 4 manifiestos; precheck en inject-consumer.sh:62; claims de versión en OVERVIEW.md:12, bundle/README.md:3, demo config, CURRENT_STATE.md | Lista exacta de la evaluación; el implement la recorre completa |
| SRC-004 | `which specify && specify --version`; `uv --version` | 2026-08-02 | CLI global del owner: specify 0.12.11 en ~/.local/bin; uv 0.11.28 disponible — el sandbox puede aislar 0.15.1 vía uvx sin tocar la instalación global | El upgrade del CLI global es acto del owner, fuera de esta feature |
