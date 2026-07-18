# ADR-0009 — Consumo y federación fail-closed de extremo a extremo

**Estado:** Aceptado
**Fecha:** 2026-07-16
**Owner:** Principal Architect

## Contexto

Core 2.0.0 incorporó una CLI read-only y contratos de federación, pero la
auditoría de sello encontró fronteras divergentes: errores sin el envelope
público, consultas direccionadas que aceptaban identidades inexistentes sobre un
grafo vacío, gramáticas de namespace distintas y mounts cuya autoridad no estaba
ligada a un attachment gobernado.

## Decisión

Toda salida de consumo, exitosa o bloqueada, cumple un schema versionado y
declara comando y `claim_boundary`. `find` puede devolver una colección vacía;
`get`, `impact` y `neighborhood` bloquean una identidad no resoluble.

La gramática única de namespace es dotted, por ejemplo `equipo.iniciativa`, y
se comparte entre InitiativeManifest, FederationMount, SDK, CLI y gates. El
perfil `federation` exige al menos dos mounts. Cada mount referencia un
InitiativeManifest, su AuthorityRegistry y sus digests; `authorized_root` es
obligatorio. `authority_layer: Consumer` expresa la capa de gobierno;
`owner_actor_id` identifica al owner y debe resolver a un actor activo con rol
`initiative-owner`. La vista verifica ambas dimensiones, conformance y digests
de cada iniciativa antes de indexar KOs o EKG. Los consumidores gobernados
revalidan documento, AuthorityRegistry y corpus antes y después de cada
operación pública; una revocación o drift invalida la vista existente.

Las APIs públicas `KnowledgeClient.from_mounts(path)` y
`QueryEngine.from_mounts(path)` reciben únicamente la ruta al documento
`federation-mounts.json` gobernado. Las listas ya normalizadas quedan como
frontera interna, no como bypass público del contrato.

Los loaders locales y federados rechazan symlinks, JSON inválido, KOs
incompletos, tipos o endpoints no resolubles. Un reader nunca convierte un
artefacto corrupto en una vista vacía aparentemente válida.

## Consecuencias

Se rompe la aceptación permisiva de mounts de un solo corpus y de consultas
direccionadas sobre grafos vacíos. Aunque el propósito se conserva, cambian
entradas y respuestas públicas; la política SemVer exige MAJOR. Estas reglas
forman parte del baseline Core 3.1.0 de ADR-0012. Las numeraciones usadas durante
su construcción no constituyen releases vigentes ni una migración activa.

## Evidencia y frontera

Tests contractuales y adversariales demostrarán enforcement local sobre
fixtures. No demostrarán identidad corporativa, operación remota ni verdad de
las iniciativas.

## Aprobación

Principal Architect · 2026-07-16 · instrucción humana expresa de ejecutar los
cambios recomendados para sellar Core.
