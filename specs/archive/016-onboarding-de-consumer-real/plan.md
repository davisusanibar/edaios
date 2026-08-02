# Plan técnico · Onboarding de consumer real

## Contexto técnico

El consumer real (`data-evolutionary/kcd-001`, SRC-003) porta la copia manual
del gate pineada a `0c60544` con deriva vigente verificada por digest
(SRC-002). El adapter ya siembra la constitución (SRC-004); ADR-0020 decidió
espejar el patrón para el gate. El ledger está vacío (SRC-005) y PLB-005 es
el hueco libre de playbooks (SRC-006).

## Decisión de implementación

1. **`seed_gate(root, out_dir, *, force=False)`** en
   `edaios_sdd_adapter/spec_kit.py`, junto a `seed_speckit_constitution`:
   - copia `tools/validation/spec_kit_gate.py` del root autoritativo al
     consumer y escribe el sidecar `spec_kit_gate.SOURCE.md` con: versión de
     Core (`VERSION`), digest sha256 del gate, fecha de siembra y vía
     (`edaios_sdd_adapter.seed_gate`);
   - destino idéntico → no-op idempotente (no reescribe sidecar);
   - destino divergente sin `force` → `ValueError` con ambos digests
     truncados ("la deriva se reporta, no se pisa");
   - `force=True` → re-siembra gate y sidecar.
2. **PLB-005** — `core/framework/docs/playbooks/PLB-005-onboarding-de-consumer.md`
   (KO tipo Playbook): secuencia acotada — verificar deriva, sembrar
   (confirmación explícita si diverge), correr
   `spec_kit_gate --profile consumer-release` en el repo del consumer,
   archivar evidencia, registrar el outcome en el ledger del Core que
   gobierna. Sin pasos que el código no respalde.
3. **Ejecución real sobre `kcd-001`** (FR-003): (a) invocar `seed_gate` sin
   `force` contra la copia divergente vigente → capturar la negativa con
   digests; (b) re-sembrar con `force=True` (confirmación del owner: la
   orden de ejecutar esta feature); (c) correr el gate sembrado sobre el
   módulo con `--profile consumer-release`; (d) archivar salidas en
   `evidence/sc-002-consumer-real.json`. Sin commit en el repo del consumer.
4. **VL-001** en `governance/VALUE_LEDGER.md` con los campos que el ledger
   declara: apuesta (entrega gobernada elimina deriva silenciosa), owner de
   beneficio, baseline (copia manual pineada a `0c60544`, divergente, fuente
   SRC-002 con fecha), target (cero deriva silenciosa del gate en consumers),
   acción (seed_gate + PLB-005), evidencia (corrida archivada), atribución,
   limitaciones (un consumer; outcome en observación), review y estado.
5. **Regresiones** — `core/framework/tests/test_seed_gate.py`: siembra
   fresca, idempotencia, negativa ante divergencia (mensaje con digests),
   re-siembra con force; y validación de que PLB-005 existe como KO.
6. **Revisión adversarial (contrato v3)** — delegada a los subagentes reales
   `edaios-refutador` y `edaios-lente-riesgo` proyectados por la feature 015;
   sus tablas se materializan en `review/findings.md` y un CRITICAL/HIGH
   abierto bloquea el cierre.
7. **RFC-0003 → Ratificado** al cierre: su Resolución declara la condición
   (ADR-0017..0020 Aceptados y features del roadmap cerradas en verde); con
   016 cerrada se cumple — `resolved_by: ADR-0017, ADR-0018, ADR-0019,
   ADR-0020, ADR-0021` y regeneración de catálogos.

## Alternativas descartadas

- empaquetar el gate en el wheel (opción B de RFC-0002): diferida por
  ADR-0020 hasta que existan varios consumers;
- sembrar también `.specify/gates.json` o superficies del monorepo: el
  consumer-release es raíz liviana (ADR-0016) y no las necesita;
- declarar el outcome de VL-001 como logrado: el ledger prohíbe cerrar
  outcomes por gate técnico; queda en observación con fecha de review;
- commitear la siembra en el repo del consumer: su árbol pertenece a su
  owner; esta feature deja los archivos y la decisión de commit allí.

## Estructura afectada

```text
core/framework/extensions/sdd-adapter/src/edaios_sdd_adapter/spec_kit.py
core/framework/docs/playbooks/PLB-005-onboarding-de-consumer.md
core/framework/tests/test_seed_gate.py
governance/VALUE_LEDGER.md                     (VL-001)
governance/RFC-0003-*.md                       (Ratificado al cierre)
specs/016-onboarding-de-consumer-real/         (artefactos + findings)
~/…/data-evolutionary/kcd-001/tools/validation/ (gate + sidecar re-sembrados, sin commit)
```

## Estrategia de pruebas

Regresiones de las cuatro ramas de `seed_gate` en árboles temporales; corrida
real archivada sobre `kcd-001` (SC-002); vínculo VL-001 validado por el gate
(SC-003); revisión adversarial y suites completas (SC-004).

## Despliegue y reversa

Push del Core por la superficie CI vigente. En el consumer: los archivos
sembrados quedan sin commit; revertir es restaurar la copia previa desde su
git. Reversa en Core: commit posterior que retira `seed_gate` y PLB-005.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | ADR-0020 y RFC-0002/0003 preceden el código; el playbook cita solo lo que el código respalda. |
| II. Spec antes que artefacto | PASS | spec, checklist y plan existen antes de seed_gate y PLB-005. |
| III. El canon crece por decisión | PASS | ADR-0020 Aceptado habilita; opción B y core-monorepo quedan diferidos por decisión, no por omisión. |
| IV. Cero cifras sin fuente | PASS | Digests, commit del pin y estado del ledger con fila SRC fechada; VL-001 declara baseline con fuente. |
| V. Una fuente, muchas vistas | PASS | El gate del consumer pasa a ser proyección gobernada del de Core con procedencia verificable. |
| VI. La IA consume; el humano firma | PASS | force=True materializa la confirmación del owner; el commit en el repo del consumer queda reservado a su owner; VL-001 en observación. |
| VII. Privacidad por diseño | PASS | T0; rutas y digests del mismo owner; sin ruta LLM en la siembra. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `SDD-CONTRACT`: valida el vínculo VL-001 contra el ledger (primera vez con
  entrada real) y el contrato v3 de esta feature.
- `TEST`: regresiones de seed_gate.
- `KOM`: PLB-005 entra como KO Playbook (numeración y frontmatter).
- `CATALOG-PROJECTION`/`TRACEABILITY`: RFC-0003 Ratificado con resolved_by.
- Resto de gates: sin cambio de contrato; deben permanecer verdes.

## Impactos

- **Arquitectura:** una función de adapter; cero superficies nuevas de Core.
- **Ontología:** sin cambio.
- **Datos/privacidad:** T0.
- **IA:** la siembra es determinista; los agentes solo revisan.
- **Costo:** despreciable.
- **Blast radius:** adapter, un playbook, ledger, y la superficie
  `tools/validation/` del consumer (reversible por su git).
