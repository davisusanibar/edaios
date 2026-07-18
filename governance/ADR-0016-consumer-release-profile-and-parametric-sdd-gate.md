# ADR-0016 — Perfil consumer-release y gate SDD parametrizable por profile

**Estado:** Aceptado
**Fecha:** 2026-07-17
**Owner:** Principal Architect
**Deriva de:** ADR-0004
**Relaciona:** ADR-0002, ADR-0003

## Contexto

`tools/validation/spec_kit_gate.py` es el self-gate del monorepo de Core: fija los
15 gate-IDs de `gates.json`, exige `specs/tombstones.json` no vacío, un registry de
perfiles bajo `core/framework/core/profiles/`, `dominio ∈ {"core"}` y trazas
resolubles contra `governance/ADR_CATALOG.md`. Esas exigencias son correctas para
certificar Core, pero **acoplan la validación del contrato SDD a la estructura del
árbol de Core**.

Una feature gobernada que vive en el repo de un consumer no puede pasar ese gate sin
**imitar una raíz Core**: importar los 15 gate-IDs, sembrar un tombstone placeholder,
declarar `dominio: core` y arrastrar el catálogo ADR de Core. Verificado
empíricamente: hacer pasar una feature de consumer exigió fabricar contexto
estructural que no describe la salud de la feature —un fake que contradice "cero
ficciones".

El gate ya anticipa la separación: acepta `--profile`, y `load_validation_profile`
resuelve los controles del perfil seleccionado. Pero `main()` **descarta** ese
retorno: el flag valida el registry y no condiciona ni un check. El seam está
construido a medias.

Los checks del gate son de dos naturalezas. ~2/3 son **SDD intrínseco** —frontmatter
completo, compatibilidad estado/fase, Constitution Check con pin vigente, FR/SC,
checklist sin pendientes, cobertura FR→tarea, cierre y matriz SC→evidencia— y valen
para cualquier feature gobernada. ~1/3 es **bookkeeping del monorepo de Core** y solo
tiene sentido en el árbol de Core.

## Decisión

Se divide la verificación del contrato SDD en dos superficies sobre **una sola
implementación**, no dos gates.

1. **Perfil `consumer-release`.** Nuevo perfil de conformidad raíz (`parent: null`),
   con superficie mínima de controles (`sdd-contract`, `claim-surface`). Certifica una
   feature gobernada en cualquier repo, sin exigir la estructura del árbol de Core. La
   monotonía de ADR-0004 se respeta: como corre *menos* controles que `core-release`,
   **no puede ser su hijo** —los hijos solo agregan— sino un perfil **raíz hermano**.
   `validate_registry` extiende su conjunto esperado para incluirlo.

2. **Gate parametrizado por profile.** Se separan en `spec_kit_gate.py` los checks
   intrínsecos de los estructurales, y los estructurales se condicionan a un control
   (`core-monorepo`) presente solo en `core-release`. `main()` **usa** el retorno de
   `load_validation_profile` para activar o apagar los estructurales. Los checks
   intrínsecos son idénticos entre perfiles; los estructurales solo corren bajo
   `core-release`.

3. **`consumer-release` exige** (fail-closed): frontmatter completo y estado/fase
   compatibles; Constitution Check con los 7 principios, veredictos del dominio, sin
   VIOLA y pin vigente contra la constitución **proyectada** por el adapter; FR/SC
   declarados; checklist sin pendientes; cobertura FR→tarea y tareas de cierre; matriz
   SC→evidencia con paths resolubles; spec tipada plana que enlaza `id` y `artifact`;
   fuentes dentro de la raíz del consumer.

4. **`consumer-release` NO exige**: los 15 gate-IDs de Core en `gates.json`,
   `tombstones.json` no vacío, `dominio ∈ {"core"}`, resolución de trazas contra el
   catálogo ADR de Core, ni el handoff `feature.json`. El consumer declara su propio
   conjunto de gates de dominio y su propio dominio; las trazas se validan por formato.

5. **Entrega por el borde, no por el kernel.** El gate parametrizado y el perfil se
   distribuyen por el `sdd-adapter`/bundle (ADR-0003: la interoperabilidad SDD vive en
   `extensions/`, con herramientas pineadas). El consumer corre
   `spec_kit_gate.py . --feature <dir> --profile consumer-release`. La fuente normativa
   sigue en `core/foundation/`.

6. **`consumer-release` se entrega como perfil built-in, no registrado.** Se resuelve
   dentro de `spec_kit_gate.py` sin agregarse a `validation-profiles.json`, porque el
   conjunto `{core-release, initiative-adoption, federation}` está fijado en **seis
   puntos de enforcement** (`baseline_surface_check.py`, `monorepo_structure_check.py`,
   `traceability_check.py`, `core_conformance_check.py`, `spec_kit_gate.py` y el módulo
   empaquetado `edaios_conformance/profiles.py`) y el `control-registry.json` exige
   cobertura exacta de perfiles. Registrar un cuarto perfil rompería esos seis gates a
   la vez. Por eso la selección de modo estructural es **allowlist fail-closed**
   (`profile != "consumer-release"`), no un control `core-monorepo` resuelto desde el
   registry: no se acopla la seguridad del gate a un cambio cross-cutting del kernel.
   Formalizar `core-monorepo` como control de primera clase y registrar el perfil es
   **trabajo de seguimiento** que debe tocar los seis puntos y el módulo empaquetado en
   un solo cambio deliberado, con sus propios contract tests.

## Alternativas

- **Un gate liviano separado en el adapter:** rechazada por deriva —dos
  implementaciones del mismo contrato divergen; una sola con selección por profile no.
- **Flag `--consumer` ad-hoc:** rechazada porque mete un modo en el kernel sin el rigor
  del sistema de perfiles ya existente (ADR-0004).
- **Que el consumer siga imitando una raíz Core:** rechazada porque exige fabricar
  tombstones, `dominio: core` y catálogos —ficción estructural que ningún principio
  autoriza.
- **Debilitar los estructurales de `core-release`:** rechazada; ADR-0004 prohíbe
  debilitar el baseline y vuelve ambiguo qué release está certificado.

## Consecuencias

Un consumer gobierna su feature con el mismo contrato SDD de Core sin volverse un
mini-monorepo Core. Los checks intrínsecos quedan como fuente única y compartida: cero
drift. El `--profile` deja de ser inerte. El pin del Constitution Check ancla contra la
constitución proyectada por el adapter, cerrando el hueco del viejo "pin no aplicable".

Frontera: `consumer-release` certifica **coherencia SDD local**, no adopción ni
conformance de una iniciativa (eso es `initiative-adoption`) ni operación remota. No
confiere autoridad ni aceptación; el cierre sigue exigiendo firma humana (ADR-0005).
El consumer es responsable de sus propios gates de dominio; Core no los conoce ni los
ejecuta.

## Evidencia y frontera del claim

Al aceptarse, contract tests locales deben probar: que `consumer-release` resuelve como
perfil raíz sin debilitar `core-release`; que los checks estructurales se apagan **solo**
bajo `consumer-release` y siguen fail-closed bajo `core-release` (rojo/verde inducido);
y que un frontmatter incoherente (p.ej. estado/fase incompatibles) falla bajo ambos
perfiles. No prueban adopción organizacional, operación remota ni producción.

## Aprobación

Principal Architect · 2026-07-17 · instrucción humana de aceptar ADR-0016 tras revisar el
prototipo en verde: SDD-CONTRACT 366/366 sin regresión, consumer limpio 42/42 bajo
`consumer-release`, el mismo consumer rojo bajo `core-release`, y la suite del gate 12/12.
Se autoriza el perfil `consumer-release` como raíz built-in y el gate parametrizado por
profile con selección estructural fail-closed por allowlist. La formalización de
`core-monorepo` como control de primera clase queda como trabajo de seguimiento (§ Decisión 6),
no habilitado por esta aceptación. La redacción y el prototipo los produjo un agente desde la
spec; la aceptación es del owner humano (Artículo VI, ADR-0005). Merge y push a `main` siguen
requiriendo autorización separada. El catálogo ADR se regenera con
`python3 tools/publishing/compile_catalogs.py --write`, no se edita a mano (ADR-0007).
