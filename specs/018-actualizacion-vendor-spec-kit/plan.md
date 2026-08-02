# Plan técnico · Actualización del vendor Spec Kit a 0.15.1

## Contexto técnico

La evaluación (SRC-002) verificó compatibilidad a nivel de código y dejó la
lista exacta de acoplamiento (SRC-003). El CLI global del owner está en
0.12.11 y `uv` permite aislar 0.15.1 para el sandbox (SRC-004). ADR-0022
está Aceptado con las dos posturas: events verificados empíricamente en el
sandbox (sin flag ni superficie en 0.15.1) e interoperar sin adoptar.

## Decisión de implementación

1. **Pin** — `SPECKIT_VERSION_PINNED = "0.15.1"` (spec_kit.py) y
   `SPEC_KIT_VERSION = "0.15.1"` (sync) + regeneración del lock.
2. **Fixtures** — las aserciones de versión en
   `test_memory_adapter_and_setup.py` y `test_working_memory.py` pasan a
   0.15.1.
3. **Manifiestos** — piso `">=0.15.1"` en preset.yml, extension.yml,
   edaios-delivery.yml y bundle.yml.
4. **Inyección** — precheck a `>=0.15.1`; la verificación de events es
   empírica en el sandbox (FR-002): el flag anunciado no existe en el CLI
   real y la superficie no se materializa.
5. **Docs con claim de versión** — OVERVIEW.md, bundle/README.md, demo
   config (+ regeneración del HTML) y CURRENT_STATE.
6. **Sandbox de aceptación (FR-003)** — directorio temporal con git init +
   shim de PATH: un `specify` que ejecuta
   `uvx --from git+https://github.com/github/spec-kit.git@v0.15.1 specify`;
   correr `inject-consumer.sh` completo contra el sandbox; verificar
   ausencia de `.specify/events.py` y de hooks de events; crear una feature
   mínima conforme y correr el gate sembrado con
   `--profile consumer-release`; archivar versiones y salidas en
   `evidence/sc-002-sandbox.json`.
7. **Revisión adversarial (v3)** — ambos subagentes antes del cierre.

## Alternativas descartadas

- actualizar el CLI global del owner desde la sesión: acto del owner sobre
  su sistema; el sandbox aislado prueba lo mismo sin tocarlo;
- omitir el sandbox por la verificación de lectura: ADR-0003 exige evidencia
  propia de ejecución para aceptar un perfil de vendor;
- mitigar events con un flag no verificado: el sandbox refutó su existencia;
  una superficie que no se materializa no se mitiga — se vigila (ADR-0022).

## Estructura afectada

```text
core/framework/extensions/sdd-adapter/src/edaios_sdd_adapter/spec_kit.py
tools/publishing/sync_spec_kit_integrations.py  (+ lock regenerado)
core/framework/tests/{test_memory_adapter_and_setup,test_working_memory}.py
core/framework/extensions/sdd-adapter/spec-kit/{preset/preset.yml,extension/extension.yml,workflow/edaios-delivery.yml,bundle/bundle.yml,bundle/README.md}
core/framework/extensions/sdd-adapter/{inject-consumer.sh,OVERVIEW.md}
docs/demos/edaios-operating-system.config.json (+ HTML regenerado)
program-office/context/CURRENT_STATE.md
specs/018-actualizacion-vendor-spec-kit/       (artefactos + findings)
```

## Estrategia de pruebas

Suites completas con fixtures actualizados; grep de claims vigentes de
0.12.11 (debe quedar solo historia/procedencia archivada); el sandbox como
prueba de ejecución de la cadena completa de inyección + gate.

## Despliegue y reversa

Push por la superficie CI vigente. Reversa: commit que restaura el pin y el
lock (el sandbox es efímero).

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | ADR-0022 y la evaluación preceden todo cambio de pin. |
| II. Spec antes que artefacto | PASS | Esta spec y plan preceden las constantes y el sandbox. |
| III. El canon crece por decisión | PASS | El pin cambia solo por ADR (PLB-006 regla 3); posturas decididas, no implícitas. |
| IV. Cero cifras sin fuente | PASS | Versiones, líneas de acoplamiento y estado del CLI con fila SRC fechada. |
| V. Una fuente, muchas vistas | PASS | El pin vive en dos constantes declaradas y el lock se regenera; docs citan, no duplican contratos. |
| VI. La IA consume; el humano firma | PASS | La orden expresa del owner materializa ADR-0022; el CLI global queda en sus manos. |
| VII. Privacidad por diseño | PASS | T0; el sandbox es efímero y sin datos personales. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `AGENT-PARITY`: lock regenerado con la versión nueva (impacto principal).
- `TEST`: fixtures de versión actualizados.
- `CORE-BASE-DEMO`: config y HTML con el claim nuevo.
- `CATALOG-PROJECTION`/`TRACEABILITY`: ADR-0022 proyectado.
- Resto: sin cambio de contrato; deben permanecer verdes.

## Impactos

- **Arquitectura/Ontología:** sin cambio; la frontera Adopt-or-Adapt se
  conserva.
- **Datos/privacidad:** T0.
- **Costo:** descarga aislada de 0.15.1 para el sandbox; efímera.
- **Blast radius:** constantes de pin, lock, 4 manifiestos, script de
  inyección, docs y fixtures.
