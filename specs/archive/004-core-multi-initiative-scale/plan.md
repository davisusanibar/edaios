# Plan técnico · Core multi-iniciativa

## Contexto técnico

Core Base 1.0.0 instala un único paquete Python con Foundation, contratos,
harnesses, Spec Kit, EKG/Query y SDK de lectura. El baseline está deliberadamente
cerrado: catálogos y gates fijan una sola topología, el receipt es v1, la
federación descubre rutas de forma implícita y parte del control plane permanece
`contracted`.

RFC-0001 selecciona un kernel agnóstico con attachments externos. ADR-0004 fija
perfiles acumulativos; ADR-0005 fija autoridad, riesgo, excepciones y receipt v2;
ADR-0006 fija federación explícita, compatibilidad y supply chain honesta.

## Decisión de implementación

### 1. Kernel y conformance

Se incorpora `edaios_conformance` dentro del artefacto único `edaios-core`.
Publicará:

- registry de schemas JSON y validador stdlib fail-closed;
- gramática de gobierno, perfiles y políticas de sensibilidad/review/security;
- validación de InitiativeManifest, autoridad, delegación, excepción, outcome y
  receipts;
- resolución de herencia de perfiles sin posibilidad de retirar controles;
- CLI de adopción que opera sobre un workspace consumidor, no sobre la autoridad
  Core.

No se agrega una dependencia de runtime externa. JSON Schema se publica como
contrato interoperable; el validador local implementa el subconjunto empleado y
rechaza keywords no soportadas para evitar validaciones parciales silenciosas.

### 2. Harnesses y evidencia

`CoreHarness` deja de limitarse a validar el registry. Cada harness obtiene una
operación determinista o validador concreto. EvidenceReceipt v2 usa canonical
JSON y SHA-256, calcula digests de evidencia, liga commits y política y se
verifica antes de aceptar. ApprovalReceipt permanece separado; `human` es un
tipo de actor validado, no una firma criptográfica.

Los receipts locales continúan en `.edaios/` como cache reconstruible. La
promoción durable exige que una iniciativa los copie a su ruta de evidencia en
Git mediante una acción humana; Core no hace commit automáticamente.

### 3. Gates por perfil

`.specify/gates.json` sigue siendo el registro ejecutable del repositorio. Los
validadores dejan de depender de conteos fijos y aceptan `--profile`:

- `core-release`: Foundation/Core, distribución y surface manifest;
- `initiative-adoption`: añade manifest, autoridad, política y evidencia;
- `federation`: añade mounts, namespace y colisiones.

El perfil hijo hereda todos los gates del padre. `baseline_surface_check.py`
conserva la defensa contra historia/runtimes instalados, pero deja de bloquear
decisiones nuevas de la genealogía vigente.

### 4. KOM y gobierno tipado

Un resource canónico define regex y lifecycles por tipo. RFC usa cuatro dígitos.
Los estados especializados se mapean al lifecycle KO (`Aceptado` de ADR equivale
a `Ratificado`) sin reescribir silenciosamente decisiones existentes.

`kom_gate.py` reporta VR-01..VR-11 por separado y valida el corpus instalado:
identidad global, tipos, metadata/cuerpo/historial Git, estado, referencias,
dominio-rango cuando haya relaciones, jerarquía, ADR de decisiones,
supersesión/transición y representaciones. Mounts de iniciativas son opcionales
y explícitos.

### 5. Federación

SDK y Query/EKG reciben mounts `{namespace, path, authority}`. El namespace forma
la identidad global; IDs locales duplicados entre namespaces son válidos, pero
la identidad global duplicada, tipos incompatibles o edges no resolubles fallan.
El constructor anterior de root único se conserva para Foundation/Core y se
marca como scope local, no como federación implícita.

### 6. Compatibilidad y distribución

Core evoluciona a 2.0.0 porque cambia contratos públicos de receipts, perfiles y
gates. Una única fuente `VERSION` alimenta package, export, lock y provenance; los
checks rechazan drift. La distribución temporal genera:

- wheel reproducible;
- checksum SHA-256;
- SBOM CycloneDX-like mínima con componentes realmente empaquetados;
- provenance local con builder, comando, inputs y subject digest;
- verificación independiente de los tres artefactos.

No se afirma SLSA level, firma, registry o publicación. La política declara
compatibilidad de schemas, soporte N/N-1 cuando exista una versión previa
materializada, deprecación y migración/reversa.

### 7. Surface manifest y documentación

`claim-surface.json` registra `claim`, `maturity`, `artifact`, `tests` y límite.
Un gate comprueba rutas, símbolos y tests. Los documentos que citaban recursos
inexistentes se corrigen a rutas reales. README, arquitectura, gobierno, contexto
y quick start describen Core 2.0.0 sin convertir fixtures en adopción.

## Alternativas descartadas

- **Core con módulos por tecnología:** contradice ADR-0003 y crea imports
  inversos.
- **Un único gate parametrizado con excepciones:** hace posible debilitar el
  baseline; se prefieren perfiles acumulativos.
- **Biblioteca externa de políticas/schemas:** introduce supply chain antes de
  demostrar necesidad; stdlib es suficiente para el contrato inicial.
- **Índice central autoritativo:** invierte Git-first y crea un runtime no
  solicitado.
- **Firma simulada con SHA-256:** un digest local no prueba identidad; se mantiene
  el claim como integridad reproducible.

## Estructura de archivos

```text
governance/
  RFC-0001...
  ADR-0004..0006...
core/framework/
  modules/conformance-core/src/edaios_conformance/
    schemas.py profiles.py federation.py distribution.py cli_support.py
    resources/{schemas,profiles,policies,grammar,claims}/...
  modules/harness-core/...                 enforcement y receipt v2
  modules/{ess-core,ekg-core,query-engine,sdk-consumption}/...
  core/docs/                               contratos corregidos
  core/profiles/                           manifests públicos
  core/templates/initiative/               attachment T0 ilustrativo
  tests/                                   unit, contract, integration, adversarial
tools/validation/
  kom_gate.py
  core_conformance_check.py
  core_distribution_check.py
  claim_surface_check.py
scripts/{test,validate}.sh
specs/archive/004-core-multi-initiative-scale/
program-office/context/
```

## Estrategia de pruebas

1. Unitarias: schemas, perfiles, grammar, harnesses, receipt, namespace y CLI.
2. Contractuales: cada schema con documento válido e inválido; cada harness
   `enforced` con camino positivo y negativo.
3. Integración: attachment T0 temporal, profile adoption, receipt/promoción,
   dos mounts federados y distribución instalada en entorno aislado.
4. Adversariales: path traversal/symlink, permiso ausente/expirado, tampering,
   staleness, IDs duplicados, policy weakening y referencia no resoluble.
5. Regresión: features cerradas, demo offline, Spec Kit, Constitution y Core
   Base sin consumers instalados.

## Despliegue y reversa

- Despliegue: release local 2.0.0 dentro del branch, sin registry ni publicación.
- Migración: manifest y receipt v1 permanecen legibles solo mediante un adapter
  explícito; nuevos artefactos se escriben v2.
- Reversa: restaurar el lock 1.0.0, ejecutar `core-release` y conservar receipts
  previos; ningún attachment se modifica automáticamente.
- Corte: commit y push autorizados únicamente después de gates verdes. No se
  crea release/tag ni PR por inferencia.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | RFC-0001 y ADR-0004..0006 gobiernan contratos antes del código; manifests apuntan a fuentes Git. |
| II. Spec antes que artefacto | PASS | Feature tipada, spec, aclaraciones, checklist y plan preceden implementación. |
| III. El canon crece por decisión | PASS | Tres ADR aceptados separan adopción, autoridad/riesgo y federación/supply chain. |
| IV. Cero cifras sin fuente | PASS | Conteos y referencias externas están registrados en `evidence/sources.md`; no se fijan targets inventados. |
| V. Una fuente, muchas vistas | PASS | Git local de Core/iniciativa conserva autoridad; federación, SBOM, provenance y catálogos son derivados. |
| VI. La IA consume; el humano firma | PASS | ApprovalReceipt exige actor humano autorizado; CLI, CI y orquestador no aceptan decisiones. |
| VII. Privacidad por diseño | PASS | SensitivityProfile y permission guard preceden evidencia o consumo; fixtures son T0 sin datos reales. |

Constitucion verificada: 1.0.0 · sha256:d57078593e5a78bb302e45cea9f5cc5d581be0c6ab8cbb8c751435febd5fb327

## Gate Impact

- `FND-PROJECTION`: se recompila si la aclaración normativa del KOM cambia.
- `SDD-CONTRACT`: adopta RFC de cuatro dígitos y mantiene cobertura completa.
- `KOM`: pasa de metadata parcial a VR-01..11 ejecutables.
- `MONOREPO-STRUCTURE`: conserva Core único y permite attachments validados sin
  instalar módulos preventivos.
- `TRACEABILITY`: catálogos dinámicos, RFC/ADR resolubles y lock versionado.
- `BASELINE-SURFACE`: conserva superficie agnóstica sin bloquear decisiones
  posteriores de la genealogía.
- `CORE-CONFORMANCE`: nuevo gate de profiles, schemas, autoridad y evidencia.
- `CLAIM-SURFACE`: nuevo gate claim → artefacto → test.
- `CORE-DISTRIBUTION`: versión única, wheel, checksum, SBOM y provenance.
- `TEST` y `VALIDATE`: amplían cobertura y sellan el release local.

## Impactos

- Arquitectura: nueva capa lógica de conformance dentro del único paquete Core.
- Ontología/gobierno: gramática y mapeo de estados ejecutables; sin nueva verdad
  institucional.
- Datos/privacidad: schemas y políticas T0–T3; no se procesan datasets.
- IA: agentes quedan detrás de delegación y permission guard; no hay LLM runtime.
- Costo: ejecución local stdlib; no se instala servicio ni dependencia externa.
- Blast radius: Foundation/KOM, gobierno, package Python, gates, tests,
  distribución, documentos y contexto; no toca dominios o engines inexistentes.
