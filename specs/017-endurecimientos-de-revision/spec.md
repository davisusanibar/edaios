---
id: EDAIOS-ENDURECIMIENTOS-DE-REVISION
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: governance
trazas:
  - ADR-0019
  - ADR-0002
  - RFC-0003
spec_tipada: specs/017-endurecimientos-de-revision/feature.spec.yaml
fuentes:
  - specs/archive/010-historical-archive-reorganization/review/findings.md
  - tools/validation/spec_kit_gate.py
  - tools/validation/traceability_check.py
value_ledger: "N/A: endurecimiento de validadores sin outcome institucional propio"
hipotesis_valor: Cada escape encontrado por la revisión adversarial que se convierte en check permanente reduce la clase entera del defecto, no solo la instancia.
---

# Endurecimientos de revisión

La revisión adversarial de la feature 010 dejó dos endurecimientos anotados
como futuros (SRC-001): el control de pin constitucional solo valida
`plan.md` — una huella inválida de 62 caracteres vivió meses en una spec — y
la validación de superficie diaria solo lee `CURRENT_STATE.md` — por donde
escapó dos veces la contradicción de `NEXT_ITERATION.md`. Esta feature los
convierte en código con sus regresiones, cerrando la clase de ambos escapes.

## Requisitos

- **FR-001:** la línea `Constitucion verificada` de `spec.md`, cuando existe,
  cumple el mismo contrato que la de `plan.md`: huella sha256 completa
  (64 hex) y frescura contra la constitución vigente; una huella truncada,
  malformada u obsoleta falla cerrado. Las specs sin la línea no la
  adquieren retroactivamente.
- **FR-002:** la validación de superficie diaria cubre también
  `NEXT_ITERATION.md`: toda ruta de feature mencionada resuelve, ningún
  reclamo de cierre contradice el estado real, y ninguna feature con
  `estado: Cerrado` figura declarada en cola o en ejecución.
- **FR-003:** existen regresiones que reproducen los dos escapes reales
  (huella de 62 caracteres; "En cola"/"en ejecución" con feature cerrada) y
  el corpus vigente pasa — lo que exige corregir el contenido obsoleto de
  `NEXT_ITERATION.md` como parte de esta feature.

## Criterios de éxito

- **SC-001:** regresión: spec con huella de 62 caracteres o desactualizada
  falla el gate; el corpus vigente pasa (8 spec.md llevan la línea de pin; los 16 plan.md ya la tenían bajo contrato previo).
- **SC-002:** regresiones: ruta no resoluble, reclamo de cierre falso y
  feature cerrada "en cola/en ejecución" en NEXT_ITERATION fallan; el corpus
  corregido pasa.
- **SC-003:** revisión adversarial materializada (v3) y suites + 14 gates en
  verde.

## Límites

No se exige la línea de pin en specs que no la tienen (sin retroactividad);
no se valida narrativa libre — solo los contratos deterministas declarados;
no se acuñan gates nuevos (los checks viven en los gates existentes).

## Clarifications

Revisión del 2026-08-02: sin ambigüedades del owner — ambos endurecimientos
quedaron registrados con refs exactas en los findings de la 010 y su
mecanismo es extensión directa de checks existentes.

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
