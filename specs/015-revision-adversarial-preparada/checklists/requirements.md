# Checklist de requisitos · Feature 015

Evaluación del 2026-08-02 sobre `spec.md` y `feature.spec.yaml`.

- [x] **Alcance acotado:** dos agentes fuente, un namespace nuevo del mundo
  cerrado, un contrato de findings versionado por v3, un checker de calidad de
  tests; los Límites excluyen runtime, aprobación por agentes, cuatro lentes y
  retroactividad sobre v2.
- [x] **Requisitos testables:** FR-001/002 por AGENT-PARITY y fixtures de
  huérfanos; FR-003 por regresiones del contrato y el corpus v2; FR-004 por
  fixtures tautológicos; FR-005 por diseño (ningún camino de aprobación).
- [x] **Criterios medibles:** SC-001..005, incluido el dogfood de esta misma
  feature (SC-004).
- [x] **Trazas resolubles:** ADR-0019 (Aceptado), ADR-0002, RFC-0003.
- [x] **Owner y valor:** Principal Architect; `value_ledger` N/A justificado.
- [x] **Fuentes (Regla IV):** admisión del gate (SRC-002), mundo cerrado
  vigente (SRC-003), autoridad humana (SRC-004), motivación del checker
  (SRC-005), idioma de versionado (SRC-006).
- [x] **Sensibilidad:** T0; sin ruta LLM en los validadores (los agentes son
  prompts proyectados que un host ejecuta; el gate solo valida su artefacto).
- [x] **Sin detalles de implementación en FR/SC:** formatos exactos y regex
  quedan para el plan.

Sin ítems críticos pendientes: el plan queda habilitado.
