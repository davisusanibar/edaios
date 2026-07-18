---
id: EDAIOS-CORE-MULTI-INITIATIVE-SCALE
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
  - ADR-0004
  - ADR-0005
  - ADR-0006
spec_tipada: specs/archive/004-core-multi-initiative-scale/feature.spec.yaml
fuentes:
  - core/foundation/model/KNOWLEDGE_OBJECT_MODEL.md
  - core/foundation/governance/ADR_PROCESS.md
  - core/foundation/governance/RFC_PROCESS.md
  - core/framework/core/docs/HARNESS_ARCHITECTURE.md
  - core/framework/core/docs/SECURITY_AND_CONCURRENCY.md
  - core/framework/core/docs/CONSUMER_INTEGRATION.md
  - core/framework/modules/harness-core/src/edaios_core_harness/resources/harness-registry.json
  - governance/ADR-0003-core-base-portability-and-git-memory.md
  - specs/archive/004-core-multi-initiative-scale/evidence/sources.md
value_ledger: "N/A: habilitador de gobierno; outcomes de adopcion requieren pilotos y owners reales"
hipotesis_valor: Un contrato de adopcion ejecutable permite sumar iniciativas heterogeneas sin introducir sus runtimes ni su verdad de dominio dentro de Core
---

# Core escalable para múltiples iniciativas

## Intención y alcance

Evolucionar EDAIOS Core Base desde un baseline cerrado hacia un kernel de
contratos adoptable por iniciativas independientes. Core conserva Foundation,
schemas, perfiles, validadores, receipts y puertos; cada iniciativa conserva su
implementación, fuentes, owners, decisiones, evidencia y outcomes en su propio
scope Git.

El cambio no instala Flink, Spark, IA, dominios institucionales, plataforma,
registry remoto, servicio multi-tenant ni un agente con autoridad. Los adapters,
runtimes y portales continuarán siendo consumidores derivados.

## Requisitos

- **FR-001:** debe existir una gramática canónica y ejecutable para identidades,
  estados y referencias de ADR, RFC, KO y artefactos SDD, incluyendo la
  normalización de RFC a cuatro dígitos y un mapeo explícito entre estados
  especializados y el lifecycle normativo de KO.
- **FR-002:** el gate KOM debe comprobar realmente las once reglas normativas
  declaradas por Foundation sobre todos los KOs instalados, con referencias y
  relaciones fail-closed y sin anunciar controles no ejecutados.
- **FR-003:** la validación debe separar los perfiles acumulativos
  `core-release`, `initiative-adoption` y `federation`; certificar Core no debe
  depender de que exista una iniciativa, y adoptar una iniciativa no debe
  debilitar los invariantes del release Core.
- **FR-004:** Core debe publicar schemas versionados y validadores para
  InitiativeManifest, PolicyProfile, SensitivityProfile, AuthorityRegistry,
  DelegationGrant, ApprovalReceipt, EvidenceReceipt, ExceptionRecord y Outcome,
  con ejemplos T0 ilustrativos y sin inventar verdad institucional.
- **FR-005:** cada harness declarado `enforced` debe poseer implementación,
  contrato y pruebas; request routing, TDD, artifact/result contracts,
  permission guard, human acceptance, rollback, telemetry y command wrapper
  deben dejar de ser promesas narrativas o conservar explícitamente madurez
  inferior.
- **FR-006:** EvidenceReceipt v2 debe ligar iniciativa, feature/run, actor,
  versión Core, política, base/head commit, digests de evidencia, sensibilidad,
  exit code, veredicto, claim boundary, rollback y aprobación; debe detectar
  evidencia alterada y staleness sin presentar una firma local como no repudio.
- **FR-007:** SDK y EKG deben admitir mounts federados explícitos, namespaces
  globales y detección fail-closed de colisiones; una vista federada continúa
  siendo derivada y nunca sustituye el Git canónico de una iniciativa.
- **FR-008:** el contrato público debe declarar compatibilidad, deprecación,
  migración y distribución reproducible, incluyendo checksum, SBOM y provenance
  local verificable; publicación y firma remota permanecen bloqueadas hasta
  existir infraestructura y autoridad reales.
- **FR-009:** el CLI debe facilitar adopción y operación mediante comandos para
  inicializar un attachment, validar por perfil, explicar fallos, verificar
  evidencia, comparar políticas, preparar upgrades y ejecutar reversa local,
  sin realizar merge, deploy ni aceptación humana.
- **FR-010:** un manifest de superficie debe relacionar cada claim con
  artefacto y prueba; referencias documentales a recursos inexistentes deben
  fallar o quedar rotuladas como `contracted`/futuras.
- **FR-011:** la suite debe cubrir contratos públicos, colisiones, schemas,
  permisos, receipts, tampering, staleness, CLI, concurrencia y compatibilidad
  mediante pruebas unitarias, contractuales, integración y adversariales.
- **FR-012:** gobierno, catálogos, contexto, arquitectura, quick start y modelo
  de madurez deben reflejar el nuevo baseline sin afirmar adopción, operación
  distribuida, firma remota, producción u outcomes todavía no demostrados.

## Criterios de éxito

- **SC-001:** todos los templates, catálogos y validadores aceptan la misma
  gramática de IDs y estados; una referencia mal formada o no resoluble falla.
- **SC-002:** el reporte KOM enumera VR-01 a VR-11 individualmente y una fixture
  con relación inválida o inversión de autoridad es rechazada.
- **SC-003:** `core-release` valida el kernel sin iniciativas;
  `initiative-adoption` acepta una fixture T0 válida y rechaza manifest,
  autoridad, sensibilidad o evidencia incompletos; `federation` rechaza IDs
  globales duplicados.
- **SC-004:** cada schema publicado posee ejemplo válido, ejemplo inválido y
  contract test; los perfiles solamente agregan controles a sus padres.
- **SC-005:** los doce harnesses terminan con madurez honesta y cada elemento
  marcado `enforced` tiene al menos una prueba positiva y una negativa.
- **SC-006:** verificar EvidenceReceipt v2 detecta modificación de evidencia,
  commit esperado distinto y aprobación ausente cuando la política la exige.
- **SC-007:** una federación ilustrativa de dos mounts con namespaces distintos
  puede consultarse; una colisión o mount implícito falla cerrado.
- **SC-008:** el artefacto distribuible es reproducible y entrega checksum,
  SBOM y provenance verificables, sin declarar firma o publicación inexistente.
- **SC-009:** el CLI ejecuta el flujo local de adopción y explicación en
  fixtures temporales sin modificar Core ni aceptar decisiones.
- **SC-010:** tests, validación integral, drift documental y gate Spec Kit
  finalizan en verde; la feature queda cerrada con evidencia y reversa.

## Frontera de claims

Sensibilidad T0. La feature entrega contratos y enforcement local del control
plane. No prueba operación multi-repositorio remota, seguridad de producción,
alta disponibilidad, rendimiento, firma criptográfica de una autoridad,
adopción organizacional ni valor de negocio. Esos claims requieren consumers,
infraestructura, owners y evidencia reales.

## Clarifications

- “Todas las iniciativas” significa que el contrato es agnóstico y extensible;
  no significa precrear un pack por tecnología o unidad organizacional.
- El Principal Architect conserva autoridad sobre Foundation; Core Maintainers
  gobiernan contratos públicos; owners y revisores de cada iniciativa operan
  únicamente dentro de delegaciones explícitas.
- El orquestador resuelve la siguiente fase y coordina; no decide ADR, riesgo,
  sensibilidad, verdad de dominio, aceptación ni outcome.
- Los tres perfiles de validación son acumulativos. Una iniciativa puede agregar
  políticas, nunca retirar controles heredados de Core o Foundation.
- Los ejemplos de iniciativas son fixtures ilustrativas y temporales; no se
  registran como consumers, módulos, outcomes ni evidencia institucional.
- Publicación, registry y firma externa se preparan como contratos verificables,
  pero permanecen no instalados hasta una decisión y capacidad operativa reales.
