---
id: EDAIOS-SDD-STATUS-MAQUINA
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: governance
trazas:
  - ADR-0002
  - ADR-0016
  - RFC-0003
spec_tipada: specs/013-sdd-status-maquina/feature.spec.yaml
fuentes:
  - tools/operations/feature_context.py
  - core/framework/modules/harness-core/src/edaios_core_harness/resources/phase-dag.json
  - .specify/commands
value_ledger: "N/A: superficie de estado interna sin outcome institucional propio"
hipotesis_valor: Un token de ruteo acotado elimina la inferencia de fase sobre prosa en cada superficie de agente y hace idéntico el siguiente paso para Claude, Codex y Copilot.
---

# Estado SDD legible por máquina

Hoy un agente que retoma el trabajo debe inferir la fase leyendo prosa de
spec.md y adivinando el siguiente comando; el caso idle (handoff v3 con
`active_feature: null`) ni siquiera está cubierto por `resolve` (SRC-002).
RFC-0003 adoptó de gentle-ai el patrón de estado estructurado con token de
ruteo acotado. ADR-0002 (carril SDD) y ADR-0016 (el estado SDD del monorepo no
pertenece al CLI de consumo) fijan el hogar: `tools/operations/`.

## Requisitos

- **FR-001:** existe una salida de estado SDD estructurada con schema
  versionado y congelado, que resuelve la feature con la misma precedencia que
  el resto del tooling (explícita > local > canónica) y cubre el caso idle sin
  error.
- **FR-002:** la salida incluye `nextRecommended` como token acotado cuyo
  dominio son exactamente los ids del phase-dag canónico (SRC-003) más `idle`;
  el token se deriva de forma determinista de la fase registrada y de los
  artefactos existentes, nunca de narrativa.
- **FR-003:** la salida incluye `blockedReasons` derivado de las filas de
  fallo del gate Spec Kit sobre la feature resuelta; con gate en verde la
  lista es vacía.
- **FR-004:** las ocho fuentes canónicas de comandos instruyen enrutar solo
  por `nextRecommended` y tratar `blockedReasons` como bloqueo de la fase
  actual; las superficies derivadas se regeneran por la proyección gobernada,
  nunca a mano.

## Criterios de éxito

- **SC-001:** regresiones deterministas: idle → `idle`; fase `planned` →
  `tasks`; fase `clarified` con y sin checklist → `plan` / `checklist`;
  feature cerrada → `idle`.
- **SC-002:** una feature con gate en rojo produce `blockedReasons` no vacía y
  el corpus vigente produce lista vacía.
- **SC-003:** AGENT-PARITY permanece verde tras editar las ocho fuentes y
  regenerar; ningún huérfano ni deriva.
- **SC-004:** `scripts/test.sh`, `scripts/validate.sh` y los 14 gates
  pre-push permanecen en verde.

## Límites

No se construye orquestador ni runtime (invariantes `coordinates-only`,
`no-execution`); el estado no aprueba ni promueve nada; el schema no viaja en
el CLI `edaios-core` (ADR-0008/ADR-0016); no se altera el phase-dag ni se
inventan fases nuevas.

## Clarifications

Revisión del 2026-08-02: sin ambigüedades bloqueantes del owner. Decisión
técnica registrada (corresponde al plan): con `blockedReasons` no vacía el
token recomienda corregir la fase actual; el avance solo se recomienda con
gate en verde.

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256 `45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86`.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
