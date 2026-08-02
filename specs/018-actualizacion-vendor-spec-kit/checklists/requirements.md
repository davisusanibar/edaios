# Checklist de requisitos · Feature 018

Evaluación del 2026-08-02.

- [x] **Alcance acotado:** un cambio de pin coherente + sandbox de
  aceptación; los Límites excluyen el CLI global, extensiones upstream
  nuevas, re-proyección de kcd-001 y líneas > 0.15.x.
- [x] **Requisitos testables:** FR-001 por grep de claims + lock + suites;
  FR-002/003 por la evidencia del sandbox (ausencia de events verificada);
  FR-004 por declaración de deuda con vía.
- [x] **Criterios medibles:** SC-001..003 con casos exactos.
- [x] **Trazas resolubles:** ADR-0022 (Aceptado), ADR-0003, ADR-0016,
  RFC-0003.
- [x] **Owner y valor:** Principal Architect; N/A justificado.
- [x] **Fuentes (Regla IV):** orden del owner (SRC-001), evaluación con
  alcance y límite (SRC-002), lista exacta de acoplamiento (SRC-003),
  versiones locales verificadas (SRC-004).
- [x] **Sensibilidad:** T0; el sandbox no procesa datos personales.
- [x] **Sin implementación en FR/SC:** comandos y shims quedan en el plan.

Sin ítems críticos pendientes: el plan queda habilitado.
