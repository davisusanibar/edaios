---
id: EDAIOS-CORE-BASE-INITIAL
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: architecture
trazas:
  - ADR-0001
  - ADR-0002
  - ADR-0003
spec_tipada: specs/archive/001-core-base-initial/feature.spec.yaml
fuentes:
  - README.md
  - core/foundation/
  - repositories.json
  - edaios.lock.json
value_ledger: "N/A: baseline habilitante sin outcome institucional"
hipotesis_valor: Una base Foundation-Core cerrada reduce acoplamiento y permite que cada extensión futura demuestre su propia necesidad
---

# EDAIOS Core Base Inicial 1.0.0

## Requisitos

- **FR-001:** instalar únicamente la jerarquía Foundation → Core, sin raíces
  adicionales, productos ni runtimes consumidores.
- **FR-002:** cerrar Core Base como versión 1.0.0 con exactamente tres ADR
  aceptados y cero RFC.
- **FR-003:** conservar Core portable, instalable y verificable sin dependencia
  de un consumer concreto.
- **FR-004:** cerrar la feature con cinco de cinco tareas completadas, cero
  pendientes, evidencia registrada y estado `Cerrado`.
- **FR-005:** generar una única guía Operating System que integre arquitectura
  de información, catálogo ADR y evidencia del baseline desde sus fuentes.

## Criterios

- **SC-001:** `repositories.json` y `edaios.lock.json` declaran solo
  `edaios-core` 1.0.0.
- **SC-002:** ninguna superficie fuera de la topología autorizada existe.
- **SC-003:** el wheel Core 1.0.0 se instala y sus contratos pasan aisladamente.
- **SC-004:** la feature aparece como `Cerrado`, `5/5 completadas` y
  `0 pendientes` en fuente y guía.
- **SC-005:** el HTML coincide con su configuración y con las tres fuentes
  documentales integradas; no contiene narrativa transitoria u obsoleta.

## Frontera

Sensibilidad T0: sin PII, datasets, secretos, red, LLM, cloud, consumer o
publicación. Core Base no demuestra adopción ni operación productiva.
