---
id: EDAIOS-REVISION-ADVERSARIAL-PREPARADA
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: governance
trazas:
  - ADR-0019
  - ADR-0002
  - RFC-0003
spec_tipada: specs/015-revision-adversarial-preparada/feature.spec.yaml
fuentes:
  - governance/ADR-0019-agentes-revisores-preparacion-sin-autoridad.md
  - tools/publishing/sync_spec_kit_integrations.py
  - tools/validation/spec_kit_gate.py
  - core/framework/core/profiles/review-policy.json
value_ledger: "N/A: preparación de revisión interna sin outcome institucional propio"
hipotesis_valor: Una refutación preparada y trazable convierte el checkpoint humano de lectura en frío en firma informada, y el Constitution Check declarativo deja de ser indefendible sin costo para la autoridad humana.
---

# Revisión adversarial preparada

El Constitution Check es declarativo — el gate admite que no puede verificar
que un PASS sea verdad (SRC-002) — y el checkpoint humano revisa sin ninguna
refutación preparada. ADR-0019 (Aceptado) decide el mecanismo: dos agentes
revisores de solo lectura como fuentes canónicas proyectadas bajo el mundo
cerrado AGENT-PARITY, hallazgos materializados por feature, y calidad de tests
verificada (el video de Vanishing Gradients: "cientos de tests que no prueban
casi nada", SRC-005).

## Requisitos

- **FR-001:** existen dos agentes revisores como fuentes canónicas
  (`edaios.refutador`: intenta refutar cada PASS del Constitution Check y cada
  claim FR/SC con evidencia de archivo; `edaios.lente-riesgo`: fail-open e
  inversiones de autoridad), con mandato de solo lectura, puerta de precisión,
  presupuesto de una sola pasada y regla de sobre de retorno.
- **FR-002:** las fuentes de agentes se proyectan a las superficies de agente
  como segundo namespace del mundo cerrado: byte-derivadas, con lock, deriva y
  huérfanos fallan; queda prohibida la superficie manual.
- **FR-003:** los hallazgos se materializan en `review/findings.md` con
  contrato verificable: filas con severidad y estado acotados, referencias no
  vacías; un hallazgo CRITICAL o HIGH abierto bloquea; el contrato de feature
  v3 lo exige para cambio estructural al cierre — las features v2 previas
  conservan su contrato.
- **FR-004:** la calidad de tests se verifica en la suite: un test sin
  aserciones o con aserciones constantes o tautológicas falla cerrado.
- **FR-005:** la autoridad no cambia: los agentes preparan; ningún hallazgo
  aprueba ni rechaza; el único aprobador es humano (SRC-004).

## Criterios de éxito

- **SC-001:** AGENT-PARITY cubre el namespace nuevo: un archivo huérfano o
  apócrifo en las superficies de agentes hace fallar la verificación.
- **SC-002:** regresiones del contrato de findings: severidad o estado fuera
  de dominio falla; CRITICAL/HIGH abierto falla; v3 estructural implementada
  sin findings falla; las features v2 del corpus pasan sin findings.
- **SC-003:** regresión de calidad de tests: un test sin asserts y un assert
  tautológico fallan cerrado; la suite vigente pasa.
- **SC-004:** esta misma feature (v3, estructural) cierra con su
  `review/findings.md` real producido por los dos agentes — dogfood del
  mecanismo completo.
- **SC-005:** `scripts/test.sh`, `scripts/validate.sh` y los 14 gates
  pre-push permanecen en verde.

## Límites

Los agentes no ejecutan gates ni aprueban (ADR-0019); no se construye runtime
ni orquestador; no se re-abre el alcance de cuatro lentes (dos bastan para un
mantenedor único); las features v2 cerradas no se re-revisan retroactivamente
— el contrato nuevo aplica desde v3.

## Clarifications

Revisión del 2026-08-02: sin ambigüedades bloqueantes del owner — ADR-0019
fija agentes, superficies, contrato de findings y autoridad. Decisión técnica
registrada: la exigencia de findings se versiona por el schema tipado de la
feature (`edaios.sdd.feature/v3`), el mismo idioma con que v2 introdujo la
matriz de verificación sin romper a las v1.

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256 `45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86`.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
