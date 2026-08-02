# Plan técnico · Cierre de contratos resolubles

## Contexto técnico

KOM-VR-02 deriva su dominio de tipos raspando la tabla Markdown de la ontología
con una regex que captura también la primera columna de la tabla de relaciones
(SRC-002): el dominio efectivo hoy es 38 tokens, no 28, y `tipo: governs` pasa.
La fila `kom` del registro de controles cita un archivo de tests inexistente en
sus dos copias (SRC-003) y ningún check resuelve esos punteros. Seis KOs de
Foundation citan en prosa archivos de la genealogía anterior (SRC-004).
ADR-0018 (Aceptado) fija el mecanismo: el contrato ejecutable declara las
entidades; el Markdown conserva la autoridad; la correspondencia se verifica
bidireccionalmente y por sección.

## Decisión de implementación

1. **Dominio de entidades ejecutable** —
   `core/framework/core/profiles/governance-grammar.json` gana
   `"entities": [28 ids]` (los de la sección `## Entidades`, SRC-005).
   `tools/validation/kom_gate.py`:
   - parsea la ontología por secciones (`## Entidades`, `## Relaciones`) y
     extrae la primera columna backticked de cada tabla con una regex que
     admite guiones bajos (la actual los excluye y por eso `derives_from` y
     `verified_by` escapaban);
   - verifica igualdad de conjuntos en ambas direcciones:
     `grammar["entities"]` ↔ filas de Entidades y claves de
     `grammar["relations"]` ↔ filas de Relaciones; cualquier diferencia es
     error de gate;
   - KOM-VR-02 valida `tipo` contra `set(grammar["entities"])`; el raspado
     global desaparece.
2. **Punteros de controles resolubles** —
   `tools/validation/core_conformance_check.py` gana, junto a la comparación de
   copias existente, la resolución de `implementation` y `tests` de cada
   control contra el árbol (patrón de `claim_surface_check.py:126-130`); path
   inexistente → fallo. La fila `kom` pasa a citar
   `core/framework/tests/test_governance_conformance.py` en ambas copias
   (fuente pública y recurso empaquetado, que deben seguir byte-idénticos). El
   módulo empaquetado `edaios_conformance/profiles.py` no cambia: valida
   controles en contextos instalados sin árbol de Core; la resolución de paths
   del monorepo pertenece al gate del monorepo.
3. **Linaje en prosa resoluble** — `kom_gate.py` valida las líneas
   `**Deriva de:**` del cuerpo: cada token backticked `*.md` debe (a) resolver
   como ruta relativa a `core/foundation/` si contiene `/`, (b) resolver por
   nombre exacto único vía rglob si es nombre suelto, o (c) estar anotado en la
   misma línea con `(histórico` — y entonces NO debe resolver (un histórico
   vivo es contradicción). Correcciones al corpus (SRC-004, SRC-006):
   `FOUNDATION_STRATEGY.md` → `strategy/README.md` (resolución de renombre a
   KO-STRATEGY vivo); `EDAIOS_FOUNDATION_SPECIFICATION.md` y
   `FOUNDATION_DOCUMENT_STANDARD.md` → anotados `(histórico, genealogía
   anterior)` sin inventar sucesor.
4. **Regresiones** — en `core/framework/tests/test_governance_conformance.py`
   (donde ya cargan `kom_gate` y los fixtures KOM): KO `tipo: governs` falla;
   mismatch entidad-extra y entidad-faltante fallan en ambas direcciones;
   registro con `tests` no resoluble falla; prosa fantasma falla; histórico que
   resuelve falla; corpus real verde.

## Alternativas descartadas

- compilar la gramática desde el Markdown: reubica la fragilidad en un
  compilador (rechazada en ADR-0018);
- corregir solo la regex: deja el dominio implícito y sin contrato inverso;
- resolver paths de controles dentro de `edaios_conformance/profiles.py`:
  rompería la validación en consumidores instalados sin árbol de Core;
- decidir sucesores para las dos referencias históricas ambiguas: inventaría
  linaje (Principio VI); la anotación es reversible por el owner.

## Estructura afectada

```text
core/framework/core/profiles/governance-grammar.json
core/framework/modules/conformance-core/src/edaios_conformance/resources/control-registry.json
core/framework/core/profiles/control-registry.json
tools/validation/kom_gate.py
tools/validation/core_conformance_check.py
core/foundation/{identity,values,vision,mission,manifesto}/README.md
core/foundation/constitution/CONSTITUTION_SCHEMA.md
core/framework/tests/test_governance_conformance.py
specs/012-cierre-de-contratos-resolubles/
```

## Estrategia de pruebas

Regresiones negativas por cada contrato nuevo (tipo inválido, mismatch en cada
dirección, path de control no resoluble, prosa fantasma, histórico resoluble) y
el corpus vigente como positivo. `scripts/test.sh`, `scripts/validate.sh` y los
14 gates pre-push cierran (SC-005). Los KOs editados no cambian de estado
(Ratificado permanece); si KOM-VR-10 objetara la edición de cuerpo, el hallazgo
se trata como bloqueo y se consulta al owner antes de debilitar nada.

## Despliegue y reversa

Sin despliegue remoto propio: el push del cierre viaja por la superficie CI de
la feature 011. Reversa: commit posterior que restaura gramática, registro y
prosa; no se reescribe `main`.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | ADR-0018 y RFC-0003 preceden el cambio; la ontología conserva autoridad. |
| II. Spec antes que artefacto | PASS | spec, checklist y este plan existen antes de tocar gramática o gates. |
| III. El canon crece por decisión | PASS | ADR-0018 Aceptado habilita; no se añade entidad ni relación alguna. |
| IV. Cero cifras sin fuente | PASS | 38/28/12, filas y líneas exactas registradas en evidence/sources.md. |
| V. Una fuente, muchas vistas | PASS | El MD sigue siendo fuente; el JSON es contrato verificado bidireccionalmente; copias del registro byte-idénticas. |
| VI. La IA consume; el humano firma | PASS | Sucesores ambiguos se anotan como históricos, no se inventan; el cierre lo firma el owner. |
| VII. Privacidad por diseño | PASS | T0; sin datos personales ni ruta LLM. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `KOM`: cambio principal — dominio desde grammar, verificación bidireccional,
  prosa resoluble.
- `CORE-CONFORMANCE`: gana resolución de punteros de controles; copias del
  registro deben seguir byte-idénticas.
- `TEST`: regresiones nuevas en la suite de gobierno.
- `FND-PROJECTION`, `CATALOG-PROJECTION`, `AGENT-PARITY`, `SDD-CONTRACT`,
  `MONOREPO-STRUCTURE`, `TRACEABILITY`, `BASELINE-SURFACE`, `CLAIM-SURFACE`,
  `CORE-DISTRIBUTION`, `CORE-RELEASE-SEAL`, `CORE-BASE-DEMO`, `VALIDATE`: sin
  cambio de contrato; deben permanecer verdes antes y después.

## Impactos

- **Arquitectura:** ninguna pieza nueva; endurecimiento de dos validadores.
- **Ontología:** sin cambio semántico (28 entidades, 12 relaciones); cambia el
  mecanismo de verificación, decidido por ADR-0018.
- **Datos/privacidad:** T0.
- **IA:** sin ruta LLM.
- **Costo:** solo tiempo de gates local/CI.
- **Blast radius:** gramática, registro (2 copias), 2 validadores, 6 KOs de
  Foundation (solo líneas de prosa), tests.
