# Plan técnico · Hardening fail-closed de las fronteras de confianza

## Contexto técnico

El baseline local contiene contratos de autoridad, receipts, perfiles,
memoria, Spec Kit y gates, pero la revisión adversarial demostró que varias
superficies solo comparan una parte de la política o confían en el estado local.
La feature 009 corrige esas divergencias en Core y en sus proyecciones, sin
crear una iniciativa, un consumer, un proveedor o un runtime.

El ADR-0014 está `Propuesto`. Ninguna tarea que modifique código, schemas,
perfiles, hooks o documentación contractual puede ejecutarse hasta que el
Principal Architect lo acepte junto con este plan y `tasks.md`.

## Decisión de implementación

La implementación se ordena por riesgo y dependencias:

1. **P0 · autoridad y evidencia:** centralizar acciones reservadas; hacer que
   `permission_guard` rechace aliases y delegación amplificada; ligar
   ApprovalReceipt a iniciativa, feature run, rol y capability `approve`; hacer
   que `expected_policy` aplique approval, antigüedad y sensibilidad y que los
   argumentos solo puedan endurecer la policy.
2. **P1 · perfiles y gates:** introducir un registry de controles con paths,
   markers de test y gates resolubles; comparar todas las dimensiones de
   monotonía; validar ids, comandos y scopes mínimos antes de seleccionar gates;
   hacer que pre-push consuma stdin de Git y ejecute cada SHA local en un
   worktree aislado; pasar base/head explícitos al gate KOM.
3. **P1 · filesystem y privacidad:** compartir un helper de contención física
   para readers/writers, rechazar `.` y symlinks, usar `.edaios` 0700 y archivos
   0600, bloquear T2/T3 antes de crear estado, redactar valores sensibles y
   asegurar staging/journal o compensación verificable para attachments, setup,
   receipts, artifacts, índices y adapters.
4. **P1/P2 · gobierno SDD:** aceptar `active_feature: null` en un handoff v3
   manteniendo lectura de v2, registrar el hueco 006 como tombstone sin inventar
   contenido, tipar relaciones ADR `Amends`/`Supersedes` y exigir una matriz
   SC→FR→task→gate/test→evidence en la fase tasked/implemented.
5. **P2 · distribución:** acotar `requires-python` a `>=3.11,<3.14`, ejecutar
   CI en Python 3.11/3.12/3.13, actualizar export y documentación desde la
   fuente única y proponer Core 3.2.0 sin crear tag o release.

Cada unidad empieza con pruebas adversariales rojas, implementa el enforcement,
regenera recursos empaquetados y termina con pruebas verdes. Los cambios de
contrato se mantienen aditivos salvo el rechazo explícito de entradas que ya
violaban el contrato.

## Alternativas descartadas

- corregir solo los tres ejemplos reproducidos: no protege las mismas
  invariantes en nuevas superficies;
- confiar en el hook o CI como autoridad: ambos verifican, pero no aceptan;
- permitir T2/T3 con chmod como si fuera privacidad: permisos no instalan
  custodia ni cifrado;
- agregar un proveedor seguro en esta feature: ampliaría producto, costo,
  operación y sensibilidad sin decisión gobernada;
- editar HTML, catálogos o recursos empaquetados a mano: rompería source-first.

## Estructura afectada

```text
governance/ADR-0014-core-trust-boundary-hardening.md
governance/ADR_CATALOG.md
specs/009-core-trust-boundary-hardening/
.specify/{feature.json,gates.json}
core/framework/core/profiles/{security-policy.json,control-registry.json,*.profile.json}
core/framework/modules/harness-core/src/edaios_core_harness/{core.py,receipts.py,cli.py}
core/framework/modules/conformance-core/src/edaios_conformance/{profiles.py,resources/}
core/framework/modules/ess-core/src/edaios_core/{io.py,memory.py}
core/framework/modules/harness-core/src/edaios_core_harness/agent_setup.py
tools/validation/{gate_registry.py,pre_push_check.py,spec_kit_gate.py,traceability_check.py,kom_gate.py,core_conformance_check.py}
tools/operations/feature_context.py
scripts/{run-gates.py,install-hooks.sh,validate.sh,ci.sh}
specs/tombstones.json
core/framework/tests/test_{conformance_harness,core_release_candidate,feature_handoff,gate_runner,working_memory,versioned_surface}.py
bitbucket-pipelines.yml
core/framework/pyproject.toml
docs/,README.md,program-office/context/
```

La lista es un mapa de fuentes y no autoriza crear todos los archivos si una
prueba demuestra que un cambio menor mantiene el mismo contrato. Los recursos
de `core/` y los empaquetados deben permanecer idénticos después de regenerar.

## Estrategia de pruebas

La matriz versionada de la feature enlazará cada SC a sus FR, tareas, markers de
test, ids de gate y evidencia. Los casos mínimos son:

- acciones reservadas y delegación sin amplificación;
- policy esperada más estricta que el receipt, stale, sensibilidad ampliada y
  approval de iniciativa/actor/capability incorrectos;
- control desconocido, path o marker ausente, herencia que debilita cualquier
  dimensión y gate mínimo movido de scope;
- refs múltiples, root push, eliminación de ref y SHA enviado distinto de
  `HEAD`, más transición KOM root/dirty/committed;
- symlink/traversal, `.` y failure-injection de cada writer multiarchivo;
- T2/T3 antes de crear DB, modos 0700/0600 y redacción CLI;
- handoff idle, tombstone 006, relaciones ADR inválidas y SC sin evidencia;
- distribución reproducible, links internos exportados y matrices Python
  3.11/3.12/3.13.

La suite debe aislar todo `.edaios` temporal y no borrar el estado local del
checkout. Los tests de gates ejecutarán copias o worktrees temporales.

## Despliegue y reversa

No hay despliegue remoto. La reversa es un commit posterior que restaura la
fuente y regenera proyecciones; no se reescribe `main`, no se crea tag y no se
publica una release. Un journal incompleto bloquea recuperación automática y
deja la evidencia para una persona. El handoff vuelve a 008 solo mediante una
decisión explícita, y `active_feature: null` se usa al cerrar 009.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | ADR-0014, spec y matriz preceden cualquier cambio de código. |
| II. Spec antes que artefacto | PASS | FR/SC, checklist, plan y tareas son fuentes versionadas. |
| III. El canon crece por decisión | PASS | El ADR propuesto bloquea implementación hasta aceptación humana. |
| IV. Cero cifras sin fuente | PASS | Versiones, permisos y fechas están registradas en evidence/sources.md. |
| V. Una fuente, muchas vistas | PASS | Recursos, catálogos, docs y export se regeneran desde fuentes. |
| VI. La IA consume; el humano firma | PASS | Principal Architect acepta ADR, plan, tareas y cierre; gates solo verifican. |
| VII. Privacidad por diseño | PASS | T2/T3 fallan antes de persistir y T0 limita la evidencia local. |

Constitucion verificada: 1.0.0 · sha256:d57078593e5a78bb302e45cea9f5cc5d581be0c6ab8cbb8c751435febd5fb327

## Gate Impact

- `FND-PROJECTION`: comprobar que la Constitución derivada permanece sin drift.
- `CATALOG-PROJECTION`: proyectar ADR-0014 y relaciones tipadas.
- `AGENT-PARITY`: conservar las integraciones Spec Kit sincronizadas.
- `SDD-CONTRACT`: validar handoff v3, tombstone y matriz SC→evidence.
- `KOM`: validar transición base/head y owners sin usar el mismo `HEAD`.
- `MONOREPO-STRUCTURE`: validar hooks, recursos y ausencia de estado local en Git.
- `TRACEABILITY`: exigir FR/SC/tarea/gate-test/evidence y relaciones resolubles.
- `BASELINE-SURFACE`: confirmar que no aparece un consumer, provider o runtime.
- `CORE-CONFORMANCE`: validar registry de controles, schemas, policies y perfiles.
- `CLAIM-SURFACE`: actualizar límites sin elevar claims por configuración.
- `CORE-DISTRIBUTION`: verificar export, recursos, checksum y contrato Python.
- `CORE-RELEASE-SEAL`: mantener Core 3.2.0 como identidad propuesta sin tag/release.
- `CORE-BASE-DEMO`: regenerar vistas sin inventar estado de adopción.
- `TEST`: ejecutar regresiones adversariales y matriz de intérpretes disponible.
- `VALIDATE`: ejecutar la cadena completa desde un checkout limpio.

El runner debe validar que los gates mínimos con scope `pre-push,ci` no puedan
ser desplazados y que pre-push/CI compartan el mismo registro canónico.

## Impactos

- **Arquitectura:** hardening del control plane y de los writers; no cambia
  Foundation ni invierte `Foundation → Core`.
- **Ontología:** agrega relaciones ADR, tombstone y evidencia tipada; no crea
  un dominio nuevo.
- **Datos/privacidad:** T0 para esta feature; T2/T3 bloqueado sin decisión.
- **IA:** agentes coordinan y verifican; no aprueban ni promueven.
- **Costo:** solo aumenta cobertura local y pasos CI declarados; no se infiere
  disponibilidad o consumo de un proveedor.
- **Blast radius:** Core, gates, handoff, docs, distribución y tests; ninguna
  iniciativa externa.
