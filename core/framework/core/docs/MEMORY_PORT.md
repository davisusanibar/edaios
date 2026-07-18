# Memory Port

Core 3.1 separa autoridad, contexto operativo e índices. La ubicación no eleva
el contenido: solo los Knowledge Objects gobernados y versionados en Git pueden
ser canónicos.

| Canal | Autoridad | Persistencia | Uso |
|---|---:|---|---|
| `canonical` | sí | Git versionado | Foundation, ADR/RFC, specs aceptadas y receipts |
| `draft` / `review` | no | Git o `.edaios/drafts/` | material pendiente de promoción humana |
| `local-working` | no | `.edaios/memory/`, reconstruible | bugs, patrones, hallazgos y continuidad entre sesiones |
| `ephemeral` | no | RAM/cache | cálculo descartable |
| índice derivado | no | `.edaios/index/`, reconstruible | búsqueda rápida sobre fuentes gobernadas |

## Contrato del provider

`edaios_core.memory.MemoryProvider` permite `health`, `capabilities`,
`save_observation`, `search`, `start_session`, `end_session`, `timeline` y
`conflict_candidates`.

Deliberadamente no existe `promote`, `approve`, `decide` o
`write_canonical`. Cada resultado de un provider declara:

```text
channel=local-working
authoritative=false
rebuildable=true
provider + provider_version + source_digest + sensitivity
```

La implementación local usa SQLite de stdlib bajo
`.edaios/memory/working.sqlite3`, lock cooperativo y writes transaccionales. Una
revisión distinta no sobrescribe la anterior: tiene identidad content-addressed.

## Conflictos: surfacing, no juez

Dos observaciones con el mismo `project + subject + claim` y valores distintos
crean un `ConflictCandidate` `review-required`. Un duplicado exacto es
idempotente. Un agente puede anexar `suggested_relation`, pero el candidato no
cambia de estado y `assert_promotable()` falla cerrado.

La resolución pertenece al flujo gobernado: fuente, owner, evidencia y firma
humana. Core no selecciona ganador ni convierte una confianza de LLM en prueba.

## Sesiones y evidencia

El journal registra `start → event* → summary → end` con eventos encadenados por
SHA-256. Sirve para reconstruir qué ocurrió y encontrar contexto. No es un
EvidenceReceipt:

- `summary` siempre nace `unverified`;
- una referencia a receipt queda `linked-not-verified`;
- alterar un evento invalida la cadena;
- truncar eventos invalida el contador y digest terminal de la sesión;
- una sesión cerrada exige exactamente `start → event* → summary → end`;
- verificación de identidad, gates y artefactos continúa en receipts separados.

## Índice derivado

`DerivedKnowledgeIndex` compila una snapshot explícita del `KnowledgeClient`:

- FTS5 cuando SQLite lo soporta; fallback LIKE declarado en `search_mode`;
- canal `normative` por defecto;
- `review`, `draft` o `superseded` requieren opt-in al construir y consultar;
- manifest ligado a `corpus_digest` y `mounts_digest`;
- drift produce `IndexStaleError` hasta ejecutar `rebuild`;
- manipular `documents` o la tabla FTS produce `IndexIntegrityError`;
- cada hit declara `authoritative=false` y conserva por separado
  `source_authoritative`, KO ID, autoridad, canal, source y source digest.

`KnowledgeClient.search()` conserva su semántica 3.0. El índice se usa de forma
explícita para no ocultar staleness ni cambiar defaults.

## Adapter Engram

El adapter en `extensions/memory-adapter/` referencia Engram release v1.19.0,
valida por separado el contrato HTTP reportado por health (`0.1.0`) y usa solo
loopback sin redirects. Soporta health, search, context (lectura), append de
observación, sesiones, timeline y lectura de candidatos. No soporta cloud, sync,
delete, compare/judge, promotion, writes canónicos o T2/T3.

El CLI `edaios-core memory` selecciona provider con `--provider {local,engram}`
(default `local`). `engram` es opt-in y usa solo operaciones read/append vía
loopback (`--endpoint` opcional). `memory context` requiere `--provider engram`;
`session-event` y `verify_session` son exclusivos de la memoria local. Un runtime
Engram ausente o incompatible produce un error contractual del comando, nunca
bloquea la memoria local ni el canon.

Engram no expone listado de observaciones por sesión: el timeline se deriva en
el adapter validando la sesión (`GET /sessions/{id}`) y filtrando por
`session_id` las observaciones recientes del proyecto (`GET /observations`),
acotado por su `limit`. Un slice vacío puede llegar serializado como `null` y
se normaliza a lista vacía.

Runtime ausente o incompatible produce `degraded`/`incompatible`; no bloquea Git
ni la búsqueda canónica. Un rechazo 4xx de Engram es un error del caller
(`EngramClientError`), no degradación del provider. Instalar u operar Engram es
una decisión de la iniciativa, no una dependencia del Core.

## Onboarding project-local

```bash
edaios-core agent-setup plan --surface codex
edaios-core agent-setup apply --surface codex
edaios-core agent-setup verify --surface codex
edaios-core agent-setup rollback --receipt .edaios/agent-setup/receipts/SETUP-....json
```

Superficies: `codex`, `claude-code`, `copilot`. Plan no escribe; apply requiere
instrucción explícita, preserva backup y receipt; una colisión bloquea; rollback
solo opera si receipt ID, surface, target, backup y digests corresponden al mismo
apply y siguen estables dentro del lock. Nunca toca `$HOME` ni allowlists globales.

Los conflictos de `.edaios/drafts/` se recalculan desde los drafts
content-addressed en cada checkpoint; borrar la base de working memory no elimina
el bloqueo. La sensibilidad debe ser aportada explícitamente al ingerir y nunca
se infiere como T0.

## Privacidad y concurrencia

T2/T3 no salen del workspace sin decisión de privacidad. El adapter Engram los
rechaza. Writes compartidos usan lock, atomic write o transacción. `.edaios/`
permanece ignorado y no debe incluirse en un commit o export canónico.

Autoridad: ADR-0003 y ADR-0011.

Implementaciones trazables:

- `core/framework/modules/ess-core/src/edaios_core/memory.py`
- `core/framework/modules/sdk-consumption/src/edaios_sdk_consumption/derived_index.py`
- `core/framework/extensions/memory-adapter/engram/adapter.json`
