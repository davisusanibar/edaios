# Plan técnico · Revisión adversarial preparada

## Contexto técnico

El mundo cerrado de proyección opera para `speckit.*` con lock y detección de
huérfanos (SRC-003). El gate admite que el Constitution Check es declarativo
(SRC-002). El idioma de versionado por schema tipado ya eximió a las v1 de la
matriz de verificación (SRC-006). ADR-0019 está Aceptado.

## Decisión de implementación

1. **Fuentes de agentes** — `.specify/agents/edaios.refutador.md` y
   `.specify/agents/edaios.lente-riesgo.md`, mismo contrato de frontmatter que
   los comandos (id, display_name, description, trigger, short_description,
   default_prompt) y cuerpo ≤450 palabras con: mandato de solo lectura, puerta
   de precisión ("un falso positivo cuesta un ciclo completo"), presupuesto de
   una sola pasada exhaustiva, regla de sobre de retorno (la salida final es
   la tabla de hallazgos como texto) y el contrato de salida (formato de
   `review/findings.md`).
2. **Segundo namespace del sync** — `sync_spec_kit_integrations.py`:
   - fuente `AGENT_SOURCE_DIR = .specify/agents/` (`edaios.*.md`; strays
     fallan);
   - superficies: `.claude/agents/{id}.md` (frontmatter `name`, `description`,
     `tools: Read, Grep, Glob` — solo lectura por construcción),
     `.agents/skills/{id-con-guiones}/SKILL.md` + `agents/openai.yaml`,
     `.github/prompts/{id}.prompt.md`; sin preset (los agentes no viajan en el
     bundle Spec Kit);
   - `managed_files()` cubre los tres espacios nuevos (`edaios.*` /
     `edaios-*`); el lock gana el bloque `agents` (clave aditiva, mismo
     schema).
3. **Contrato de findings en el gate** — `spec_kit_gate.py`:
   - la exigencia de matriz (línea 594) acepta `{v2, v3}`;
   - `review/findings.md`: cuando existe, valida filas
     `| RA-NNN | refutador|lente-riesgo | CRITICAL|HIGH|MEDIUM|LOW |
     abierto|corregido|refutado|aceptado | … | refs |` con refs no vacías, o
     la línea literal `Sin hallazgos:` con justificación; un CRITICAL o HIGH
     `abierto` es FAIL; ids únicos;
   - exigencia de existencia: schema v3 + `tipo_cambio` estructural +
     `fase: implemented`.
4. **Checker de calidad de tests** — `tools/validation/test_quality_check.py`
   (stdlib `ast`): en `core/framework/tests/test_*.py`, todo método `test_*`
   debe contener al menos una aserción (`self.assert*`, `self.fail`, o
   `with self.assertRaises*`); aserciones constantes (`assertTrue(True)`,
   literal en posición de verdad) y tautológicas (`assertEqual(x, x)` con
   AST idéntico) fallan. Se engancha en `scripts/test.sh` tras la suite
   (gate TEST, sin id nuevo).
5. **Comando analyze** — la fuente `speckit.analyze.md` gana el paso de
   invocación de los dos agentes y materialización de `review/findings.md`;
   regeneración de superficies.
6. **Dogfood (SC-004)** — los dos agentes se ejecutan sobre esta misma
   feature; sus hallazgos reales quedan en
   `specs/015-revision-adversarial-preparada/review/findings.md` antes del
   cierre.
7. **Regresiones** — fixture huérfano en superficies de agentes (sync
   `--check` falla); findings con severidad/estado inválido, CRITICAL abierto,
   v3 estructural sin findings; corpus v2 pasa; test sin asserts y
   tautológico fallan el checker; suite vigente pasa.

## Alternativas descartadas

- cuatro lentes + jueces ciegos: sobredimensiona la atención del mantenedor
  único (ADR-0019);
- gate que ejecute agentes LLM: los gates son deterministas; validan el
  artefacto, no ejecutan la revisión;
- exigencia de findings por fecha o número de feature: constante congelada;
  el schema tipado v3 es el idioma vigente de versionado de contrato;
- checker de tests con cobertura/mutación: dependencias fuera de stdlib;
  el `ast` cubre la clase de fallo señalada (asserts vacíos/tautológicos).

## Estructura afectada

```text
.specify/agents/edaios.{refutador,lente-riesgo}.md   (fuentes nuevas)
tools/publishing/sync_spec_kit_integrations.py        (namespace agentes)
.claude/agents/ · .agents/skills/edaios-* · .github/prompts/  (proyectadas)
.specify/integrations.lock.json                       (lock con agents)
tools/validation/spec_kit_gate.py                     (v3 + findings)
tools/validation/test_quality_check.py                (nuevo)
scripts/test.sh                                       (enganche del checker)
.specify/commands/speckit.analyze.md                  (paso adversarial)
core/framework/tests/test_governance_conformance.py   (regresiones)
specs/015-revision-adversarial-preparada/             (artefactos + findings)
```

## Estrategia de pruebas

Regresiones negativas por cada contrato nuevo, positivas del corpus (v2 sin
findings, suite actual sin tautologías), AGENT-PARITY con huérfano, y el
dogfood de SC-004 sobre esta feature.

## Despliegue y reversa

Push por la superficie CI vigente. Reversa: commit que retira fuentes,
superficies proyectadas, checker y validaciones; no se reescribe `main`.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | ADR-0019 y RFC-0003 preceden todo archivo de esta feature. |
| II. Spec antes que artefacto | PASS | spec, checklist y plan existen antes de fuentes y validadores. |
| III. El canon crece por decisión | PASS | ADR-0019 Aceptado habilita namespace, contrato y checker. |
| IV. Cero cifras sin fuente | PASS | Admisiones, políticas e idioma de versionado con fila SRC fechada. |
| V. Una fuente, muchas vistas | PASS | Agentes proyectados desde fuente única con lock; superficie manual prohibida. |
| VI. La IA consume; el humano firma | PASS | Los agentes preparan refutación; approval_actor_type sigue humano; ningún hallazgo aprueba. |
| VII. Privacidad por diseño | PASS | T0; los validadores no procesan datos personales ni rutas LLM. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `AGENT-PARITY`: namespace nuevo bajo el mismo lock (impacto principal).
- `SDD-CONTRACT`: contrato v3 + findings (impacto principal).
- `TEST`: checker de calidad enganchado en la suite.
- Resto de gates: sin cambio de contrato; deben permanecer verdes.

## Impactos

- **Arquitectura:** cero runtime; dos prompts proyectados y dos validadores.
- **Ontología:** sin cambio (la revisión adversarial es enforcement, no
  entidad nueva; su restricción podrá tipificarse cuando opere).
- **Datos/privacidad:** T0.
- **IA:** los agentes leen y refutan; no escriben canon ni aprueban.
- **Costo:** una pasada de revisión por feature estructural al cierre.
- **Blast radius:** sync, gate, suite de tests, superficies de agentes.
