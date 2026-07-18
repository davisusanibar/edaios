# ADR-0011 — Memoria operativa local e índices derivados sin autoridad

**Estado:** Aceptado
**Fecha:** 2026-07-16
**Owner:** Principal Architect

## Relación con el baseline day-zero

ADR-0012 incorpora esta capacidad al baseline Core 3.1.0 y reemplaza el bloqueo
operativo asociado al cutover retirado. La memoria, el índice y el adapter
mantienen exactamente la misma frontera no autoritativa; su presencia en el
baseline no implica release publicada ni Engram instalado.

## Contexto

Core distingue memoria canónica en Git, memoria local reconstruible y memoria
efímera, pero su puerto actual solo clasifica un registro y calcula una huella.
No existe todavía un provider ejecutable, búsqueda indexada, timeline de sesión
ni detección de contradicciones entre borradores. La búsqueda de Knowledge
Objects recorre el corpus completo y la integración de agentes se limita a
proyecciones del repositorio.

Engram demuestra patrones útiles de memoria local, FTS5, sesiones, conflictos y
setup multiagente. Sin embargo, Engram declara SQLite como autoridad de su propio
sistema y permite que un agente persista juicios semánticos. Esas semánticas no
pueden trasladarse al canon EDAIOS: Git y los Knowledge Objects siguen siendo la
única autoridad, y una persona autorizada conserva la aceptación.

## Decisión

Core 3.1.0 añade una superficie aditiva y vendor-neutral para memoria operativa:

- `MemoryProvider` expone capacidades, salud, observaciones, búsqueda, sesiones,
  timeline y candidatos de conflicto; deliberadamente no expone `promote`,
  `approve`, `decide` ni una escritura al canon;
- todo registro proveniente de un provider se etiqueta `authoritative=false`,
  `rebuildable=true`, con provider, versión, proyecto, sesión, sensibilidad,
  procedencia y digest;
- el provider local persiste únicamente bajo `.edaios/`, usa escritura atómica y
  lock cooperativo, y mantiene eventos de sesión encadenados por digest;
- un índice de conocimiento derivado vive bajo `.edaios/index/`, queda ligado a
  la huella del corpus y de los mounts, busca canal canónico por defecto, detecta
  staleness antes de consultar y declara si opera con FTS5 o fallback;
- el índice verifica también la integridad de sus filas y tabla FTS, y cada hit
  conserva autoridad fuente sin declarar autoritativa la proyección;
- la detección crea `ConflictCandidate` en estado `review-required`. Un LLM puede
  sugerir una relación, pero no resolverla ni elegir ganador. Un conflicto
  pendiente no impide capturar un borrador, pero bloquea su promoción;
- el timeline y el resumen son `observation-only`: pueden referenciar receipts,
  pero no los sustituyen ni cuentan como prueba por sí mismos;
- el setup de agentes es project-local por defecto, primero produce un plan, y
  solo escribe mediante `--apply`; es idempotente, falla ante colisiones y genera
  un receipt reversible;
- Engram se implementa como adapter opcional y degradable en `extensions/`,
  con release y versión de API separados, sin redirects, y validado por
  capacidades. La ausencia o incompatibilidad del runtime
  no bloquea el canon. El adapter no expone sync remoto, juicio, eliminación ni
  promoción. T2/T3 no pueden salir del workspace sin una decisión de privacidad.

Core no adopta SQLite ni Engram como fuente de verdad, no sincroniza prompts o
memoria por defecto y no incorpora cloud, TUI, daemon o un LLM juez al kernel.
Los conflictos de drafts se recalculan desde sus archivos y su sensibilidad se
declara explícitamente; borrar una cache SQLite no elimina el checkpoint.

## Alternativas

- hacer obligatoria la dependencia Engram: rechazada por acoplar el kernel a un
  runtime externo y por invertir la autoridad Git-first;
- convertir timelines en EvidenceReceipt: rechazada porque una narración del
  agente no prueba ejecución, identidad ni resultado;
- resolver conflictos con un LLM: rechazada porque una inferencia no es una
  firma humana y porque los candidatos lexicales pueden ser incompletos;
- reemplazar la búsqueda existente: rechazada; el índice se agrega como una
  superficie explícita y regenerable para conservar compatibilidad.

## Consecuencias

Las iniciativas pueden recuperar contexto entre sesiones con menor fricción y
buscar un corpus federado sin escanearlo en cada consulta, manteniendo visibles
la procedencia y el nivel de autoridad. La promoción continúa fail-closed y
requiere evidencia y aceptación separadas. El índice, las sesiones y un provider
externo pueden borrarse y reconstruirse sin pérdida del canon.

El incremento se identificó como `MINOR` (3.1.0) porque añade contratos y
comandos sin cambiar la semántica de búsqueda por defecto. ADR-0012 lo incorpora
al nuevo baseline y reemplaza expresamente el cutover anterior. El baseline no
se interpreta por ello como release sellada.

## Evidencia y frontera del claim

La evidencia local puede demostrar schemas, fallback/FTS5, staleness, hash-chain,
degradación del adapter, idempotencia del setup y prohibición de auto-promoción.
No demuestra adopción, calidad semántica, privacidad T2/T3, operación remota,
disponibilidad de Engram, identidad externa, rendimiento ni outcome.

Fuentes externas observadas el 2026-07-16 y límites de la comparación quedan en
`specs/archive/007-agent-working-memory-and-derived-index/evidence/sources.md`.

## Aprobación

Principal Architect · 2026-07-16 · instrucción humana expresa de analizar la
propuesta y ejecutar las mejoras del Core. La integración remota, publicación y
promoción de release permanecen acciones separadas.
