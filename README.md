# EDAIOS — Core 3.1.0 · baseline day-zero

EDAIOS es un sistema operativo del conocimiento para convertir intención humana
en cambios gobernados. Git conserva la autoridad y Core materializa contratos,
perfiles, harnesses y gates sin absorber runtimes o verdad de las iniciativas.

## Qué existe

```text
Foundation → Core
     │          └─ Spec Kit, contratos, perfiles, harnesses y conformance
     └─ identidad, Constitución, Ontología, KOM y gobierno
```

- Gobierno versionado en `governance/`.
- **Foundation 1.0.0** en `core/foundation/`.
- **Core 3.1.0** instalado como baseline funcional de raíz única portable,
  aceptado por ADR-0013.
- **Sin candidato de release activo:** `.specify/release.json` declara el
  baseline y no permite inferir publicación, tag o sello.
- Memoria operativa, índice derivado, conflictos pendientes, sesiones y
  onboarding forman parte del baseline; el adapter Engram está incluido y su
  runtime sigue siendo opcional y no instalado.
- **Un único módulo instalado:** `edaios-core`.
- **Tres perfiles acumulativos:** `core-release`, `initiative-adoption` y
  `federation`.
- **Attachments de iniciativa por contrato**, fuera de la autoridad Core.
- **Sin semántica institucional instalada.**
- **Cualquier iniciativa o consumidor futuro nace por necesidad, spec y decisión
  explícitas.**
- **Sin Platform, productos, cloud, registry, Node ni release publicada**.

## Quick start

1. Lee [AGENTS.md](AGENTS.md) y
   [CURRENT_STATE.md](program-office/context/CURRENT_STATE.md).
2. Revisa el gobierno en [governance/README.md](governance/README.md).
3. Selecciona la feature vigente con
   `python3 tools/operations/feature_context.py resolve --path-only`.
4. Ejecuta `./scripts/test.sh` y `./scripts/validate.sh`.

La guía completa está en [docs/quick-start.md](docs/quick-start.md) y la memoria
de agentes en [docs/agent-working-memory.md](docs/agent-working-memory.md). La demo es
una vista offline regenerable; no es autoridad ni evidencia de runtime.

## Frontera de claims

El baseline demuestra localmente contratos, schemas, memoria no autoritativa,
índice regenerable, sesiones, adapter degradable y distribución reproducible.
No demuestra release sellada, Engram instalado, adopción organizacional,
consumidores reales, datos, conectores, registry, firma externa, cloud, HA,
SLO, seguridad de producción, rendimiento ni outcomes; esas capacidades
permanecen no instaladas y no reclamadas.

Este repositorio no tiene licencia raíz ni autorización de publicación. La
licencia de `core/framework/` aplica solo a ese componente.
