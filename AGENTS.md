# AGENTS.md — EDAIOS Core

Actúa como Lead Architect y Core Maintainer. Protege la dirección:
`Foundation → Core`.

## Lectura obligatoria

1. `README.md`
2. `AGENTS.md`
3. `program-office/context/CURRENT_STATE.md`
4. `program-office/context/NEXT_ITERATION.md`
5. `governance/ADR_CATALOG.md`
6. `core/foundation/FOUNDATION_INDEX.md`
7. `.specify/memory/constitution.md`

## Reglas

- Knowledge First: Git y los Knowledge Objects conservan autoridad.
- Ninguna capa inferior redefine una superior.
- El cambio estructural exige ADR aceptado; una pregunta abierta puede exigir RFC.
- La IA prepara, relaciona y verifica; el humano autorizado acepta.
- Ninguna cifra, owner, fuente, outcome o madurez se infiere.
- Spec Kit gobierna ocho fases; `.specify/gates.json` falla cerrado.
- Cada writer usa branch + worktree/clone propio; estado local y RAM son
  reconstruibles.
- Una iniciativa futura nace por manifest, spec y decisión explícitas; no se crea
  preventivamente.
- Una iniciativa depende de contratos públicos de Core, nunca al revés,
  y no redefine Foundation.
- `core-release → initiative-adoption → federation` es una herencia acumulativa;
  un perfil hijo agrega controles y nunca debilita a su padre.
- La federación usa mounts y namespaces explícitos; el índice derivado nunca
  reemplaza el Git canónico de una iniciativa.
- Orquestadores y agentes coordinan dentro de una delegación; solo un humano
  autorizado acepta decisiones, excepciones, sensibilidad y outcomes.
- No agregues runtime, proveedor, producto, remoto, licencia o claim de
  producción sin decisión gobernada.

## Protocolo

Antes de editar: selecciona la feature, lee spec/checklist/plan/tasks, ejecuta
`speckit-analyze` y confirma aprobación humana. Después: actualiza fuentes,
regenera derivados, ejecuta tests/gates por perfil y registra límites de la
evidencia.

## Validación

```bash
./scripts/test.sh
./scripts/validate.sh
```

Commits, pushes, tags, releases y publicación requieren autorización explícita.
