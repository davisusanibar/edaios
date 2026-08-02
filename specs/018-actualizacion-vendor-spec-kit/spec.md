---
id: EDAIOS-ACTUALIZACION-VENDOR-SPEC-KIT
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: governance
trazas:
  - ADR-0022
  - ADR-0002
  - ADR-0016
  - RFC-0003
spec_tipada: specs/018-actualizacion-vendor-spec-kit/feature.spec.yaml
fuentes:
  - governance/ADR-0022-actualizacion-vendor-spec-kit.md
  - core/framework/extensions/sdd-adapter/src/edaios_sdd_adapter/spec_kit.py
  - tools/publishing/sync_spec_kit_integrations.py
  - core/framework/extensions/sdd-adapter/inject-consumer.sh
value_ledger: "N/A: actualización de perfil de vendor sin outcome institucional propio"
hipotesis_valor: Consumir el SDD comoditizado desde upstream vigente con la frontera Adopt-or-Adapt intacta elimina el costo creciente del drift y hereda el endurecimiento de seguridad del borde de inyección.
---

# Actualización del vendor Spec Kit a 0.15.1

ADR-0022 (Aceptado por orden expresa del owner) decide la actualización del
pin 0.12.11 → 0.15.1 sobre la evaluación técnica verificada a nivel de
código: cero rupturas en esquemas y CLI (SRC-002), 19 releases de
endurecimiento, y dos posturas nuevas — events desactivados en la inyección
e "interoperar sin adoptar" frente al preset de gobernanza upstream.

## Requisitos

- **FR-001:** el pin se actualiza en un solo cambio coherente: constantes del
  adapter y del sync, lock regenerado, fixtures de test, piso `>=0.15.1` en
  los cuatro manifiestos vendorizados, precheck y docs con el claim de
  versión; ninguna referencia a 0.12.11 sobrevive como claim vigente.
- **FR-002:** ninguna superficie ejecutable de events entra al consumer:
  verificado empíricamente en el sandbox (el CLI 0.15.1 no expone flag de
  events y la inyección no materializa `.specify/events.py` ni hooks).
- **FR-003:** la aceptación se demuestra con evidencia propia: inyección
  completa y gate `--profile consumer-release` en verde contra un consumer
  sandbox usando `specify` 0.15.1 aislado (sin alterar el CLI global del
  owner), archivada con versiones y salidas.
- **FR-004:** los consumers ya inyectados no se tocan en esta feature: la
  re-proyección de `kcd-001` queda declarada como deuda con su vía
  (idempotente, próximo toque), no silenciosa.

## Criterios de éxito

- **SC-001:** cero ocurrencias de `0.12.11` como claim vigente fuera de
  historia/procedencia archivada; lock regenerado con `spec-kit@v0.15.1`;
  suites y 14 gates en verde.
- **SC-002:** el sandbox archiva: versión de `specify` usada (0.15.1),
  inyección completa en verde y verificación empírica de events (sin flag en
  el CLI real, sin `.specify/events.py` ni hooks en el consumer), y gate
  `consumer-release` en verde sobre una feature mínima del sandbox.
- **SC-003:** revisión adversarial materializada (v3) y cierre con el estado
  del programa coherente.

## Límites

No se actualiza el CLI global del owner (su upgrade es acto propio); no se
adoptan extensiones upstream nuevas (assess/intent/OKF); no se re-proyecta
`kcd-001` aquí; no se afirma compatibilidad con líneas > 0.15.x; el preset
ARG no se instala — la postura es de política (ADR-0022), no de código.

## Clarifications

Revisión del 2026-08-02: sin ambigüedades del owner — ADR-0022 fija
alcance, posturas y prerequisito de aceptación. Decisión técnica registrada:
el sandbox usa `uvx --from git+…spec-kit.git@v0.15.1` con un shim de PATH
para aislar la versión sin tocar la instalación global (0.12.11 verificada
en SRC-004). Corrección empírica registrada: la evaluación de lectura
afirmó un flag `--events false` que el CLI real no tiene; el sandbox lo
refutó y verificó que la superficie de events no se materializa — la
mitigación especulativa se retira y la evidencia de ejecución manda.

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
