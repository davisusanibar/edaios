# Plan técnico · Reorganización del archivo histórico

## Contexto técnico

La superficie diaria mezcla vigente con histórico: siete features cerradas en
la raíz de `specs/` (SRC-002) y un índice de archivo cuya prosa quedó
desactualizada (SRC-001). El patrón de archivado ya existe (001-008,
SRC-003) y los gates validan rutas declaradas en frontmatter, superficie
diaria y handoff (SRC-004): mover sin actualizar rompe cerrado — que es
exactamente la protección que esta feature usa como red.

## Decisión de implementación

1. **Regla de superficie sostenible** — en `specs/` viven solo las features
   abiertas y la última cerrada; todo cierre anterior vive en
   `specs/archive/`. Al cierre de esta feature: `010` (última cerrada) queda
   en raíz y `009`, `011`..`016` se reubican bajo `specs/archive/`.
2. **Movimiento con reescritura** — `git mv` por feature + reescritura de los
   dos campos de ruta (`spec_tipada` en spec.md, `artifact` en
   feature.spec.yaml) al prefijo `specs/archive/` (patrón SRC-003). Nada más
   del contenido cambia.
3. **Índice con rutas viejo→nuevo** — `governance/ARCHIVE_INDEX.md` gana la
   tabla de features archivadas (id, autoridad ADR, ruta anterior, ruta
   nueva) para 009 y 011-016; su prosa desactualizada se corrige y la regla
   de superficie queda declarada.
4. **Referencias y superficie** — actualización de rutas mencionadas en
   `.specify/feature.json` (last_closed → `specs/010-…` al cierre),
   `program-office/context/{CURRENT_STATE,NEXT_ITERATION}.md` (cierres
   previos → rutas de archivo), config de la demo (feature/lineage → `010`) y
   menciones de gobernanza (`RFC-0002`, `RFC-0003`, `ADR-0020`, `VL-001`) —
   corrección factual de paths, sin cambiar decisiones.
5. **Onboarding** — la superficie de navegación enlaza primero lo vigente y
   explica cómo consultar el archivo (SC-003).
6. **Revisión adversarial (v3)** — subagentes reales sobre esta feature antes
   del cierre; findings materializados.

## Alternativas descartadas

- symlinks de compatibilidad en las rutas viejas: prohibidos por la
  contención física de los gates (los validadores rechazan symlinks);
- archivar también la última cerrada: dejaría la superficie sin el puntero
  de continuidad que el handoff y la demo muestran;
- lista congelada de features a archivar: la regla de superficie es el
  contrato; la lista se deriva del estado, no se pinnea.

## Estructura afectada

```text
specs/{009,011,012,013,014,015,016}-*/     → specs/archive/ (git mv + reescritura de 2 campos)
governance/ARCHIVE_INDEX.md                (tabla viejo→nuevo + regla)
governance/{RFC-0002,RFC-0003,ADR-0020,VALUE_LEDGER}.md   (paths)
.specify/feature.json · docs/demos/*.config.json          (punteros)
program-office/context/{CURRENT_STATE,NEXT_ITERATION}.md  (paths)
docs/quick-start.md                        (onboarding)
specs/010-historical-archive-reorganization/ (artefactos + findings)
```

## Estrategia de pruebas

La red es la suite existente: `spec_kit_gate` revalida las 15 features en sus
rutas nuevas; `validate_program_surface` exige superficie coherente;
`test.sh`/`validate.sh` y los 14 gates cierran (SC-002). SC-001 se verifica
contra la tabla del índice (toda ruta nueva resoluble).

## Despliegue y reversa

Push por la superficie CI vigente. Reversa: commit que restaura las rutas
(git conserva la historia de los moves).

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | Nada pierde autoridad: cambia la ruta, no el contenido ni el estado. |
| II. Spec antes que artefacto | PASS | La spec 010 y este plan preceden todo movimiento. |
| III. El canon crece por decisión | PASS | La feature fue propuesta por el owner y su regla de mantenimiento estaba declarada en el índice. |
| IV. Cero cifras sin fuente | PASS | Censo de 7 cerradas y patrón de rutas con filas SRC fechadas. |
| V. Una fuente, muchas vistas | PASS | Índice, demo y superficie diaria se actualizan desde el estado real. |
| VI. La IA consume; el humano firma | PASS | El cierre lo firma el owner; la revisión adversarial precede la firma. |
| VII. Privacidad por diseño | PASS | T0; solo rutas de repositorio. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `SDD-CONTRACT`: revalida cada feature en su ruta nueva (impacto principal).
- `TRACEABILITY`: superficie diaria y menciones resolubles tras el movimiento.
- `CORE-BASE-DEMO`: config y HTML regenerados con el linaje nuevo.
- `CATALOG-PROJECTION`, `KOM`, `AGENT-PARITY`, `FND-PROJECTION`,
  `MONOREPO-STRUCTURE`, `BASELINE-SURFACE`, `CORE-CONFORMANCE`,
  `CLAIM-SURFACE`, `CORE-DISTRIBUTION`, `CORE-RELEASE-SEAL`, `TEST`,
  `VALIDATE`: sin cambio de contrato; deben permanecer verdes.

## Impactos

- **Arquitectura/Ontología:** sin cambio.
- **Datos/privacidad:** T0.
- **IA:** los agentes revisan; el movimiento es determinista.
- **Costo:** despreciable.
- **Blast radius:** rutas de 7 features, índice, punteros de programa y demo.
