# Plan técnico · Estado SDD legible por máquina

## Contexto técnico

`feature_context.py` ya implementa la precedencia explícita > local > canónica
(SRC-002) pero no emite estado estructurado y no maneja idle. El phase-dag
canónico es una cadena lineal (SRC-003). Las fases persistidas en el corpus
son cinco (SRC-004); la fase checklist no deja marcador y se infiere del
artefacto. ADR-0016 excluye el bookkeeping SDD del CLI de consumo: el hogar es
esta herramienta de operaciones.

## Decisión de implementación

1. **Subcomando `status`** en `tools/operations/feature_context.py`:
   - flags: `--feature` (explícito opcional), `--profile`
     (`core-release`/`consumer-release`, pass-through al gate) y `--no-gate`
     (omite `blockedReasons` para respuesta inmediata).
   - salida única JSON, schema congelado `edaios.sdd.status/v1`:
     `{schema, source, feature, estado, fase, nextRecommended, blockedReasons}`;
     en idle: `feature: null`, `source: "idle"`, `nextRecommended: "idle"`,
     `blockedReasons: []`.
   - resolución: `resolve()` actual; `FeatureContextError` por ausencia de
     selector y el caso `active_feature: null` mapean a idle, no a error.
2. **Derivación del token** — el DAG se lee del recurso canónico (SRC-003) y
   se lineariza por dependencias; el mapeo fase→fase-completada es
   `{specified: specify, clarified: clarify, planned: plan, tasked: tasks,
   implemented: implement}` (dominio observado, SRC-004; fase fuera del
   dominio → error fail-closed). `nextRecommended` = siguiente id de la
   cadena, con dos reglas de artefacto: `clarified` recomienda `plan` solo si
   `checklists/requirements.md` existe (si no, `checklist`); estado `Cerrado`
   + `implemented` → `idle`. Con `blockedReasons` no vacía el token
   retrocede a la fase completada actual (corregir antes de avanzar,
   Clarifications).
3. **`blockedReasons`** — subproceso `sys.executable
   tools/validation/spec_kit_gate.py <root> --feature <dir> [--profile p]`;
   se capturan las líneas `[FAIL]` (prefijo removido). El gate sigue siendo
   el único juez; status solo transporta sus filas.
4. **Línea de ruteo** en las 8 fuentes `.specify/commands/speckit.*.md` +
   regeneración con `tools/publishing/sync_spec_kit_integrations.py` (lock
   sha256 nuevo, AGENT-PARITY verde).
5. **Regresiones** en `core/framework/tests/test_sdd_status.py` (patrón
   load_module): idle v3; planned→tasks; clarified con/sin checklist;
   Cerrado→idle; fase desconocida falla; gate rojo → blockedReasons no vacía y
   token en fase actual (fixture bajo `--profile consumer-release` para no
   arrastrar el bookkeeping del monorepo, ADR-0016); corpus real → vacía.

## Alternativas descartadas

- emitirlo desde `edaios-core`: ADR-0008/0016 lo excluyen del CLI de consumo;
- inventar un vocabulario de tokens propio: el dominio ya existe en el
  phase-dag canónico; duplicarlo crearía una segunda fuente;
- inferir la fase de la prosa de spec.md: exactamente el anti-patrón que esta
  feature elimina;
- ejecutar el gate in-process importándolo: acopla los ciclos de vida de dos
  herramientas; el subproceso conserva al gate como juez independiente.

## Estructura afectada

```text
tools/operations/feature_context.py               (subcomando status)
.specify/commands/speckit.*.md                    (línea de ruteo, 8 fuentes)
.claude/commands/ · .agents/skills/ · .github/prompts/ · preset  (regenerados)
.specify/integrations.lock.json                   (lock regenerado)
core/framework/tests/test_sdd_status.py           (regresiones)
specs/013-sdd-status-maquina/                     (artefactos)
```

## Estrategia de pruebas

Regresiones deterministas del mapeo (SC-001), negativa de gate rojo y positiva
del corpus (SC-002), AGENT-PARITY tras regenerar (SC-003), suites completas y
14 gates (SC-004).

## Despliegue y reversa

El push viaja por la superficie CI de specs/011. Reversa: commit posterior que
retira el subcomando y la línea de las fuentes y regenera proyecciones.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | RFC-0003 y los ADR trazados preceden el cambio; el DAG canónico es la fuente del dominio. |
| II. Spec antes que artefacto | PASS | spec, checklist y este plan existen antes de tocar la herramienta. |
| III. El canon crece por decisión | PASS | Carril ya decidido (ADR-0002/0016); sin frontera nueva. |
| IV. Cero cifras sin fuente | PASS | Dominio de fases, cadena del DAG y comportamiento idle con fila SRC fechada. |
| V. Una fuente, muchas vistas | PASS | Token derivado del phase-dag único; superficies regeneradas por el sync con lock. |
| VI. La IA consume; el humano firma | PASS | El estado informa; no aprueba, no promueve, no cierra. |
| VII. Privacidad por diseño | PASS | T0; metadatos de repositorio; sin ruta LLM. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `AGENT-PARITY`: fuentes editadas + lock regenerado (impacto principal).
- `SDD-CONTRACT`: sin cambio de contrato de features; debe seguir verde.
- `TEST`: regresiones nuevas.
- `FND-PROJECTION`, `CATALOG-PROJECTION`, `KOM`, `MONOREPO-STRUCTURE`,
  `TRACEABILITY`, `BASELINE-SURFACE`, `CORE-CONFORMANCE`, `CLAIM-SURFACE`,
  `CORE-DISTRIBUTION`, `CORE-RELEASE-SEAL`, `CORE-BASE-DEMO`, `VALIDATE`: sin
  cambio; deben permanecer verdes.

## Impactos

- **Arquitectura:** una superficie de lectura nueva en tooling de
  operaciones; cero piezas de runtime.
- **Ontología:** sin cambio.
- **Datos/privacidad:** T0.
- **IA:** los agentes consumen el token; ninguno decide con él más de lo que
  el gate ya decidió.
- **Costo:** un subproceso de gate por consulta (evitable con `--no-gate`).
- **Blast radius:** una herramienta, 8 fuentes + proyecciones, un test.
