# Revisión adversarial · Feature 015

Ejecutada el 2026-08-02 por `edaios.refutador` y `edaios.lente-riesgo`
(una pasada exhaustiva cada uno) sobre spec, plan, tasks, evidencia y el diff
completo de la feature. Dogfood de SC-004: la primera revisión adversarial del
mecanismo es sobre el mecanismo mismo.

| Id | Lente | Severidad | Estado | Hallazgo | Refs |
|---|---|---|---|---|---|
| RA-001 | lente-riesgo | HIGH | corregido | La proyección de agentes era fail-open: si `.specify/agents/` desaparecía, el sync retiraba las superficies en silencio en vez de fallar (el namespace de comandos sí falla vacío). Corregido: sin fuentes de agentes el sync falla cerrado. | tools/publishing/sync_spec_kit_integrations.py, FR-002 |
| RA-002 | refutador | MEDIUM | aceptado | El checker de calidad exige la aserción dentro del cuerpo del método `test_*`: un test que delega todas sus aserciones a un helper daría falso positivo. Falla cerrado (exceso de rigor, no fuga); la suite vigente no tiene ese patrón. Trade-off aceptado y documentado. | tools/validation/test_quality_check.py, FR-004 |
| RA-003 | refutador | LOW | refutado | Sospecha de que el presupuesto ≤450 palabras del plan estaba violado por las fuentes de agentes. Refutado con conteo: refutador 317, lente-riesgo 292 palabras de cuerpo. | .specify/agents/, plan.md |

Veredicto humano: aceptado por el owner en el cierre (autorización expresa de
la sesión del 2026-08-02); los agentes prepararon, no aprobaron.
