# ADR-0020 — Entrega gobernada del gate SDD al consumer

**Estado:** Aceptado
**Fecha:** 2026-08-01
**Owner:** Principal Architect

## Contexto

RFC-0002 dejó dos preguntas abiertas tras ADR-0016: cómo se entrega
`spec_kit_gate.py` a un consumer (hoy: copia vendorizada a mano con sidecar de
procedencia, verificado en `data-kcd2026`), y cómo selecciona el gate su modo
estructural (hoy: allowlist por nombre de perfil). El programa declara como
siguiente prioridad un piloto real gobernado (`program-office/context/NEXT_ITERATION.md`),
y RFC-0003 la recoge como feature 015: el primer consumer real con evidencia y la
primera entrada del Value Ledger.

## Decisión

**Entrega: opción A de RFC-0002.** `edaios_sdd_adapter` incorpora `seed_gate()`
junto a `seed_speckit_constitution`: copia el gate al consumer con sidecar de
procedencia (versión del paquete, digest sha256 del gate, fecha), es idempotente, y
se niega a sobrescribir una copia divergente sin confirmación explícita — la deriva
se reporta, no se pisa. La copia del consumer queda gobernada por la versión del
adapter en lugar de por disciplina manual.

**Selección de modo estructural: se conserva la allowlist por nombre, con gatillo
de revisión.** Formalizar un control `core-monorepo` exige un cambio atómico de
seis puntos de verificación más el módulo empaquetado y la cobertura exacta del
`control-registry.json`; con un único consumer, ese costo no compra seguridad
adicional — la allowlist es fail-closed. El gatillo: cuando exista un segundo
consumer conforme, este punto se reabre como enmienda de este ADR (la opción 1 de
RFC-0002 queda documentada como camino preferente futuro).

Con la aceptación de este ADR, RFC-0002 pasa a Ratificado con
`resolved_by: ADR-0020`.

## Alternativas

- opción B de RFC-0002 (empaquetar el gate y re-cablear ~8 sitios de Core):
  rechazada por ahora; toca el corazón del self-gating de Core para eliminar una
  copia que la opción A ya deja versionada y trazada;
- opción C (statu quo vendorizado): rechazada; es la fragilidad que motivó el RFC;
- resolver también el control `core-monorepo` ahora: rechazada; cambio atómico de
  alto costo sin segundo consumer que lo justifique.

## Consecuencias

El consumer real de la feature 015 recibe el gate por vía gobernada y su
procedencia es verificable. Queda una copia por consumer — trade-off aceptado y
declarado. El retiro del sidecar manual de `data-kcd2026` ocurre en la feature 015
al re-sembrar con `seed_gate()`.

## Evidencia y frontera del claim

Evidencia: RFC-0002 (opciones y trade-offs), vendorización actual en
`data-kcd2026` documentada allí, prioridad de piloto real en NEXT_ITERATION.
Frontera: este ADR no afirma adopción organizacional ni federación con dos
attachments reales; no empaqueta el gate en el wheel; no cambia perfiles ni
controles.

## Aprobación

Principal Architect · 2026-08-01 · aprobación humana expresa del Owner en sesión
de trabajo: plan de evolución aprobado y orden explícita de continuar tras
revisión del resumen de decisiones. Borrador preparado por IA en la misma sesión.
