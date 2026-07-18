# Demos offline

Esta guía es un derivado determinista de su JSON, de arquitectura de
información, catálogos ADR/RFC, handoff, evidencia gobernada y fuentes del
glosario. Explica el gobierno; no reemplaza la autoridad, la aprobación ni la
evidencia.

- `edaios-operating-system.html`: recorrido completo de Foundation → Core,
  gobierno, Spec Kit, arquitectura, evidencia y glosario contextual buscable.
- `edaios-core-quickstart.html`: instalación del CLI, creación de attachments,
  memoria operativa y uso opcional del adapter Engram.

La guía mantiene visibles tres planos que no son equivalentes:

- Core 3.1.0 es el baseline funcional portable bajo ADR-0013. El contrato
  `edaios.core-release-state/v2` declara `single-root` y deriva
  `unique-reachable-root` después del commit; el hash no se embebe de forma
  autorreferencial dentro del tree;
- la capacidad vNext acumulada está incluida en Core 3.1.0, pero no existe una
  rama `vNext`. Incluye memoria operativa no autoritativa, índice derivado,
  conflictos advisory, sesiones y el adapter Engram opcional. El adapter está
  incluido, pineado y probado; el runtime Engram no está instalado;
- la feature 008 normaliza las fuentes y vistas del baseline. Su estado, fase y
  tareas se derivan de Spec Kit y no convierten el baseline en release público.

El handoff canónico conserva 004 como baseline, 007 como último cierre y 008
como foco activo. No existe una iniciativa instalada: cualquier consumer futuro
entra por owner, manifest, spec, decisión y evidencia. `BASELINE INSTALADO` no
afirma ancla externa, tag observado, release público, adopción, producción
ni outcomes. `.specify/release.json` y ADR-0013 son las fuentes de la genealogía
portable; el HTML continúa siendo una vista derivada.

Regenera con `python3 tools/publishing/generate_day_zero_demos.py` y verifica
con `python3 tools/validation/day_zero_demo_check.py .`.
