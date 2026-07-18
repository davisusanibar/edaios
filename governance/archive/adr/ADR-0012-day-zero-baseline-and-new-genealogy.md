# ADR-0012 — Baseline day-zero de Core 3.1 y nueva genealogía Git

**Estado:** Aceptado
**Fecha:** 2026-07-16
**Owner:** Principal Architect

## Relación vigente

ADR-0013 reemplaza el pin literal del root y el hogar remoto concreto mediante
una raíz única derivada. El baseline 3.1.0, la ausencia de candidato y las
fronteras de claims decididas aquí permanecen vigentes.

## Contexto

El repositorio remoto fue reinicializado por instrucción humana expresa con un
único commit raíz en `main`, sin ramas secundarias ni tags. El contenido
conservó la superficie funcional Core 3.1.0, pero las fuentes operativas todavía
describen un candidato 3.0 pendiente, una rama vNext y el cutover de la feature
006. Esa narrativa ya no corresponde al estado Git observado.

## Decisión

Core 3.1.0 pasa a ser el baseline funcional instalado de la nueva genealogía.
La versión describe el contrato acumulado del producto; no afirma continuidad
con un release remoto anterior ni reutiliza receipts, tags o evidencia de la
genealogía retirada.

La parte reusable de ADR-0010 permanece vigente como política para preparar y
sellar releases futuras. Su cutover específico de Core 3.0.0 queda reemplazado
por esta decisión: la feature 006 se cierra por sustitución y sus manifests,
targets y evidencias ligados a commits retirados dejan de ser estado operativo.

El gate de release se vuelve neutral respecto de features y versiones. En
ausencia de un manifest explícito declara `baseline-no-candidate` y no permite
inferir un release. Un candidato futuro debe suministrar manifest y contratos
versionados, comprometidos y verificables; no puede reaprovechar artefactos de
otra versión.

`main` es la única rama canónica. Los cambios siguientes nacen en una feature,
ejecutan el registro de gates mediante CI y llegan a `main` sin reescribir su
historia. El tag `v3.1.0` solo puede apuntar al commit de normalización después
de observar CI verde y protección contra reescritura; el tag identifica el
baseline, no demuestra adopción, producción, firma externa u outcomes.

La configuración de Bitbucket Pipelines es una vista ejecutable del registro
`.specify/gates.json`: invoca `scripts/ci.sh`, pero no redefine los gates ni
reemplaza la aceptación humana.

## Alternativas

- renumerar el producto a 1.0.0: rechazada porque ocultaría la compatibilidad y
  capacidades acumuladas del contrato Core ya implementado;
- conservar 3.0 como candidato pendiente: rechazada porque sus refs y
  genealogía ya no existen;
- tratar el nuevo root como release sellado por sí solo: rechazada porque un
  commit o tag no sustituye evidencia, CI, protección ni autoridad humana;
- incorporar una iniciativa o runtime al baseline: rechazado porque invierte la
  dependencia Foundation → Core → Consumer.

## Consecuencias

README, contexto, quick start, changelog y demo deben mostrar Foundation + Core
3.1.0 instalados y ningún consumer. La primera iniciativa será externa y entrará
por attachment, spec y decisión. Specs anteriores pueden conservar conocimiento
de diseño, pero no actuar como handoff, candidato o evidencia remota vigente.

## Aprobación

Principal Architect · 2026-07-16 · instrucción humana expresa de normalizar el
baseline, configurar CI, publicar `main` y crear `v3.1.0` únicamente con gates
y estado remoto observados.
