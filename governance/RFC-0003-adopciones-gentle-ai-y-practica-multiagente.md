# RFC-0003 — ¿Qué adopta EDAIOS de gentle-ai y de la práctica multi-agente sin perder su enforcement code-first?

**Estado:** Propuesto
**Fecha:** 2026-08-01
**Owner:** Principal Architect

## Problema

Se comparó EDAIOS contra gentle-ai (`github.com/Gentleman-Programming/gentle-ai`,
clon analizado en commit `b6ecb3e`) y contra la práctica multi-agente descrita en el
episodio de Vanishing Gradients del 2026-07-30 (Chip Huyen y Tim Hopper, "Agents and
Agents That Try to Prove You Wrong", youtube.com/watch?v=NH-ic7-V-jY). El contraste
es simétrico:

- EDAIOS tiene enforcement code-first (gates fail-closed, schemas, constitución
  compilada con citas verificables) pero **cero subagentes**: ningún revisor, ningún
  refutador, ningún estado SDD legible por máquina para ruteo.
- gentle-ai tiene ergonomía SDD sobresaliente (specs por dominio, DAG de fases,
  status JSON ruteable, cuatro lentes de review más refutador, presupuestos por
  artefacto) pero su propia documentación admite que el sistema es prompt-enforced:
  no existe validador nativo de su `openspec/config.yaml`.

Durante la refutación adversarial del borrador de adopción (método del propio
episodio: un agente intenta demostrar que el plan se equivoca) se verificaron además
dos hechos que condicionan cualquier evolución:

- **D1.** KOM-VR-02 es fail-open hoy: la regex de `tools/validation/kom_gate.py:49`
  extrae 38 tokens de la ontología, no 28, y acepta 10 nombres de relaciones
  (`governs`, `consumes`, `implements`, `decides`, `resolves`, `supersedes`,
  `projects`, `references`, `validates`, `represents`) como tipos de entidad. Un KO
  con `tipo: governs` pasa el gate KOM. Verificado ejecutando la regex real sobre
  `core/foundation/ontology/EDAIOS_ONTOLOGY.md`.
- **D2.** El repositorio opera con remoto `github.com/davisusanibar/edaios` mientras
  ADR-0013 (Aceptado) declara `bitbucket.org/data_and_ia/edaiosv` como hogar
  canónico. Los 14 gates con scope `ci` no corren en ningún remoto real; añadir CI
  de GitHub sin decisión ratificaría un re-homing que nadie decidió.
- **D3.** CORE-BASE-DEMO estaba rojo desde el commit inicial (verificado en worktree
  prístino de HEAD): el generador de demos exigía un canon sin propuestas abiertas,
  premisa rota por RFC-0002 (Propuesto desde 2026-07-17), y el HTML almacenado era
  anterior incluso a ese RFC; el check además comparaba el total de RFCs contra la
  etiqueta de ratificados. Nadie lo notó porque el CI no corre en remoto — prueba
  viva de D2. Corregido en esta misma iteración: la demo refleja el catálogo tal
  cual es (propuestas incluidas) y la pureza de release queda donde corresponde,
  en CORE-RELEASE-SEAL.

La pregunta: qué capacidades se adoptan, con qué mecanismo, y en qué orden, sin
violar los principios I-VII ni degradar el enforcement existente.

## Opciones y trade-offs

- **A · Adopción selectiva con consumidor validante (recomendada).** Cada adopción
  entra como código, schema o prompt proyectado con un gate o test que lo valida.
  Siete capacidades sobreviven la refutación; el resto se rechaza con fundamento
  verificado. Costo mediano, distribuido en cinco features.
- **B · Trasplante amplio del modelo gentle-ai.** Incluir deltas de spec, split
  orquestador/ejecutor, presupuestos de palabras como gate, tabla de modelos por
  fase. Rechazado pieza por pieza: los deltas presuponen un paso de fusión que
  EDAIOS no tiene (la evolución de KOs ya la cubre PAT-003 con KOM-VR-10); el split
  orquestador/ejecutor sería prosa inmediatamente falsa sin runtime; los
  presupuestos como bloqueo habrían fallado la feature 009 (spec de 963 palabras,
  conteo verificado, contra el límite 650 de gentle-ai); la tabla de modelos sin
  parser es una tabla decorativa — el anti-patrón que D1 demuestra letal.
- **C · Statu quo.** No adoptar nada. Deja abiertos D1 y D2, mantiene el Constitution
  Check como declaración sin refutación preparada y a EDAIOS sin revisión adversarial.

## Impacto y reversibilidad

La opción A es aditiva: no debilita ningún control (los perfiles prohíben
`remove_controls`), no introduce runtime ni proveedor (se mantienen los invariantes
`coordinates-only` y `no-execution`), y cada pieza es reversible por versión. La
autoridad no cambia: los agentes revisores **preparan** refutaciones; el único
aprobador sigue siendo humano (`approval_actor_type: "human"` en review-policy).

## Plan de evidencia

Vehículos que resuelven este RFC por partes, cada uno con su criterio de aceptación:

1. **ADR-0017 + specs/011-ci-remota-y-estado-vigente** — decide el hogar canónico
   (cierra D2); primer run verde de GitHub Actions archivado como evidencia; check
   determinista de frescura de `program-office/context/CURRENT_STATE.md` en
   TRACEABILITY.
2. **ADR-0018 + specs/012-cierre-de-contratos-resolubles** — cierra D1: la gramática
   de gobierno gana `entities`, `kom_gate` verifica correspondencia bidireccional
   MD↔JSON por sección y KOM-VR-02 consume la lista del contrato; un KO con
   `tipo: governs` debe fallar. Paths de `control-registry.json` resolubles
   (la fila `kom` cita hoy un test inexistente). Referencias en prosa
   `Deriva de:` resolubles.
3. **specs/013-sdd-status-maquina** — `tools/operations/feature_context.py` emite
   `edaios.sdd.status/v1` con `nextRecommended` acotado al dominio del phase-dag;
   los ocho comandos fuente rutean solo por ese token.
4. **ADR-0019 + specs/015-revision-adversarial-preparada** — dos agentes fuente
   (`edaios.refutador`, `edaios.lente-riesgo`) bajo un segundo namespace del mundo
   cerrado AGENT-PARITY; `review/findings.md` obligatorio para cambio estructural
   desde la fase analyze; checker de calidad de tests bajo el gate TEST.
5. **ADR-0020 + specs/016-onboarding-de-consumer-real** — resuelve RFC-0002
   (opción A, `seed_gate()`); ciclo SDD real en el consumer `data-kcd2026`; primera
   entrada VL-001 del Value Ledger con evidencia.

## Validación de reutilización (auditoría de aceleradores, 2026-08-01)

A pregunta del Owner — si existen frameworks tipo EDAIOS reutilizables en vez de
construir desde cero — se auditó el ecosistema OSS con datos vivos de GitHub. No
existe un competidor que cubra las siete capas. Por capa:

- **SDD: ya reutilizado.** EDAIOS está montado sobre github/spec-kit (~125k
  estrellas, el líder), vendorizado 0.12.11 vía el adapter Adopt-or-Adapt de
  ADR-0016. Hallazgo operativo: upstream va en v0.15.1 — **~15 releases de drift
  en 3 semanas** — y su preset nuevo "Autonomous Run Governance" entra en
  territorio de gobernanza. Acción candidata: actualizar el vendor y evaluar ese
  preset antes de que canibalice la narrativa propia. Alternativas (OpenSpec ~63k,
  BMAD ~51k, Agent OS estancado, Kiro propietario): se descartan como reemplazo;
  de OpenSpec se minan los stores multi-repo.
- **Memoria: ya reutilizado.** Engram (Gentleman-Programming/engram, ~5.8k, el
  mantenido) es la elección vigente del adapter; Mem0/Graphiti/Letta solo si
  SQLite local queda corto.
- **Supply chain: el acelerador más claro disponible.** Los receipts custom
  podrían emitirse como in-toto Statements (envelope DSSE, estándar compartido
  por Sigstore y SLSA) sin cambiar el flujo local; syft para SBOM; cosign
  opcional. Adaptación de bajo costo, interoperabilidad inmediata.
- **Config multi-superficie: parcial.** La convención AGENTS.md es estándar de la
  Linux Foundation desde dic-2025 (EDAIOS ya la usa); ruler (~2.8k) cubre la
  mitad "instrucciones" pero no el lock sha256 ni la proyección tipada — el sync
  propio sigue justificado.
- **Gates sobre artefactos: sin reemplazo.** OPA/Conftest gobiernan datos
  estructurados y el agent-governance-toolkit de Microsoft gobierna runtime;
  nadie valida la cadena spec→plan→task→claim con fail-closed. Los 15 gates
  stdlib se conservan.
- **Ontología operativa: sin reemplazo.** La tesis está validada externamente
  (charla de F. Coyle, AI Engineer 2026) pero no hay toolkit; LinkML es el único
  bloque serio (YAML → JSON Schema/OWL/Pydantic) y queda anotado como camino
  generador futuro para la gramática — decisión separada de ADR-0018, que cierra
  el contrato actual sin migrar de formato.
- **Ledger ADR/RFC: sin reemplazo.** El nicho murió en 2024 (adr-tools,
  log4brains); el compilador propio está justificado.

Conclusión de la auditoría: la diferenciación defendible de EDAIOS es
ontología + gates + claim surface; el workflow SDD se comoditizó en 2026 y debe
consumirse de upstream, no competirse.

## Recomendación

Opción A. Del episodio se adopta además, como práctica de trabajo sin cambio de
repo: revisión en PR y no en IDE, tiering de modelos caro→barato al delegar, y la
validación externa de la postura EDAIOS de no construir el inner loop (los
proveedores de modelos ya lo construyen; EDAIOS es el outer loop: specs, gates,
evidencia, revisión).

De la auditoría de reutilización se derivan dos vehículos candidatos adicionales,
pendientes de decisión del Owner para entrar al roadmap: (a) actualización del
vendor Spec Kit 0.12.11 → 0.15.x por el carril Adopt-or-Adapt existente, con
evaluación del preset de gobernanza upstream; (b) receipts en formato in-toto
Statement + SBOM con syft, manteniendo checksums stdlib como fallback.

## Resolución

Pendiente. Se ratificará cuando ADR-0017, ADR-0018, ADR-0019 y ADR-0020 estén
Aceptados y las features del roadmap cierren con gates en verde.
