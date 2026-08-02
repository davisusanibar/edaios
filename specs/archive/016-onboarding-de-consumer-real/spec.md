---
id: EDAIOS-ONBOARDING-DE-CONSUMER-REAL
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: architecture
trazas:
  - ADR-0020
  - ADR-0016
  - RFC-0003
  - RFC-0002
spec_tipada: specs/archive/016-onboarding-de-consumer-real/feature.spec.yaml
fuentes:
  - governance/ADR-0020-entrega-gobernada-del-gate-al-consumer.md
  - core/framework/extensions/sdd-adapter/src/edaios_sdd_adapter/spec_kit.py
  - tools/validation/spec_kit_gate.py
  - governance/VALUE_LEDGER.md
value_ledger: VL-001
hipotesis_valor: La entrega gobernada del gate elimina la deriva silenciosa del consumer real y produce el primer outcome medible del programa con baseline verificado.
---

# Onboarding de consumer real

El consumer real existe y su deriva también: el módulo `kcd-001` de
`data-evolutionary` porta una copia vendorizada del gate pineada al commit
baseline `0c60544` vía sidecar manual, y esa copia ya divergió del gate
vigente de Core (SRC-002 — digests distintos tras cinco features de
evolución). Es la fragilidad exacta que RFC-0002 documentó y que ADR-0020
(Aceptado) decidió cerrar con `seed_gate()`.

## Requisitos

- **FR-001:** el adapter SDD ofrece `seed_gate()`: copia el gate al consumer
  con sidecar de procedencia (versión de Core, digest sha256, fecha, vía);
  es idempotente ante copia idéntica; ante copia divergente se niega a
  sobrescribir sin confirmación explícita y reporta ambos digests — la deriva
  se reporta, no se pisa.
- **FR-002:** existe un playbook acotado de onboarding (PLB-005) que
  gobierna la secuencia: sembrar, validar con `--profile consumer-release`
  sobre el repo del consumer, archivar evidencia; sin pasos aspiracionales.
- **FR-003:** la siembra se ejecuta sobre el consumer real (`kcd-001`): la
  negativa ante la copia divergente actual queda demostrada, la re-siembra
  confirmada actualiza gate y sidecar, y el gate sembrado valida las features
  reales del consumer; toda la corrida queda archivada como evidencia.
- **FR-004:** el Value Ledger registra `VL-001` con apuesta, owner de
  beneficio, baseline con fuente y fecha (la copia manual divergente),
  acción, evidencia y limitaciones; el estado del outcome queda en
  observación — un gate técnico no cierra un outcome.

## Criterios de éxito

- **SC-001:** regresiones de `seed_gate()`: siembra fresca crea gate y
  sidecar con digest; segunda siembra idéntica es no-op; divergencia sin
  confirmación falla con ambos digests; re-siembra confirmada actualiza
  ambos archivos.
- **SC-002:** evidencia real archivada: negativa ante la divergencia vigente
  de `kcd-001`, re-siembra confirmada, y corrida del gate sembrado sobre las
  features del consumer.
- **SC-003:** `VL-001` existe en el ledger con todos los campos declarados y
  el vínculo `value_ledger: VL-001` de esta feature resuelve en el gate.
- **SC-004:** revisión adversarial materializada (contrato v3) y
  `scripts/test.sh`, `scripts/validate.sh` y los 14 gates pre-push en verde.

## Límites

No se empaqueta el gate en el wheel (opción B de RFC-0002, diferida); no se
crea el control `core-monorepo` (gatillo: segundo consumer); no se modifican
las features ni el código del consumer más allá de la superficie sembrada
(`tools/validation/`); no se hace commit en el repositorio del consumer — su
árbol queda para revisión de su owner; el outcome de VL-001 no se declara
logrado, queda en observación.

## Clarifications

Revisión del 2026-08-02: sin ambigüedades bloqueantes del owner — ADR-0020
fija mecanismo y alcance; el consumer real está localizado en el workspace
(`data-evolutionary/kcd-001`) con la copia manual y su sidecar intactos como
baseline. Decisión técnica registrada: la confirmación explícita de
re-siembra es el parámetro `force=True` de la API (la política de quién lo
invoca pertenece al playbook, no al código).

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256 `45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86`.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
