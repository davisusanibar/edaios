# ADR-0005 — Autoridad, riesgo, excepciones y evidencia verificables

**Estado:** Aceptado
**Fecha:** 2026-07-15
**Owner:** Principal Architect
**Deriva de:** RFC-0001

## Contexto

La autoridad humana, los permisos, los tramos T0–T3 y la reversa existen como
principios, pero varias superficies siguen `contracted` y el receipt v1 no liga
actor, commit, política ni digests de evidencia.

## Decisión

Core publica schemas y enforcement local para AuthorityRegistry,
DelegationGrant, SensitivityProfile, PolicyProfile, ExceptionRecord,
EvidenceReceipt, ApprovalReceipt y Outcome. El permiso es deny-by-default; una
delegación tiene scope y expiración; una excepción tiene compensaciones y
caducidad; Foundation no es exceptuable.

EvidenceReceipt v2 liga run, iniciativa, feature, actor, Core/policy, base/head,
digests, sensibilidad, resultado, límites y rollback. ApprovalReceipt es un
artefacto separado y exige actor humano autorizado. El hash local preserva
integridad reproducible, pero no se presenta como firma criptográfica o no
repudio. Cada harness marcado `enforced` debe tener implementación y pruebas
positivas y negativas.

## Alternativas

- conservar actor/fecha como texto: rechazada por falta de scope y delegación;
- permitir excepciones informales: rechazada por deuda sin expiración;
- tratar CI o agentes como aprobadores: contradice autoridad humana.

## Consecuencias

Los consumers pueden demostrar quién actuó, bajo qué política y contra qué
evidencia. Los perfiles de mayor riesgo solo agregan controles. La aceptación
continúa reservada a personas; el orquestador coordina sin decidir.

## Evidencia y frontera del claim

La suite local verifica schemas, permisos, expiración, tampering y staleness. No
demuestra identidad corporativa, firma remota ni seguridad de producción.

## Aprobación

Principal Architect · 2026-07-15 · autorización humana expresa de esta
implementación gobernada.
