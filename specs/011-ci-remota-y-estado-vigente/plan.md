# Plan técnico · Superficie de CI remota y estado de programa vigente

## Contexto técnico

Los 14 gates con scope `ci` (SRC-002) solo se ejecutan hoy vía hook local
opcional; el remoto real (GitHub, ADR-0017) no ejecuta nada, y esa ceguera
mantuvo CORE-BASE-DEMO rojo desde el commit inicial (RFC-0003, D3). La
superficie diaria del programa (`program-office/context/`) contradice el handoff
canónico: declara 008 como última cerrada y hogar Bitbucket (SRC-005). ADR-0017
está Aceptado: la implementación puede proceder.

## Decisión de implementación

1. **Workflow de gates** — `.github/workflows/ci.yml`, dos jobs:
   - `gates`: matriz Python 3.11/3.12/3.13 (SRC-003) sobre `ubuntu-latest`;
     `actions/checkout` pineado por SHA de commit con `fetch-depth: 0`
     (ADR-0013 falla cerrado en shallow y `kom_gate` consulta `git show HEAD:`);
     paso de integridad `test "$GITHUB_SHA" = "$(git rev-parse HEAD)"`
     (paridad con la verificación que la superficie Bitbucket ya declara);
     `actions/setup-python` pineado por SHA; ejecución de `./scripts/ci.sh`
     (una fuente, dos superficies de CI).
   - `pr-size`: solo en `pull_request`; calcula el tamaño del diff contra la
     base y lo publica en el step summary junto a la unidad de revisión
     `review_unit` (SRC-006). Sin `exit != 0` posible por diseño: el job
     informa, nunca bloquea (Límites de la spec).
   - Pins vigentes (SRC-007): `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
     (v7.0.1) y `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97`
     (v7.0.0).
2. **Check de frescura** — `tools/validation/traceability_check.py` gana una
   validación de superficie diaria: `CURRENT_STATE.md` debe contener el
   directorio literal de `last_closed_feature` del handoff canónico y la
   `VERSION` vigente, y no debe mencionar como cerrada una feature cuyo
   `spec.md` no declare `estado: Cerrado`. Falla cerrado; no interpreta
   narrativa (SRC-005, límite).
3. **Refresh de contenido** — `CURRENT_STATE.md` y `NEXT_ITERATION.md` pasan a
   reflejar: 009 cerrada, 010 propuesta en cola, hogar GitHub (ADR-0017),
   dirección de programa RFC-0003 (features 011-015). La narrativa autorada se
   conserva; solo se corrigen los hechos contradichos.
4. **Prueba de regresión** — test en `core/framework/tests/` que ejecuta el
   check de frescura sobre un fixture con superficie obsoleta (debe fallar) y
   sobre el corpus real (debe pasar).

## Alternativas descartadas

- generar `CURRENT_STATE.md` por completo: congelaría narrativa autorada en un
  template (refutación registrada en RFC-0003);
- job de tamaño bloqueante con umbral numérico: cifra sin baseline propio viola
  el Principio IV; queda como reporte hasta que el Value Ledger respalde un
  umbral;
- retirar `bitbucket-pipelines.yml`: fuera del alcance decidido por ADR-0017 y
  requerido hoy por `monorepo_structure_check.py`;
- referenciar actions por tag mutable (`@v7`): un tag re-apuntable rompe la
  reproducibilidad que el resto del repo exige por digest;
- instalar dependencias de CI (linters, YAML parsers): Core es stdlib-only; la
  validez del workflow la prueba el run remoto (SC-001), no un parser local.

## Estructura afectada

```text
.github/workflows/ci.yml                          (nuevo)
tools/validation/traceability_check.py            (check de frescura)
program-office/context/CURRENT_STATE.md           (refresh de contenido)
program-office/context/NEXT_ITERATION.md          (refresh de contenido)
core/framework/tests/test_governance_conformance.py (o archivo de test análogo)
specs/011-ci-remota-y-estado-vigente/             (artefactos de la feature)
```

## Estrategia de pruebas

- unitaria: fixture de superficie obsoleta falla el check; corpus vigente pasa;
- integración local: `scripts/test.sh` (150 casos actuales + regresión nueva) y
  `scripts/validate.sh` sin regresiones;
- remota: SC-001 exige el primer run verde archivado con URL y commit en
  `evidence/`; ocurre tras el push autorizado por el owner (Clarifications).

## Despliegue y reversa

El despliegue es el push del commit al hogar canónico, acto reservado al owner
(Restricciones de la Constitución). La reversa es un commit posterior que
elimina el workflow o restaura la superficie previa; no se reescribe `main`.
La superficie Bitbucket queda intacta.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | RFC-0003 y ADR-0017 preceden a todo archivo de esta feature. |
| II. Spec antes que artefacto | PASS | spec.md, checklist y este plan existen antes de tocar código o workflow. |
| III. El canon crece por decisión | PASS | ADR-0017 Aceptado habilita el cambio estructural; ADR-0013 conserva genealogía. |
| IV. Cero cifras sin fuente | PASS | 14 gates, matriz Python, review_unit y pins de actions tienen fila SRC en evidence/sources.md. |
| V. Una fuente, muchas vistas | PASS | Ambas superficies de CI ejecutan scripts/ci.sh; ninguna proyección se edita a mano. |
| VI. La IA consume; el humano firma | PASS | El push al remoto y el cierre de la feature son actos del owner; los gates verifican. |
| VII. Privacidad por diseño | PASS | T0: el workflow procesa solo metadatos del repo público; sin datos personales ni ruta LLM. |

Constitucion verificada: 1.0.0 · sha256:d57078593e5a78bb302e45cea9f5cc5d581be0c6ab8cbb8c751435febd5fb327

## Gate Impact

- `TRACEABILITY`: gana el check de frescura de superficie diaria (cambio principal).
- `TEST`: incorpora la regresión del check de frescura.
- `VALIDATE`: sin cambio de contrato; la cadena completa debe seguir verde.
- `MONOREPO-STRUCTURE`: `.github/` ya es ruta permitida; verificar que el
  workflow nuevo no introduce rutas fuera del mundo cerrado.
- `FND-PROJECTION`, `CATALOG-PROJECTION`, `AGENT-PARITY`, `SDD-CONTRACT`, `KOM`,
  `BASELINE-SURFACE`, `CORE-CONFORMANCE`, `CLAIM-SURFACE`, `CORE-DISTRIBUTION`,
  `CORE-RELEASE-SEAL`, `CORE-BASE-DEMO`: sin cambio de contrato; deben
  permanecer verdes antes y después.

## Impactos

- **Arquitectura:** ninguna pieza nueva de Core; solo superficie de ejecución
  remota y un check adicional en un gate existente.
- **Ontología:** sin cambio (el cierre D1 corresponde a la feature 012).
- **Datos/privacidad:** T0; el workflow no recibe secretos nuevos.
- **IA:** sin ruta LLM; agentes solo prepararon los artefactos.
- **Costo:** minutos de GitHub Actions del plan del owner; 3 ejecuciones por
  evento por la matriz; sin proveedor nuevo.
- **Blast radius:** `.github/`, un validador, dos documentos de programa y un
  test; Core empaquetado intacto.
