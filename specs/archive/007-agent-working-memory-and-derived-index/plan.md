# Plan técnico · Memoria operativa e índice derivado

## Contexto técnico

El Core previo a esta feature declaraba una política de memoria, lectores
canónicos, receipts, locks y atomic writes, pero carecía de provider operativo
y de índice. Engram aporta una
referencia madura de experiencia local; ADR-0011 conserva sus patrones útiles y
rechaza trasladar su autoridad o juez al Core.

## Decisión de implementación

### 1. Contratos y almacenamiento local

`edaios_core.memory` publicará dataclasses inmutables y un protocolo
`MemoryProvider`. `LocalWorkingMemory` usará SQLite de stdlib bajo
`.edaios/memory/working.sqlite3`, con FTS5 si está disponible y fallback LIKE
explícito. Observaciones, sesiones, eventos y candidatos son no autoritativos.
Cada write se serializa con `workspace_lock`; roots, symlinks, UTF-8 y digests se
validan antes de persistir. La sesión conserva contador y digest terminal para
detectar truncamiento. No existe método de promoción.

### 2. Índice derivado de Knowledge Objects

`edaios_sdk_consumption.derived_index` compilará una snapshot desde un
`KnowledgeClient` ya gobernado. El manifest interno liga schema, corpus digest,
mounts fingerprint, modo de búsqueda y canales. La base se reemplaza
atómicamente bajo lock. `search_indexed` revalida corpus, filas y FTS antes de
consultar y devuelve resultados no autoritativos con autoridad fuente, canal y
source digest. La API existente
`search()` no cambia.

### 3. Conflictos y promoción

El provider crea candidatos deterministas cuando `subject + claim` coinciden y
los valores/digests difieren; un duplicado exacto es idempotente. El candidato
solo puede estar `review-required`; una sugerencia externa se anexa como
metadata no autoritativa. `assert_promotable()` falla mientras existan
candidatos pendientes. La resolución gobernada queda fuera del provider y debe
producir un artefacto humano separado. Para drafts, los candidatos se recalculan
desde los archivos en cada checkpoint y la sensibilidad es input explícito.

### 4. Sesiones y timeline

Eventos JSON canónicos se encadenan con `previous_digest` y `event_digest`.
Start captura feature, actor, agent, worktree, branch y HEAD declarados; summary
y end no cambian su carácter `observation-only`. Las referencias a receipts
incluyen digest y estado `linked`, pero no se validan como evidencia dentro del
journal. Contador, digest terminal y lifecycle detectan una cadena truncada.

### 5. Adapter Engram y onboarding

`extensions/memory-adapter` contiene un provider HTTP loopback para Engram
release v1.19.0/API health 0.1.0 y un manifest de compatibilidad. Usa `urllib` de
stdlib, timeout, token opcional y rechazo preventivo de redirects; solo health,
search, append observation, session start/end y timeline.
No implementa endpoints de sync, delete, compare/judge o cloud.

`edaios_core_harness.agent_setup` genera un plan desde
`.specify/integrations.lock.json` para Claude, Codex o Copilot. El target vive
bajo `.edaios/agent-setup/`; `apply` preserva backup, escribe atómicamente y crea
receipt, `verify` compara digests y `rollback` restaura. Un archivo ajeno no se
sobre-escribe.

### 6. CLI, schemas y baseline

La CLI añade `memory {doctor,save,search,session-start,session-event,session-end,
timeline,conflicts}` y `agent-setup {plan,apply,verify,rollback}`. Los envelopes
declaran claim boundary. Schemas versionan record, session event, conflict y
setup receipt. La superficie resultante forma parte del baseline Core 3.1.0.

## Alternativas descartadas

- reemplazar `KnowledgeClient.search()`: rompe compatibilidad y oculta staleness;
- usar una base global en `$HOME`: mezcla iniciativas y amplía permisos;
- invocar un LLM desde Core: introduce red, costo y autoridad ambigua;
- adoptar git-sync ahora: T2/T3, concurrencia y retención requieren otra decisión;
- insertar código Engram: innecesario; el adapter usa su API pública.

## Estructura afectada

```text
governance/ADR-0011-*.md
specs/archive/007-agent-working-memory-and-derived-index/
core/framework/modules/ess-core/src/edaios_core/memory.py
core/framework/modules/sdk-consumption/src/edaios_sdk_consumption/derived_index.py
core/framework/modules/harness-core/src/edaios_core_harness/{agent_setup,cli}.py
core/framework/extensions/memory-adapter/
core/framework/modules/conformance-core/.../schemas/
core/framework/core/{docs,profiles,export-manifest.json}
core/framework/tests/test_{working_memory,derived_index,agent_setup}.py
```

## Estrategia de pruebas

1. Unit tests de records, digests, channels y ausencia de promoción.
2. FTS5 y fallback, rebuild determinista, drift y búsqueda canónica opt-in.
3. Duplicados, contradicciones, suggested relation y promoción bloqueada.
4. Cadena de sesión, tampering, receipts enlazados y summary no verificado.
5. Adapter con servidor HTTP simulado, versión, timeout, host y degradación.
6. Setup plan/apply/verify/rollback, idempotencia y colisión.
7. Schemas, packaging, export y entrypoint aislado sin dependencia Engram.

## Despliegue y reversa

Reversa: revertir el incremento gobernado; `.edaios/memory`, `.edaios/index` y
`.edaios/agent-setup` son reconstruibles y pueden eliminarse. Esta reversa no
modifica por sí misma tags, publicación o configuración remota.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | Git y KOs conservan autoridad; memoria e índice declaran `authoritative=false`. |
| II. Spec antes que artefacto | PASS | Feature tipada, checklist, ADR y plan preceden implementación. |
| III. El canon crece por decisión | PASS | ADR-0011 aceptado fija la nueva frontera estructural. |
| IV. Cero cifras sin fuente | PASS | v1.19.0 y hechos externos están rotulados y fechados en `evidence/sources.md`. |
| V. Una fuente, muchas vistas | PASS | Índice, timeline y setup son proyecciones regenerables o reversibles. |
| VI. La IA consume; el humano firma | PASS | Conflictos permanecen pendientes y no existe operación de auto-promoción. |
| VII. Privacidad por diseño | PASS | T0 local; T2/T3 y transporte no loopback fallan cerrado. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `CATALOG-PROJECTION`: incorpora ADR-0011.
- `SDD-CONTRACT`: valida feature 007 y su cierre como antecedente del baseline.
- `CORE-CONFORMANCE`: añade schemas y contratos de memoria.
- `CLAIM-SURFACE`: agrega claims con tests ejecutables.
- `CORE-DISTRIBUTION`: incluye adapter, schemas y nuevos módulos en wheel/export.
- `TEST`: cubre memoria, índice, conflictos, sesiones, adapter y setup.
- `VALIDATE`: verifica que 3.1 no debilite Foundation ni gates existentes.
- `CORE-RELEASE-SEAL`: distingue baseline sin candidato de una release futura;
  no reinterpreta instalación local como sello.

## Impactos

- Arquitectura: nueva superficie aditiva dentro de Core y extensión opcional.
- Ontología/Foundation: sin cambios normativos.
- Datos/privacidad: T0 sintético; T2/T3 y sync remoto prohibidos.
- IA: puede producir observaciones/sugerencias, nunca decisiones.
- Costo: SQLite local stdlib; sin servicio obligatorio.
- Blast radius: package Core, CLI, schemas, docs, tests y distribución del baseline.
