# Checklist de requisitos · Feature 012

Evaluación del 2026-08-01 sobre `spec.md` y `feature.spec.yaml`.

- [x] **Alcance acotado:** tres cierres (dominio de entidades ejecutable,
  punteros de controles resolubles, referencias de linaje resolubles); los
  Límites excluyen ampliar la ontología, modelar dominio de datos y migrar de
  formato (LinkML queda como camino futuro en RFC-0003).
- [x] **Requisitos testables:** cada FR tiene una regresión negativa asociada
  (SC-001..SC-004) y el corpus vigente como caso positivo.
- [x] **Criterios medibles:** SC-001 (KO `tipo: governs` falla), SC-002
  (mismatch bidireccional falla), SC-003 (test no resoluble falla; copias
  byte-idénticas), SC-004 (prosa no resoluble falla; históricos no resuelven),
  SC-005 (suites y 14 gates verdes).
- [x] **Trazas resolubles:** ADR-0018 (Aceptado), ADR-0014 (Aceptado), RFC-0003
  — verificado por `spec_kit_gate` (44/44).
- [x] **Owner y valor:** Principal Architect; `value_ledger` N/A justificado;
  hipótesis declarada.
- [x] **Fuentes (Regla IV):** 38 tokens/10 relaciones (SRC-002), fila `kom` y
  su archivo real (SRC-003), 6 líneas fantasma con rutas exactas (SRC-004),
  secciones y conteos de la ontología (SRC-005), sucesor de la estrategia
  (SRC-006) — todas con rótulo, fecha, alcance y límite.
- [x] **Sensibilidad:** T0 — metadatos de repositorio; sin ruta LLM.
- [x] **Sin detalles de implementación en FR/SC:** los FR declaran contrato y
  condición de fallo; regex, funciones y firmas quedan para el plan.

Sin ítems críticos pendientes: el plan queda habilitado.
