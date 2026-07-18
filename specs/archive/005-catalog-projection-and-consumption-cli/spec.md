---
id: EDAIOS-CATALOG-PROJECTION-AND-CONSUMPTION-CLI
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: architecture
trazas:
  - ADR-0002
  - ADR-0003
  - ADR-0007
  - ADR-0008
spec_tipada: specs/archive/005-catalog-projection-and-consumption-cli/feature.spec.yaml
fuentes:
  - governance/archive/adr/ADR-0007-governance-catalogs-as-compiled-projections.md
  - governance/archive/adr/ADR-0008-read-only-consumption-cli.md
  - tools/publishing/compile_constitution.py
  - core/framework/modules/query-engine/src/edaios_query/__init__.py
  - core/framework/modules/sdk-consumption/src/edaios_sdk_consumption/__init__.py
  - specs/archive/005-catalog-projection-and-consumption-cli/evidence/sources.md
value_ledger: "N/A: habilitador de gobierno; el valor de consumo exige iniciativas con owners reales"
hipotesis_valor: Catalogos compilados eliminan la contencion de decisiones concurrentes y una CLI read-only evita que cada iniciativa invente scripts divergentes sobre el mismo contrato
---

# Catálogos compilados y CLI de consumo read-only

## Requisitos

- **FR-001:** los catálogos ADR/RFC se compilan desde los documentos de
  decisión individuales leyendo solo metadatos explícitos; nada se infiere.
- **FR-002:** el gate `CATALOG-PROJECTION` falla cerrado ante números
  duplicados, cabeceras no canónicas, estados fuera del dominio o drift entre
  documento y catálogo comprometido.
- **FR-003:** `edaios-core kos list|get` expone Knowledge Objects en modo
  lectura con el sobre `edaios.cli-output/v1` y `claim_boundary` declarado.
- **FR-004:** `edaios-core query find|impact|neighborhood` consulta el grafo
  EKG en modo lectura, permanece latente sin instancia y falla cerrado ante
  identidades no resolubles.
- **FR-005:** ambas capacidades quedan registradas como claims `enforced` con
  pruebas resolubles, y los derivados (demo) se regeneran desde sus fuentes.

## Criterios

- **SC-001:** `compile_catalogs.py --check` reproduce byte a byte ambos
  catálogos comprometidos.
- **SC-002:** un corpus con número duplicado, heading ajeno o estado inválido
  produce error del compilador, nunca una proyección.
- **SC-003:** toda salida de consumo declara schema y frontera; un id no
  resoluble retorna `blocked` con exit code 2.
- **SC-004:** tests y los doce gates pre-push permanecen en verde localmente.
- **SC-005:** `claim-surface.json` registra `catalog-projection` y
  `consumption-cli` como enforced con markers demostrados.

## Frontera

Sensibilidad T0: contratos, proyecciones y consultas locales. No demuestra
adopción, iniciativas reales, publicación ni operación remota. La CLI no
adquiere autoridad: consulta, no acepta ni promueve.
