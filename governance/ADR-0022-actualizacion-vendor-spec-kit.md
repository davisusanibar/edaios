# ADR-0022 — Actualización del perfil operativo Spec Kit a 0.15.1

**Estado:** Aceptado
**Fecha:** 2026-08-02
**Owner:** Principal Architect

- Amends: ADR-0002

## Contexto

El vendor GitHub Spec Kit está pineado a 0.12.11 (delivery gobernado por
ADR-0002 y perfil consumer por ADR-0016; frontera Adoptar-o-Adaptar de
PLB-006, regla 3: cambiar el pin exige ADR). Upstream va en
0.15.1 con 19 releases de distancia y cadencia de ~1 minor por semana. La
evaluación técnica registrada en specs/018 verificó a nivel de código de
ambos tags: cero rupturas en los cuatro esquemas que EDAIOS consume
(preset/extension/workflow/bundle, schema 1.0) y en las cinco invocaciones
del CLI de `inject-consumer.sh`; los cambios upstream son aditivos y de
endurecimiento de seguridad (HTTP acotado, TOCTOU, symlinks, eliminación de
shell). Dos novedades exigen postura: la capa de runtime-events que
`specify init` 0.15.x siembra en el consumidor, y el ecosistema de presets de
gobernanza upstream (Autonomous Run Governance, v0.3.3) con `verdict_input`
para aprobaciones no interactivas.

## Decisión

Se actualiza el perfil operativo del vendor GitHub Spec Kit de 0.12.11 a
**0.15.1** por el carril Adoptar-o-Adaptar (PLB-006, supersesión
PAT-003). El pin se actualiza en un solo cambio: `SPECKIT_VERSION_PINNED`,
`SPEC_KIT_VERSION` con lock regenerado, fixtures de test, piso
`>=0.15.1` en los cuatro manifiestos vendorizados, precheck y docs.

Sobre la capa de runtime-events anunciada por upstream para 0.15.x: el
sandbox de aceptación verificó que `specify init` 0.15.1 no expone flag de
events y que la ruta de inyección claude no materializa superficie alguna
(sin `.specify/events.py`, sin configuración de hooks). No se requiere
mitigación en la inyección; la vigilancia queda declarada: si una línea
futura materializa esa superficie, su gobierno precede a su adopción. Los consumers ya
inyectados (`kcd-001`) se re-proyectan (constitución + lock) en su próximo
toque; el gate solo se re-siembra vía `seed_gate`.

Frente al preset upstream "Autonomous Run Governance" se decide
**interoperar sin adoptar**: puede instalarse detrás del adapter con
delivery mode restringido a `LocalImplementation` (sus modos
`PublishPR`/`MergeAndSync` chocan con el Artículo VI); el preset EDAIOS
conserva prioridad 5 y los hooks `edaios.gate` permanecen `optional: false`.
La firma humana vive en artefactos EDAIOS y nunca se delega a un
`verdict_input` de workflow. La diferenciación EDAIOS — ontología + gates
sobre artefactos + claim surface — no se delega.

La aceptación exige evidencia propia (PLB-006): inyección y
`consumer-release` en verde contra un consumer sandbox con `specify` 0.15.1.

## Alternativas

- permanecer en 0.12.11: renuncia a los fixes de seguridad del borde de
  inyección y agranda el drift semanalmente; rechazada;
- adoptar la capa de events y gobernarla: superficie ejecutable nueva sin
  necesidad demostrada; diferible hasta que un consumer la requiera;
- adoptar el preset de gobernanza upstream: gobierna el proceso del run, no
  el conocimiento ni el claim; redundante en su solape y contradictorio en
  sus modos de entrega remota.

## Consecuencias

El adapter queda como frontera creíble consumiendo el SDD comoditizado
(tesis de RFC-0003). El CLI global del owner puede actualizarse a su ritmo:
los manifiestos con piso `>=0.15.1` declaran el perfil probado y la
inyección compara `specify --version` contra el piso y se detiene por
debajo (fail-closed). Las estampas de versión del consumer declaran el
perfil operativo aceptado (el pin), garantizado por ese piso en la ruta
gobernada; sembrar fuera del script queda fuera del claim. La estampa de versión en consumers ya
inyectados queda desincronizada hasta su re-proyección — deuda declarada,
no silenciosa.

## Evidencia y frontera del claim

Evidencia: evaluación de specs/018 (esquemas y CLI comparados a nivel de
código en ambos tags, releases upstream v0.12.12..v0.15.1, catálogos
comunitarios) y el sandbox de aceptación archivado en su evidencia.
Frontera: este ADR no adopta extensiones upstream nuevas (assess, intent,
OKF), no activa la capa de events, no re-proyecta consumers (ocurre en su
próximo toque) y no afirma compatibilidad con líneas posteriores a 0.15.x.

## Aprobación

Principal Architect · 2026-08-02 · orden humana expresa del Owner en sesión
de trabajo ("Procede con el vendor update") sobre la evaluación técnica
completa presentada. Borrador preparado por IA en la misma sesión.
