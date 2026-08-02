# Checklist de requisitos · Feature 016

Evaluación del 2026-08-02 sobre `spec.md` y `feature.spec.yaml`.

- [x] **Alcance acotado:** una función de adapter, un playbook, la ejecución
  real sobre `kcd-001` y la primera entrada del ledger; los Límites difieren
  la opción B de RFC-0002 y el control `core-monorepo`, y prohíben commitear
  en el repo del consumer.
- [x] **Requisitos testables:** FR-001 por regresiones de las cuatro ramas;
  FR-002/003 por la evidencia archivada de la corrida real; FR-004 por el
  gate (vínculo VL-001) y los campos del ledger.
- [x] **Criterios medibles:** SC-001..004 con casos exactos.
- [x] **Trazas resolubles:** ADR-0020 (Aceptado), ADR-0016, RFC-0003,
  RFC-0002 (Ratificado).
- [x] **Owner y valor:** Principal Architect; `value_ledger: VL-001` — primera
  entrada real, no N/A.
- [x] **Fuentes (Regla IV):** deriva real con digests (SRC-002), historia del
  consumer (SRC-003), patrón del adapter (SRC-004), ledger vacío (SRC-005),
  hueco PLB-005 (SRC-006).
- [x] **Sensibilidad:** T0 — rutas y digests de repos del mismo owner; sin
  datos personales ni ruta LLM.
- [x] **Sin detalles de implementación en FR/SC:** firmas y formatos exactos
  quedan para el plan.

Sin ítems críticos pendientes: el plan queda habilitado.
