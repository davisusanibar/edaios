---
id: EDAIOS-CI-REMOTA-Y-ESTADO-VIGENTE
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: governance
trazas:
  - ADR-0017
  - ADR-0013
  - RFC-0003
spec_tipada: specs/archive/011-ci-remota-y-estado-vigente/feature.spec.yaml
fuentes:
  - governance/ADR-0017-hogar-canonico-github-y-ci-remota.md
  - .specify/gates.json
  - core/framework/pyproject.toml
  - core/framework/core/profiles/review-policy.json
value_ledger: "N/A: infraestructura de verificación remota sin outcome institucional propio"
hipotesis_valor: Ejecutar los gates en el remoto real convierte el fail-closed de disciplina manual en garantía verificable y hace visible cualquier gate rojo el mismo día.
---

# Superficie de CI remota y estado de programa vigente

RFC-0003 documentó que los gates de scope `ci` no corren en ningún remoto real
(D2) y que esa ausencia mantuvo un gate rojo invisible desde el commit inicial
(D3). ADR-0017 decidió el hogar canónico GitHub y autorizó la superficie de CI
remota. Esta feature materializa esa decisión y repara la superficie diaria del
programa, que hoy contradice el handoff canónico (SRC-005).

## Requisitos

- **FR-001:** todos los gates declarados con scope `ci` (14 hoy, SRC-002) se
  ejecutan en el hogar canónico en cada push a `main` y en cada pull request,
  sobre historia Git completa y verificando que el commit ejecutado es el commit
  recibido.
- **FR-002:** la ejecución remota cubre todas las versiones de Python que Core
  declara soportadas (SRC-003).
- **FR-003:** cada pull request recibe un reporte informativo del tamaño de su
  diff contrastado con la unidad de revisión de la política vigente (SRC-006);
  el reporte no bloquea.
- **FR-004:** la verificación de trazabilidad falla cerrado si la superficie
  diaria del programa contradice el handoff canónico de features o la versión
  vigente de Core.
- **FR-005:** la superficie diaria del programa refleja el hogar canónico
  decidido y la genealogía real de features (SRC-005), sin borrar narrativa
  autorada.

## Criterios de éxito

- **SC-001:** existe al menos un run remoto en verde sobre el hogar canónico que
  ejecuta los 14 gates de scope `ci`, archivado en `evidence/` con URL y commit.
- **SC-002:** una regresión con superficie diaria contradictoria hace fallar la
  verificación de trazabilidad, y el corpus vigente pasa sin errores.
- **SC-003:** `scripts/test.sh` y `scripts/validate.sh` pasan sin regresiones.
- **SC-004:** la salida del reporte informativo de tamaño de diff es visible en
  un run remoto y no existe condición de bloqueo asociada a ninguna cifra.

## Límites

No se decide ningún umbral bloqueante de tamaño de PR: convertir el reporte en
bloqueo exige un baseline propio respaldado por el Value Ledger (Principio IV).
No se retira `bitbucket-pipelines.yml` (fuera de alcance por ADR-0017). No se
afirma protección de rama, release, publicación ni adopción; la evidencia remota
cubre solo los runs archivados.

## Clarifications

Revisión del 2026-08-01 (alcance, owner, valor, datos, privacidad, seguridad,
errores, criterios): sin ambigüedades bloqueantes que requieran decisión del
owner — alcance y hogar fijados por ADR-0017 aceptado; T0 sin datos personales;
las elecciones restantes son técnicas y corresponden al plan. Dependencia
registrada, no ambigüedad: la evidencia de SC-001 exige commit y push al hogar
canónico, actos que requieren autorización humana explícita (Restricciones de la
Constitución); la implementación local no la sustituye.

## Constitution Check

Constitucion verificada: `.specify/memory/constitution.md` sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86.

I PASS · II PASS · III PASS · IV PASS · V PASS · VI PASS · VII PASS.
