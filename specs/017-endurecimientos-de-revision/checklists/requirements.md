# Checklist de requisitos · Feature 017

Evaluación del 2026-08-02.

- [x] **Alcance acotado:** dos extensiones de checks existentes + regresiones
  + corrección del corpus; los Límites excluyen retroactividad, narrativa
  libre y gates nuevos.
- [x] **Requisitos testables:** cada FR tiene regresión negativa que
  reproduce el escape real y positiva sobre el corpus corregido.
- [x] **Criterios medibles:** SC-001..003 con casos exactos.
- [x] **Trazas resolubles:** ADR-0019 (Aceptado), ADR-0002, RFC-0003.
- [x] **Owner y valor:** Principal Architect; N/A justificado.
- [x] **Fuentes (Regla IV):** hallazgos con refs exactas (SRC-001), contrato
  de pin existente (SRC-002), tercer escape vivo verificado (SRC-003).
- [x] **Sensibilidad:** T0; sin ruta LLM.
- [x] **Sin implementación en FR/SC:** regex y firmas quedan para el plan.

Sin ítems críticos pendientes: el plan queda habilitado.
