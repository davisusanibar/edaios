# Quick start · memoria operativa de agentes

Esta capacidad es opcional. Git conserva la autoridad; la memoria ayuda a
retomar trabajo y el índice acelera consultas.

## 1. Diagnóstico

```bash
edaios-core memory doctor --root .
```

La salida debe declarar `authoritative: false`, `rebuildable: true` y
`search_mode: fts5` o `fallback-like`.

## 2. Iniciar y cerrar una sesión

```bash
edaios-core memory session-start \
  --root . --session SESSION-001 --project edaios \
  --feature FEATURE-ID \
  --actor OWNER --agent codex --worktree "$PWD" \
  --branch "$(git branch --show-current)" --head "$(git rev-parse HEAD)"

edaios-core memory session-event \
  --root . --session SESSION-001 --kind gate \
  --payload '{"command":"./scripts/test.sh","exit_code":0}'

edaios-core memory session-end \
  --root . --session SESSION-001 \
  --summary "Trabajo local observado; no equivale a evidencia aceptada." \
  --head "$(git rev-parse HEAD)"
```

El summary sigue siendo observacional. Usa `memory timeline` para revisar la
cadena y su integridad. Sustituye `FEATURE-ID` por el id de la feature
seleccionada en tu worktree; el selector local no cambia el handoff canónico.

## 3. Guardar y buscar un hallazgo

```bash
edaios-core memory save \
  --root . --project edaios --subject federation \
  --claim index-policy --value "canonical-only by default" \
  --type pattern --sensitivity T0

edaios-core memory search --root . --project edaios --query "index policy"
edaios-core memory conflicts --root . --project edaios
```

`review-required` no elige ganador y bloquea promoción hasta una decisión humana.

## 4. Construir el índice canónico

```bash
edaios-core memory index-rebuild --root .
edaios-core memory index-search --root . --query "authority"
edaios-core memory index-status --root .
```

Para material no normativo, el opt-in aparece tanto en rebuild como en search:

```bash
edaios-core memory index-rebuild --root . --channel normative --channel review
edaios-core memory index-search --root . --query "proposal" --channel review
```

Un corpus modificado deja el índice `stale`; una SQLite o tabla FTS manipulada
falla por integridad. Cada hit es una proyección `authoritative=false` que enlaza
la autoridad de su fuente; vuelve a construir el índice para recuperarlo.

## 5. Preparar una superficie de agente

```bash
edaios-core agent-setup plan --root . --surface codex
edaios-core agent-setup apply --root . --surface codex
edaios-core agent-setup verify --root . --surface codex
```

El setup es project-local, idempotente y reversible. No configura Engram ni
`$HOME`. Para `claude-code` o `copilot`, cambia el valor de `--surface`.

## 6. Engram opcional

Core incluye el contrato y el adapter, no el runtime. Una iniciativa que decida
usarlo debe instalar Engram release v1.19.0 por fuera de Core, iniciarlo en
loopback y validar el contrato HTTP `health.version=0.1.0`. Si falta o intenta un
redirect, Core continúa con Git, memoria local e índice.

El provider por defecto es `local`; `engram` es opt-in en cada comando:

```bash
edaios-core memory doctor --root . --provider engram
edaios-core memory context --root . --provider engram \
  --project edaios --scope project

edaios-core memory save \
  --root . --provider engram --session SESSION-001 \
  --project edaios --subject federation \
  --claim index-policy --value "canonical-only by default"
```

`--endpoint` apunta a otro loopback. `memory context` agrega el contexto del
proyecto y solo existe con `engram`. Con `engram`, `save` exige `--session`,
`conflicts` no acepta `--subject` y `timeline` omite la verificación de cadena;
`session-event` y esa verificación son exclusivos de la memoria local.

Un runtime ausente o incompatible bloquea el comando con un error contractual,
nunca la memoria local ni el canon.

No habilites cloud/sync, T2/T3 ni `mem_judge` como decisión. Esas rutas están
fuera del contrato.
