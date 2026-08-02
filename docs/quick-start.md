# Quick start

Este recorrido parte de Core 3.1.0 instalado como baseline day-zero. Foundation
y el kernel están disponibles; ninguna iniciativa ni runtime consumidor está
instalado y no existe un candidato de release activo.

## 1. Orientación

Lee README → AGENTS → CURRENT_STATE → NEXT_ITERATION → ADR Catalog. No recorras
el árbol al azar ni uses una demo como fuente.

La superficie vigente es corta por diseño: en `specs/` viven solo las features
abiertas y la última cerrada; todo cierre anterior está en `specs/archive/`,
indexado con rutas viejo→nuevo en `governance/ARCHIVE_INDEX.md`. Para estado
por máquina: `python3 tools/operations/feature_context.py status`.

## 2. Aislamiento

```bash
git worktree add ../edaios-<tarea> -b task/<tarea>
python3 tools/operations/feature_context.py select <feature>
./scripts/install-hooks.sh
```

Un writer por worktree. El selector local no desplaza la autoridad compartida.
El hook pre-push ejecuta los gates de `.specify/gates.json`; sin él, el
fail-closed depende solo de disciplina manual.

## 3. Contrato antes de código

La feature crea `feature.spec.yaml`, `spec.md`, checklist, plan, tareas y
evidencia. Recorre constitution → specify → clarify → checklist → plan → tasks
→ analyze. Implement solo comienza con analyze verde y aprobación humana.

## 4. Elige el perfil correcto

- `core-release`: cambia o certifica el kernel;
- `initiative-adoption`: valida un attachment sin instalarlo dentro de Core;
- `federation`: valida mounts y namespaces de iniciativas ya gobernadas.

Los perfiles son acumulativos. No se omite un gate heredado para acelerar una
iniciativa.

## 5. Gobierno

- tarea: contrato claro, sin decisión estructural;
- RFC: alternativas relevantes abiertas;
- ADR: decisión estructural;
- Foundation: requiere autoridad explícita y recompilar Constitución.
- excepción: registro temporal, compensado, aprobado y con expiración; nunca
  puede exceptuar Foundation.

## 6. Adopta sin acoplar

El attachment declara initiative id/namespace, owners, versión y digest de
Core, sensibilidad, políticas, fuentes y autoridad. Core valida; no copia la
implementación, no infiere el dominio y no ejecuta el data plane.

## 7. Evidencia

Ejecuta pruebas primero en el scope modificado y luego `./scripts/test.sh` y
`./scripts/validate.sh`. Registra lo observado y lo no observado. Gates no
firman decisiones, valor ni verdad de owner. EvidenceReceipt verifica integridad
y staleness; ApprovalReceipt conserva por separado la decisión humana y se
resuelve contra PolicyProfile y AuthorityRegistry. Ese resultado local todavía
no demuestra estado Git remoto.

## 8. Memoria operativa opcional

Usa `edaios-core memory doctor`, inicia una sesión y construye el índice solo
cuando ayude al trabajo. `.edaios/` es local y reconstruible; summaries y
conflict suggestions no son evidencia ni decisión. La guía completa está en
[`agent-working-memory.md`](agent-working-memory.md).

## 9. Entrega

Inspecciona el diff, regenera vistas, conserva reversa y solicita revisión.
Commit, push y publicación son acciones separadas y explícitas.

Para preparar una release futura, sigue
[`core-release-cutover.md`](core-release-cutover.md). El estado `baseline` no es
un candidato; un manifest `prepared` no es aprobación; `locally-approved` no
autoriza afirmar push o tag; y solo un GitCutoverReceipt autorizado permite
declarar `sealed-by-authorized-observation`. El checker valida la evidencia
aportada, no consulta al proveedor en vivo.

El onboarding parte directamente de Core 3.1.0; no hereda una guía de migración
ni requiere conocer una genealogía anterior.
