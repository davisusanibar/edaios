# ADR-0010 — Release reproducible y cutover canónico de Core

**Estado:** Aceptado
**Fecha:** 2026-07-16
**Owner:** Principal Architect

## Relación con el baseline day-zero

ADR-0012 reemplaza el cutover concreto descrito en este contexto y retira sus
artefactos ligados a commits y refs que ya no existen. Permanece vigente la
política reusable: candidato reproducible, aprobación local separada y sello
remoto únicamente por observación autorizada. Este ADR no afirma hoy una
release 3.0, tag, branch protegida o receipt operativo.

## Contexto histórico

La genealogía evaluada entonces vivía en `feature/core-clean`, mientras el
remoto conservaba una rama legacy como default. Core 2.0.0 había sido declarado cerrado antes de añadir
nuevas capacidades públicas bajo el mismo número. El wheel local es
reproducible mediante un builder de validación, pero el artefacto PEP 517 y el
export Foundation + Core todavía no están materializados como un candidato
durable ligado a commit y receipts.

## Decisión

Para la genealogía observada entonces se eligió la identidad de desarrollo Core
3.0.0 porque los contratos fail-closed de ADR-0009 eran incompatibles con
entradas toleradas previamente. El patrón de candidato de sello incluye:

- wheel PEP 517 construido dos veces y probado desde instalación aislada;
- bundle Foundation + Core materializado desde `export-manifest.json`;
- rechazo de symlinks y escape de roots durante packaging;
- checksum, SBOM, provenance, manifest de release y digest del árbol Git;
- EvidenceReceipt v2, PolicyProfile, AuthorityRegistry y ApprovalReceipt
  separados para una aprobación local verificable;
- un GitCutoverTarget canónico en estado `proposed`, incluido expresamente en
  la evidencia y aprobación antes de promover rama o tag;
- GitCutoverReceipt separado, observado después del push, que liga el mismo
  commit/tree a rama canónica, tag, required checks, branch protection y default
  branch remotos sin mezcla de la genealogía legacy; el repo y la rama objetivo
  se resuelven explícitamente y el observer debe estar autorizado; el receipt
  referencia evidencia durable del proveedor y la publicación durable de las
  attestations locales;
- tests y gates ejecutados por un runner CI neutral y por pre-push;
- demo, contexto y handoff derivados del mismo manifest de release.

Un manifest de candidato es un snapshot determinista, siempre declara
`prepared` y el commit candidato fija sus bytes. El checker publica un reporte
versionado que separa `candidate_status`, `readiness`, `status` y
`verification_mode`, y calcula
`ready-for-approval`, `locally-approved` o
`sealed-by-authorized-observation` desde evidencia suministrada; no consulta al
proveedor en vivo; `provider_live_verified` es siempre `false`. Commit, push,
tag, publicación y cambio del default branch
permanecen acciones separadas. Tras aprobación humana se crea una rama canónica
protegida desde la genealogía limpia, se convierte en default y se archiva la
historia legacy sin mezclarla. Dos receipts locales nunca pueden autoafirmar el
estado final.

## Alternativas

- reescribir 2.0.0: rechazada porque distintos bytes compartirían identidad;
- mezclar las historias Git: rechazada porque reintroduce la genealogía retirada;
- presentar el builder manual como wheel oficial: rechazado porque no prueba el
  backend declarado por `pyproject.toml`.

## Consecuencias

El repositorio puede quedar implementado y validado localmente antes de una
promoción. El sello remoto solo existe cuando commit, tag, default branch y
receipts apuntan a los mismos bytes con autorización explícita. El intento
concreto anterior fue sustituido, no sellado.

## Aprobación

Principal Architect · 2026-07-16 · instrucción humana expresa de ejecutar los
cambios recomendados; las mutaciones remotas siguen requiriendo autorización
Git explícita.
