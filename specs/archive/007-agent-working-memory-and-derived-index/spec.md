---
id: EDAIOS-AGENT-WORKING-MEMORY-AND-DERIVED-INDEX
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: architecture
trazas:
  - ADR-0001
  - ADR-0003
  - ADR-0005
  - ADR-0006
  - ADR-0010
  - ADR-0011
spec_tipada: specs/archive/007-agent-working-memory-and-derived-index/feature.spec.yaml
fuentes:
  - core/framework/core/docs/MEMORY_PORT.md
  - core/framework/modules/sdk-consumption/src/edaios_sdk_consumption/__init__.py
  - core/framework/extensions/sdd-adapter/src/edaios_sdd_adapter/adapter.py
  - .specify/integrations.lock.json
  - specs/archive/007-agent-working-memory-and-derived-index/evidence/sources.md
  - specs/archive/007-agent-working-memory-and-derived-index/evidence/implementation-validation.md
value_ledger: "N/A: capacidad habilitante local; outcomes requieren iniciativa, owner y fuente externos"
hipotesis_valor: Una memoria operativa reconstruible y una búsqueda derivada reducen fricción de continuidad y federación sin convertir contexto de agente en autoridad
---

# Memoria operativa de agentes e índice de conocimiento derivado

## Intención y alcance

Completar el puerto de memoria de Core con una implementación local, contracts
vendor-neutral, búsqueda indexada, sesiones observacionales, surfacing de
conflictos y onboarding explícito. Engram sirve como referencia y adapter
opcional; no se incorpora como dependencia, canon ni juez.

El incremento fue incorporado al baseline day-zero por ADR-0012. No instala
Engram, no sincroniza memoria fuera del workspace y no crea una iniciativa o
dominio.

La implementación local quedó cerrada el 2026-07-16. `Cerrado` significa tareas
implementadas y evidencia técnica local; no significa release, adopción u
operación productiva.

## Requisitos

- **FR-001:** Core debe publicar un contrato `MemoryProvider` sin operaciones de
  promoción, aceptación o decisión; toda salida local o externa debe declarar
  provider, versión, canal, sensibilidad, procedencia, digest,
  `authoritative=false` y `rebuildable=true`.
- **FR-002:** el provider local debe guardar observaciones content-addressed
  bajo `.edaios/memory/`, validar roots y UTF-8, serializar writes mediante lock
  y atomicidad, preservar revisiones y ser borrable sin afectar el canon.
- **FR-003:** debe existir un índice derivado ligado a la huella del corpus y de
  los mounts, almacenado bajo `.edaios/index/`, con FTS5 cuando esté disponible y
  fallback explícito. Debe buscar solo conocimiento canónico por defecto,
  requerir opt-in para borradores/memoria y bloquear consultas cuando esté stale.
- **FR-004:** la detección debe diferenciar duplicado exacto de contradicción,
  crear únicamente candidatos `review-required`, conservar sugerencias de IA
  como no autoritativas y bloquear promoción mientras exista un conflicto
  pendiente; nunca debe seleccionar un ganador automáticamente.
- **FR-005:** las sesiones deben registrar `start`, `event`, `summary` y `end`
  con feature, branch/worktree, actor/agente, timestamps y cadena de digests. El
  timeline debe ser `observation-only` y cualquier afirmación verificada debe
  enlazar un receipt existente por digest.
- **FR-006:** el onboarding debe ofrecer `plan`, `apply`, `verify` y `rollback`
  para superficies soportadas, operar project-local por defecto, derivar desde
  el lock de integraciones, ser idempotente, fallar ante colisiones y no escribir
  sin consentimiento explícito.
- **FR-007:** el adapter Engram debe ser opcional, degradable y pineado a una
  compatibilidad explícita; debe usar transporte local seguro, rechazar hosts no
  loopback por defecto y no exponer sync remoto, juicio, delete, promotion o
  writes al canon. Ausencia o incompatibilidad no bloquean Git ni validación
  canónica.
- **FR-008:** schemas y CLI deben representar records, sesiones, conflictos,
  capacidades, staleness y límites de claim con errores tipados, sin mezclar
  resultados canónicos con working memory de forma implícita.
- **FR-009:** pruebas contractuales y adversariales deben cubrir provider ausente,
  host remoto, T2/T3, symlink/root escape, UTF-8 inválido, concurrencia, drift del
  corpus, índice stale, duplicado/contradicción, no auto-promoción, cadena de
  sesión, setup idempotente y colisiones.
- **FR-010:** la superficie aditiva debe identificarse como Core 3.1.0,
  actualizar manifests y documentación sin declarar release sellada ni
  reemplazar la búsqueda canónica por defecto.

## Criterios de éxito

- **SC-001:** inspección del protocolo confirma que no existe método de promover,
  aprobar, decidir o escribir Knowledge Objects canónicos.
- **SC-002:** dos revisiones distintas del mismo subject se conservan con digests
  diferentes y un intento concurrente o fuera del root falla cerrado.
- **SC-003:** una consulta canónica devuelve resultados tipados por FTS5 o
  fallback; modificar el corpus hace que el índice se rechace como stale hasta
  reconstruirlo.
- **SC-004:** un duplicado exacto no crea conflicto y dos claims incompatibles
  producen un candidato pendiente sin ganador; la comprobación de promoción se
  bloquea.
- **SC-005:** alterar cualquier evento invalida la cadena de sesión; un summary
  sin receipt permanece `unverified` y no se contabiliza como evidencia.
- **SC-006:** `setup plan` no escribe, `apply` repetido es idempotente, una
  colisión no administrada bloquea y `rollback` restaura el contenido previo.
- **SC-007:** un adapter Engram ausente reporta `degraded` sin afectar búsqueda
  canónica; un endpoint no loopback o una versión incompatible se rechazan.
- **SC-008:** schemas, wheel/export y entrypoint aislado incluyen la nueva
  superficie sin dependencias externas obligatorias.
- **SC-009:** el gate Spec Kit, tests aplicables y conformance quedan verdes con
  fixtures adversariales; cualquier límite no observado queda explícito.
- **SC-010:** todos los portadores del baseline coinciden en 3.1.0 y el estado de
  release mantiene explícito que no existe candidato activo ni publicación
  reclamada.

## Frontera de claims

T0 local. Se procesan únicamente fixtures y metadatos sintéticos. La feature no
demuestra calidad semántica, retención real entre agentes, privacidad T2/T3,
performance, cloud, identity, disponibilidad de Engram, adopción ni outcome.

## Clarifications

1. Se adoptan patrones de Engram y se reimplementan con stdlib; no se copia su
   código ni se incorpora su SQLite como autoridad.
2. `mem_judge` inspira surfacing, no decisión: una inferencia solo puede anexar
   `suggested_relation`; la resolución gobernada exige actor humano autorizado.
3. Timeline y summary son contexto operativo. Solo un EvidenceReceipt verificado
   puede respaldar evidencia; el journal se limita a referenciarlo.
4. El índice es una proyección reemplazable. `KnowledgeClient.search()` conserva
   su semántica canónica y la nueva búsqueda indexada se invoca explícitamente.
5. La integración Engram soporta solo loopback y operaciones read/append de
   working memory. Sync, cloud, delete y conflict judgment quedan fuera.
6. Setup modifica únicamente archivos del proyecto. Configuraciones de `$HOME`,
   allowlists o procesos globales requieren otra decisión y permiso.
7. ADR-0012 incorpora la capacidad al baseline day-zero. Baseline y release
   siguen siendo estados distintos: instalar la capacidad no crea un sello.
