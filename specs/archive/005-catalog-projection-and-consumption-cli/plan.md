# Plan técnico · Catálogos compilados y CLI de consumo

## Contexto y decisión

Con ocho decisiones y una genealogía multi-iniciativa, los catálogos editados a
mano colisionan en cada alta concurrente, y el conocimiento distribuido en el
wheel carece de punto de entrada shell. ADR-0007 convierte los catálogos en
proyecciones compiladas (patrón `FND-PROJECTION`); ADR-0008 expone la
superficie CLI de consumo read-only como paridad del contrato Python.

Alternativas descartadas:

1. verificación cruzada sin compilador: conserva la doble captura del hecho;
2. índice central autoritativo: invierte Git-first;
3. `impact()` dentro del gate SDD: el gate permanece sin dependencias y el
   impacto informa, no decide.

## Materialización

1. `tools/publishing/compile_catalogs.py`: colecta ADR/RFC, valida cabeceras
   canónicas, estados y unicidad; renderiza ambos catálogos; `--check` para el
   gate `CATALOG-PROJECTION` registrado en `.specify/gates.json`.
2. `edaios-core kos list|get` sobre `KnowledgeClient` y
   `edaios-core query find|impact|neighborhood` sobre `QueryEngine`, con sobre
   `edaios.cli-output/v1` y `claim_boundary` en cada salida.
3. Claims `catalog-projection` y `consumption-cli` en `claim-surface.json` con
   tests y markers resolubles.
4. Despinneo del catálogo en `day_zero_demo_check`: la genealogía sellada
   0001..0006 pasa de igualdad exacta a prefijo obligatorio con ids únicos y
   ordenados.
5. Regenerar catálogos y demo; ejecutar tests y gates completos.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. Conocimiento | PASS | La autoridad queda en los documentos ADR/RFC; el catálogo es vista derivada. |
| II. Spec | PASS | Esta feature declara contrato y criterios; ADR-0007/0008 preceden la implementación. |
| III. Decisión | PASS | Dos ADR aceptados autorizan proyección y superficie CLI. |
| IV. Fuentes | PASS | El compilador lee metadatos explícitos; los conteos derivan de filas, no de literales. |
| V. Vistas | PASS | Catálogos y demo se regeneran desde fuentes con verificación de drift. |
| VI. Firma | PASS | La instrucción humana expresa autoriza ejecutar estos pendientes; la CLI no firma ni acepta. |
| VII. Privacidad | N/A | Sensibilidad T0: metadatos de gobierno y consultas locales, sin datos ni PII. |

Constitucion verificada: 1.0.0 · sha256:d57078593e5a78bb302e45cea9f5cc5d581be0c6ab8cbb8c751435febd5fb327

## Gate Impact

- `CATALOG-PROJECTION` (nuevo): documento↔catálogo sin drift, fail-closed.
- `TRACEABILITY`: verifica ADR-0007/0008 resolubles fila↔archivo↔Estado.
- `CLAIM-SURFACE`: dos claims enforced nuevos con markers demostrados.
- `CORE-BASE-DEMO`: catálogo como prefijo sellado + gates visibles en paridad.
- `SDD-CONTRACT`, `TEST`, `VALIDATE`: cobertura FR→tareas y suite completa.

## Impacto y reversa

- Arquitectura: media; agrega una proyección y una superficie read-only sin
  tocar autoridad, harnesses ni distribución.
- Datos/IA/privacidad: sin cambio material; consultas locales T0.
- Blast radius: gobierno, gates, CLI, claims, demo y tests.
- Reversa: revertir el commit restaura catálogos manuales y CLI previa; no hay
  estado externo ni migración.
