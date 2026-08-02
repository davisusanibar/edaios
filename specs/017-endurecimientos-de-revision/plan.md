# Plan técnico · Endurecimientos de revisión

## Contexto técnico

Los dos escapes están caracterizados con precisión por los findings de la 010
(SRC-001) y el tercero está vivo: NEXT_ITERATION declara "en ejecución" a la
010 cerrada (SRC-003). El contrato de pin ya existe para plan.md (SRC-002);
la validación de superficie ya existe para CURRENT_STATE. Ambos
endurecimientos son extensiones directas, no mecanismos nuevos.

## Decisión de implementación

1. **Pin en spec.md** — `spec_kit_gate.py`: en la validación por feature,
   si el cuerpo de `spec.md` contiene una línea `Constitucion verificada`,
   se le aplica el contrato del plan: formato `sha256` de 64 hex y frescura
   contra `.specify/memory/constitution.md`. Sin la línea no hay exigencia
   (sin retroactividad, Límites). Mensajes de fallo distinguen `spec` de
   `plan`.
2. **Superficie diaria doble** — `traceability_check.py`: se extrae a un
   helper la parte de `validate_program_surface` que es por-archivo (rutas
   `specs/(archive/)?NNN-…` resolubles; reclamos de cierre con adyacencia
   `feature NNN … cerrad*` verificados contra `estado: Cerrado`) y se aplica
   a `CURRENT_STATE.md` y `NEXT_ITERATION.md`. Regla nueva en ambos: una
   feature con `estado: Cerrado` no puede figurar en una cláusula
   `en cola`/`en ejecución` (ámbito de oración con límite `. ` sobre texto normalizado — contrato distinto y más ancho que la adyacencia del check de cierres; fail-closed: una negación en la misma oración puede dar falso positivo y se resuelve reescribiendo la oración). La cita obligatoria de
   `last_closed_feature` y `VERSION` sigue siendo solo de CURRENT_STATE.
3. **Corpus** — NEXT_ITERATION se corrige al estado real (010 cerrada,
   programa en idle, decisiones pendientes del owner) para que la regresión
   positiva pase.
4. **Regresiones** — `test_program_surface.py`: fixture con huella de 62 hex
   en spec (vía subproceso del gate, patrón AdversarialReviewTests) — no:
   el pin de spec se prueba en `test_governance_conformance.py`
   (AdversarialReviewTests._feature_root ya construye features sintéticas
   con spec.md; se añade la línea de pin malformada); NEXT_ITERATION se
   prueba en `test_program_surface.py` con fixtures nuevos (ruta fantasma,
   cierre falso, cerrada-en-cola) y el corpus real como positivo.
5. **Revisión adversarial (v3)** — ambos subagentes antes del cierre.

## Alternativas descartadas

- exigir la línea de pin en todas las specs: retroactividad sobre 001-008
  archivadas que nunca la tuvieron;
- validar narrativa libre de NEXT_ITERATION: no determinista; solo contratos
  de adyacencia como los vigentes;
- gate nuevo para superficie: los checks viven en TRACEABILITY y
  SDD-CONTRACT existentes.

## Estructura afectada

```text
tools/validation/spec_kit_gate.py            (pin de spec)
tools/validation/traceability_check.py       (helper por-archivo + NEXT_ITERATION + regla en-cola)
program-office/context/NEXT_ITERATION.md     (corrección de contenido)
core/framework/tests/test_program_surface.py (regresiones NEXT_ITERATION)
core/framework/tests/test_governance_conformance.py (regresión pin de spec)
specs/017-endurecimientos-de-revision/       (artefactos + findings)
```

## Estrategia de pruebas

Regresiones negativas que reproducen los tres escapes reales y positivas del
corpus corregido; suites completas y 14 gates (SC-003).

## Despliegue y reversa

Push por la superficie CI vigente. Reversa: commit que retira las extensiones.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | Los endurecimientos derivan de findings gobernados, no de preferencia. |
| II. Spec antes que artefacto | PASS | Esta spec y plan preceden el código. |
| III. El canon crece por decisión | PASS | Extensión de checks existentes bajo ADR-0019/0002; sin estructura nueva. |
| IV. Cero cifras sin fuente | PASS | Los tres escapes citados con refs exactas y el tercero verificado vivo. |
| V. Una fuente, muchas vistas | PASS | El contrato de pin es uno; spec y plan lo comparten. |
| VI. La IA consume; el humano firma | PASS | La revisión adversarial precede la firma del owner. |
| VII. Privacidad por diseño | PASS | T0: los validadores procesan solo rutas y huellas del repositorio; sin datos personales ni ruta LLM. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `SDD-CONTRACT`: pin de spec (impacto principal).
- `TRACEABILITY`: superficie doble + regla en-cola (impacto principal).
- `TEST`: regresiones nuevas.
- Resto: sin cambio de contrato; deben permanecer verdes.

## Impactos

- **Arquitectura/Ontología:** sin cambio.
- **Datos/privacidad:** T0.
- **Costo:** despreciable.
- **Blast radius:** dos validadores, un documento de programa, dos archivos de test.
