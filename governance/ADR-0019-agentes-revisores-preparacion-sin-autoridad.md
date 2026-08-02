# ADR-0019 — Agentes revisores de solo lectura: preparación sin autoridad

**Estado:** Aceptado
**Fecha:** 2026-08-01
**Owner:** Principal Architect

## Contexto

El Constitution Check de los planes es declarativo: `spec_kit_gate.py` verifica
completitud, dominio de veredictos y frescura del pin, pero admite en su propio
código que no puede verificar que un PASS sea verdad. La única defensa es el
checkpoint humano, que hoy revisa sin ninguna refutación preparada. EDAIOS no
define ningún subagente: no hay revisor, ni refutador, ni lente de riesgo. La
práctica externa contrastada en RFC-0003 (gentle-ai; episodio Vanishing Gradients
2026-07-30) converge en el mismo mecanismo: agentes cuyo único trabajo es intentar
demostrar que el cambio se equivoca, con presupuesto acotado y sin autoridad de
aprobación.

## Decisión

Se crean agentes revisores como fuentes canónicas versionadas en
`.specify/agents/`, proyectadas a las superficies de agente por
`tools/publishing/sync_spec_kit_integrations.py` como **segundo namespace del mundo
cerrado AGENT-PARITY**: mismas reglas que los comandos Spec Kit — proyección
byte-idéntica, pin sha256 en el lock, deriva y huérfanos fallan el gate. Queda
prohibido crear superficies de agente (`.claude/agents/`, skills equivalentes) a
mano fuera de la proyección.

Alcance inicial: dos agentes, no cuatro.

- `edaios.refutador` — intenta refutar cada PASS del Constitution Check y cada
  claim FR/SC del plan y la spec, con evidencia concreta de archivo y línea;
- `edaios.lente-riesgo` — busca fail-open e inversiones de autoridad
  (derivado que gobierna a su fuente, control debilitado, superficie no gobernada).

Contrato de los agentes, obligatorio en sus fuentes: mandato de solo lectura;
puerta de precisión (reportar solo defectos defendibles con evidencia — un falso
positivo cuesta un ciclo completo de corrección); presupuesto de una sola pasada
exhaustiva por revisión; y regla de sobre de retorno (la salida final es texto con
los hallazgos, nunca una llamada a herramienta).

Los hallazgos se materializan en `review/findings.md` dentro de la feature, con
severidad y estado por hallazgo. `spec_kit_gate.py` valida su estructura siempre y
exige su existencia para `tipo_cambio` estructural desde la fase analyze.

La autoridad no cambia: los agentes preparan la refutación que el humano lee antes
de firmar. El único aprobador sigue siendo humano (`approval_actor_type: "human"`).
Ningún hallazgo aprueba ni rechaza nada por sí mismo.

## Alternativas

- cuatro lentes más refutador y jueces ciegos (modelo gentle-ai completo):
  rechazada por ahora; sobredimensiona la atención de un mantenedor único, que es
  el recurso escaso que la puerta de precisión protege;
- gate que ejecute agentes LLM: rechazada; los gates son deterministas y de
  librería estándar — un gate valida el artefacto de hallazgos, no ejecuta la
  revisión;
- superficies de agente escritas a mano por herramienta: rechazada; sería
  exactamente la deriva que AGENT-PARITY existe para impedir.

## Consecuencias

Todo cambio estructural llega al checkpoint humano con una refutación preparada y
trazable. El costo es un paso adicional en analyze y el mantenimiento de dos
fuentes de agente bajo el lock. Si la práctica demuestra valor, ampliar lentes será
una enmienda menor de este ADR.

## Evidencia y frontera del claim

Evidencia: admisión de no-verificabilidad del Constitution Check en el propio
gate; ausencia total de subagentes en el árbol actual; convergencia externa
documentada en RFC-0003. Frontera: este ADR no introduce runtime ni orquestador en
Core; no garantiza que la refutación encuentre todos los defectos; no delega
aprobación alguna en agentes.

## Aprobación

Principal Architect · 2026-08-01 · aprobación humana expresa del Owner en sesión
de trabajo: plan de evolución aprobado y orden explícita de continuar tras
revisión del resumen de decisiones. Borrador preparado por IA en la misma sesión.
