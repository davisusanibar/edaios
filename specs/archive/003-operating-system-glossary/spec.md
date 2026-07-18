---
id: EDAIOS-OPERATING-SYSTEM-GLOSSARY
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: hardening
trazas:
  - ADR-0002
  - ADR-0003
spec_tipada: specs/archive/003-operating-system-glossary/feature.spec.yaml
fuentes:
  - docs/demos/edaios-operating-system.config.json
  - core/foundation/constitution/ART-008-GLOSARIO.md
  - core/foundation/ontology/EDAIOS_ONTOLOGY.md
  - core/foundation/model/KNOWLEDGE_OBJECT_MODEL.md
  - core/foundation/governance/ADR_PROCESS.md
  - core/foundation/governance/RFC_PROCESS.md
  - core/framework/core/docs/SDD_ARTIFACT_GRAMMAR.md
  - specs/archive/003-operating-system-glossary/evidence/sources.md
value_ledger: "N/A: mejora de comprensión de una vista derivada sin outcome institucional"
hipotesis_valor: Un glosario contextual y buscable reduce la fricción de onboarding sin debilitar el vocabulario gobernado
---

# Glosario del EDAIOS Operating System

## Alcance

Agregar a la guía offline una séptima vista llamada `Glosario` que explique en
lenguaje directo los códigos, objetos y reglas que aparecen en el recorrido. La
vista deriva definiciones de fuentes vigentes, muestra cómo se usa cada término
en este repositorio y hace explícitas las ambigüedades o contratos todavía
parciales.

## Requisitos

- **FR-001:** la navegación debe incorporar `Glosario` como séptima vista sin
  alterar ni perder las seis vistas existentes.
- **FR-002:** el glosario debe explicar como mínimo ADR, RFC, T0, FR/FR-001,
  SC/SC-001, T/T001, ART, VAL, KO y KOM, además de los términos de mayor
  frecuencia necesarios para comprender gobierno, conocimiento, delivery,
  sensibilidad, evidencia y valor.
- **FR-003:** cada entrada debe ofrecer nombre expandido cuando exista,
  explicación simple, uso en este repositorio, ejemplo o límite y fuente
  resoluble; los identificadores locales de una feature no deben presentarse
  como identidades globales.
- **FR-004:** la vista debe permitir buscar sin distinguir mayúsculas ni
  acentos, filtrar por categoría, informar el número de resultados y comunicar
  un estado vacío de forma accesible, conservando todas las definiciones
  legibles cuando JavaScript no esté disponible.
- **FR-005:** el HTML debe continuar siendo offline y derivado
  determinísticamente del config y las fuentes gobernadas; el gate de la demo
  debe cubrir navegación, vocabulario mínimo, fuentes, semántica accesible y
  contrato del filtro.

## Criterios de éxito

- **SC-001:** `#glossary` activa un séptimo tab seleccionado y muestra una guía
  para leer `ADR-0003`, `FR-001`, `SC-001`, `T001`, `ART-008`, `T0` y
  `VAL-004`.
- **SC-002:** buscar `ADR` deja visible la entrada de Architecture Decision
  Record; buscar `conocimiento` encuentra KO/KOM y términos relacionados sin
  depender de tildes o mayúsculas.
- **SC-003:** el filtro de sensibilidad permite localizar T0, T1/T2/T3 y PII;
  la vista aclara que el baseline define T0 y restricciones T2/T3, no una
  taxonomía semántica completa de los cuatro tramos.
- **SC-004:** `VAL` queda rotulado como referencia no materializada, no como catálogo o
  gate activo; `ART-NNN` se distingue del `ART-*` de ArtifactRecord en la
  gramática SDD.
- **SC-005:** generación, drift check, gate, pruebas, validación y recorrido en
  navegador terminan en verde sin assets de red ni cambios a Foundation.

## Frontera

Sensibilidad T0. Esta feature mejora una proyección educativa y corrige una
etiqueta confusa de la demo. No enmienda el glosario constitucional, no crea un
catálogo `VAL`, no completa la taxonomía T1–T3 y no acepta decisiones.

## Aclaraciones resueltas

- “Otros” significa vocabulario que ya aparece en la guía o en el onboarding
  inmediato; no intenta copiar toda la Ontología.
- `FR-001`, `SC-001` y `T001` reinician numeración dentro de cada feature; su
  contexto es la carpeta Spec Kit que los contiene.
- `ART-NNN` identifica un artículo constitucional; `ART-*` también aparece en
  la gramática técnica como identidad genérica de `ArtifactRecord`, por lo que
  la vista debe mostrar el contexto antes de interpretar el prefijo.
- `VAL-004` permanece mencionado en el KOM como nombre de una implementación de
  validación, pero no resuelve a un artefacto del Core Base limpio. No existe un
  ledger `VAL-*`; el gate activo relacionado es `KOM`.
- Las definiciones normativas no se reescriben: la demo las resume, enlaza su
  fuente y declara los límites de la simplificación.
