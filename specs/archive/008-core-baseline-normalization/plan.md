# Plan técnico · Normalización del baseline Core 3.1.0

## Contexto técnico

El nuevo `main` contiene la superficie funcional validada de Core 3.1.0, pero
el handoff y las vistas aún dependen de la feature 006 y de un candidato 3.0
retirado. El cambio corrige fuentes y derivados sin tocar Foundation ni la API
del kernel.

## Decisión de implementación

1. Registrar ADR-0012/0013 y mover el handoff canónico a 008, preservando 007
   como último cierre.
2. Cerrar 006 por sustitución y retirar sus manifests/targets ligados a la
   genealogía anterior; actualizar 007 para que el bloqueo de promoción quede
   resuelto por ADR-0012.
3. Generalizar el checker de release: el default sin manifest es
   `baseline-no-candidate`; los candidatos se validan solo con path explícito,
   seguro y comprometido.
4. Reescribir las fuentes operativas y regenerar catálogos y HTML.
5. Añadir `bitbucket-pipelines.yml` como delegación mínima a `scripts/ci.sh` y
   cubrirla con tests/topología.
6. Validar el snapshot como raíz única portable y crear `edaiosv/main` solo si
   el remoto continúa vacío; cualquier tag queda fuera de este bootstrap.

## Alternativas descartadas

- conservar 006 activa: mantiene un bloqueo sobre refs inexistentes;
- borrar todo el tooling de release: pierde conocimiento y controles reusables;
- editar el HTML directamente: rompería source-first;
- crear Flink dentro del Core: viola la frontera de consumidor externo;
- tag antes de CI: convierte intención en claim no observado.

## Estructura afectada

```text
governance/archive/adr/ADR-0012-*.md
governance/ADR-0013-*.md
specs/006-core-seal-and-release-cutover/
specs/archive/007-agent-working-memory-and-derived-index/
specs/archive/008-core-baseline-normalization/
.specify/feature.json
tools/{publishing,validation}/
core/framework/tests/
README.md
program-office/context/
docs/
bitbucket-pipelines.yml
```

## Estrategia de pruebas

1. Spec Kit y trazabilidad sobre handoff 004→007→008.
2. Unit tests del release gate sin candidato y con manifest explícito.
3. Test de pipeline: un único runner `scripts/ci.sh`, sin duplicar comandos.
4. Regeneración config→HTML y prueba de interacciones existentes.
5. Tests, validate y CI completos desde clon limpio.
6. Clon limpio de un solo root y observación de `edaiosv/main` sin tags.

## Despliegue y reversa

La implementación se materializa como el único root de `edaiosv/main`. La
publicación usa un lease que exige destino vacío; si aparece otra ref, se
detiene. Después del bootstrap, cualquier corrección crea un commit nuevo y no
reescribe `main`. Sin CI/protección observadas no se crea tag ni release.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | ADR-0013 y feature 008 preceden la mutación de fuentes y remoto. |
| II. Spec antes que artefacto | PASS | Contrato, checklist y plan existen antes de implementar. |
| III. El canon crece por decisión | PASS | ADR-0013 acepta la raíz portable y el hogar canónico nuevo. |
| IV. Cero cifras sin fuente | PASS | Root, tests, gates y refs están fechados en `evidence/sources.md`. |
| V. Una fuente, muchas vistas | PASS | Demo y catálogos se regeneran desde config y documentos canónicos. |
| VI. La IA consume; el humano firma | PASS | La instrucción humana autoriza; CI y gates solo verifican. |
| VII. Privacidad por diseño | PASS | T0 técnico sin datos, PII o transporte de memoria. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `CATALOG-PROJECTION`: incorpora ADR-0013.
- `SDD-CONTRACT`: cambia handoff y agrega feature 008.
- `TRACEABILITY`: retira el estado operativo 006 y conserva referencias resolubles.
- `MONOREPO-STRUCTURE`: admite la configuración CI raíz.
- `CORE-RELEASE-SEAL`: deja de depender del candidato 3.0.
- `CORE-BASE-DEMO`: deriva baseline 3.1 instalado y feature 008.
- `TEST`: cubre gate, pipeline, handoff y vistas.
- `VALIDATE`: ejecuta todas las superficies sobre la nueva branch.

## Impactos

- Arquitectura: normalización de control plane y release, sin API nueva.
- Ontología/Foundation: sin cambios.
- Datos/privacidad: T0; sin datos institucionales.
- IA: sin nueva inferencia o autoridad.
- Costo: CI remoto sujeto al plan del proveedor; no se infiere disponibilidad.
- Blast radius: gobierno, handoff, tooling, docs, demo y configuración CI.
