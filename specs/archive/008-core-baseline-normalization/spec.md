---
id: EDAIOS-CORE-BASELINE-NORMALIZATION
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: architecture
trazas:
  - ADR-0001
  - ADR-0002
  - ADR-0010
  - ADR-0011
  - ADR-0012
  - ADR-0013
spec_tipada: specs/archive/008-core-baseline-normalization/feature.spec.yaml
fuentes:
  - governance/ADR-0013-portable-single-root-genealogy.md
  - .specify/feature.json
  - .specify/gates.json
  - tools/validation/core_release_seal_check.py
  - tools/publishing/generate_day_zero_demos.py
  - specs/archive/008-core-baseline-normalization/evidence/sources.md
  - specs/archive/008-core-baseline-normalization/evidence/baseline-validation.md
value_ledger: "N/A: normalización técnica del baseline; adopción y outcomes requieren una iniciativa externa con owner y fuentes propios"
hipotesis_valor: Un baseline único, honesto y validado permite que las iniciativas consuman Core sin heredar estados, refs o evidencia de una genealogía retirada
---

# Normalización del baseline Core 3.1.0

## Intención y alcance

Convertir el contenido funcional ya presente en `main` en un baseline semántico
coherente con la nueva genealogía: Foundation + Core 3.1.0 instalados, sin
candidato 3.0 pendiente, sin rama vNext y sin consumer o runtime incorporado.

La feature normaliza gobierno, handoff, release gate, documentación, demo y CI.
No cambia Foundation, la API funcional de Core, los perfiles acumulativos ni la
frontera de memoria no autoritativa.

## Requisitos

- **FR-001:** VERSION, lock, manifests, documentación y demo deben presentar
  Core 3.1.0 como baseline instalado de la nueva genealogía, sin afirmar una
  release previa, adopción, producción o outcome.
- **FR-002:** ADR-0012 debe reemplazar el cutover específico 3.0; la feature 006
  debe dejar de ser activa y sus artefactos ligados a commits retirados no deben
  participar en gates, demo, handoff o claims vigentes.
- **FR-003:** el tooling de release debe aceptar un manifest explícito y seguro;
  cuando no exista candidato debe retornar `baseline-no-candidate`, sin leer una
  versión histórica ni permitir promoción implícita.
- **FR-004:** el handoff canónico debe declarar 007 como último cierre y 008 como
  foco activo; no debe existir selector local compartido ni tarea operativa de
  la feature 006.
- **FR-005:** README, contexto, quick start, changelog, arquitectura de
  información y demo deben derivar el mismo estado instalado y conservar todas
  las interacciones del ciclo, gobierno, Spec Kit, arquitectura, evidencia y
  glosario.
- **FR-006:** Bitbucket Pipelines debe invocar exclusivamente `scripts/ci.sh`;
  la topología debe admitir ese archivo sin convertir CI en autoridad o runtime
  del producto.
- **FR-007:** tests y gates deben cubrir ausencia de candidato, manifest
  explícito seguro, handoff actualizado, config→HTML sin drift y pipeline
  delegado al runner canónico.
- **FR-008:** el snapshot debe poder materializarse como un único commit raíz
  verificable en `edaiosv/main`, sin hashes autorreferenciales ni historia
  heredada. El bootstrap de `main` exige tests/gates locales y remoto vacío;
  cualquier tag, publicación o sello permanece bloqueado sin CI y protección.

## Criterios de éxito

- **SC-001:** todos los portadores vigentes reportan Core 3.1.0 baseline y las
  superficies de entrada no contienen `vNext`, un candidato 3.0 pendiente ni
  nombres de ramas o commits retirados.
- **SC-002:** la feature 006 no aparece en el handoff o demo y ningún manifest o
  target suyo es consumido por un gate vigente.
- **SC-003:** ejecutar el release gate sin manifest termina en verde con
  `baseline-no-candidate`; un path ausente, externo o con traversal falla.
- **SC-004:** Spec Kit resuelve baseline 004, último cierre 007 y activa 008 sin
  referencias duplicadas o tareas huérfanas.
- **SC-005:** la guía HTML se regenera desde sus fuentes, conserva siete vistas,
  siete etapas y ocho escenas y muestra el baseline instalado.
- **SC-006:** el pipeline versionado delega en `scripts/ci.sh` y un clon limpio
  termina con tests y todos los gates CI en verde.
- **SC-007:** los gates de superficie confirman un solo módulo Core y ausencia
  de dominios, engines, consumers, Platform, productos y runtimes.
- **SC-008:** un clon completo del snapshot resuelve exactamente un root sin
  padres, rechaza shallow/replace/grafts y reporta `baseline-no-candidate`; el
  remoto no contiene tags ni ramas heredadas.

## Frontera de claims

T0 técnico. La feature puede demostrar coherencia local, CI, refs y protección
observados. No demuestra adopción, una iniciativa real, datos, privacidad T2/T3,
operación distribuida, firma criptográfica, disponibilidad, rendimiento ni
outcomes.

## Clarifications

1. Se conserva la identidad 3.1.0 porque describe el contrato funcional
   acumulado; la nueva genealogía no pretende reescribir SemVer como 1.0.0.
2. ADR-0010 continúa como política reusable, pero su intento de cutover 3.0 no
   es una release ni evidencia vigente.
3. Specs cerradas conservan conocimiento; ninguna puede fingir refs, receipts o
   estado remoto que ya no existe.
4. El primer consumer, incluido Flink, vivirá fuera de Core y requerirá su propia
   feature, decisión y attachment.
5. La autorización permite crear y pushear el root de `main`; un tag o release
   siguen siendo acciones separadas y no reclamadas por esta feature.
