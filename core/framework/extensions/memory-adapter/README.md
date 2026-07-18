# Memory Adapter

Extensión opcional del puerto `local working`. Core no instala un backend ni lo
convierte en autoridad. El provider puede desaparecer sin afectar Git, KOs,
ADRs, specs o receipts.

La referencia Engram está pineada en `engram/adapter.json`: el release del
provider es `1.19.0`, mientras que `GET /health` documenta la versión del
contrato HTTP como `0.1.0`. Son ejes distintos y el adapter no compara uno con
el otro. Soporta solo API HTTP en loopback para health, search, observaciones,
sesiones, timeline y lectura de candidatos. No expone cloud, sync, delete,
compare/judge, promotion ni writes canónicos. T2/T3 se rechazan.

Engram no lista observaciones por sesión: el timeline se deriva validando la
sesión con `GET /sessions/{id}` y filtrando por `session_id` las observaciones
recientes del proyecto (`GET /observations`), acotado por `limit`. Los slices
vacíos que Engram serializa como `null` se normalizan a lista vacía. Un 4xx del
runtime se reporta como `EngramClientError` (error del caller); solo fallos de
conexión o 5xx producen `ProviderUnavailable` y salud `degraded`.

Cada resultado queda envuelto como `edaios.external-memory-result/v1` con
release del provider, versión API observada, sensibilidad y procedencia. Cuando
el caller aporta `source_digest`, el adapter lo valida y conserva en
`source_digest` y `provenance`; Engram no promete persistir esos metadatos, por
lo que la preservación declarada es la del envelope EDAIOS.

El runtime debe iniciarse e instalarse fuera de Core mediante una decisión de la
iniciativa. Si no está disponible, la integración reporta `degraded`; la memoria
Git-first continúa operativa.

## Selección de provider en el CLI

`edaios-core memory <cmd> --provider {local,engram}` (default `local`) elige el
provider. `engram` es opt-in, loopback y read/append; acepta `--endpoint` para
apuntar a otro loopback. `memory context --provider engram` expone `GET /context`
(solo lectura). `save` con `engram` exige `--session`, `conflicts` no acepta
`--subject`, y `session-event`/`verify_session` quedan solo en la memoria local.
El default `local` mantiene intacto el baseline "adapter incluido sin runtime".
