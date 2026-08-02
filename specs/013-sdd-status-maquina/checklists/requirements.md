# Checklist de requisitos · Feature 013

Evaluación del 2026-08-02 sobre `spec.md` y `feature.spec.yaml`.

- [x] **Alcance acotado:** un subcomando de estado + una línea de ruteo en las
  8 fuentes; los Límites excluyen orquestador, runtime, cambios al phase-dag y
  al CLI de consumo.
- [x] **Requisitos testables:** FR-001/002 por regresiones deterministas de
  mapeo; FR-003 por fixture con gate rojo vs corpus verde; FR-004 por
  AGENT-PARITY tras regenerar.
- [x] **Criterios medibles:** SC-001..SC-004 con casos exactos enumerados.
- [x] **Trazas resolubles:** ADR-0002 (Aceptado, archivado), ADR-0016
  (Aceptado), RFC-0003 — carril ya decidido, sin ADR nuevo.
- [x] **Owner y valor:** Principal Architect; `value_ledger` N/A justificado;
  hipótesis declarada.
- [x] **Fuentes (Regla IV):** el caso idle sin manejo (SRC-002), la cadena del
  DAG (SRC-003), el dominio de fases observado (SRC-004) y la proyección de 8
  fuentes (SRC-005) tienen fila con rótulo, fecha, alcance y límite.
- [x] **Sensibilidad:** T0 — metadatos de repositorio; sin ruta LLM.
- [x] **Sin detalles de implementación en FR/SC:** los FR declaran contrato
  (schema congelado, dominio del token, derivación determinista); nombres de
  flags y funciones quedan para el plan.

Sin ítems críticos pendientes: el plan queda habilitado.
