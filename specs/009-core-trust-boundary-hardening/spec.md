---
id: EDAIOS-CORE-TRUST-BOUNDARY-HARDENING
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: architecture
trazas:
  - ADR-0002
  - ADR-0004
  - ADR-0005
  - ADR-0011
  - ADR-0012
  - ADR-0014
spec_tipada: specs/009-core-trust-boundary-hardening/feature.spec.yaml
fuentes:
  - governance/ADR-0014-core-trust-boundary-hardening.md
  - specs/009-core-trust-boundary-hardening/evidence/sources.md
value_ledger: "N/A: hardening técnico del kernel sin adopción ni outcome de una iniciativa"
hipotesis_valor: Un Core que verifica sus propias fronteras impide que configuración incompleta o estado local eleven autoridad y claims
---

# Hardening de fronteras de confianza de Core

## Intención y alcance

Cerrar las brechas reproducidas entre los contratos públicos de Core y su
enforcement local en autoridad, evidencia, perfiles, gates, ciclo Spec Kit,
filesystem, memoria y compatibilidad Python.

La feature fortalece Core y sus proyecciones. No crea consumers, proveedores,
servicios, remotos, una release ni un mecanismo de aceptación automática.

## Requisitos

- **FR-001:** toda acción reservada debe usar una identidad canónica y ser
  denegada a agentes; ninguna delegación puede otorgar una capacidad, scope o
  vigencia que el delegante no posea de forma efectiva.
- **FR-002:** la verificación de evidencia debe aplicar todas las restricciones
  de la política esperada aunque el receipt solicite menos y exigir que
  cualquier aprobación pertenezca al mismo receipt e iniciativa y provenga de
  una persona activa con rol y capacidad explícitamente autorizados.
- **FR-003:** un cambio de política o un perfil hijo no puede debilitar controles,
  aprobación, antigüedad, excepciones o sensibilidad heredadas.
- **FR-004:** cada control declarado por un perfil debe resolver a
  implementación, prueba y gate verificables; un control desconocido o sin
  cobertura debe fallar cerrado.
- **FR-005:** los gates mínimos y sus scopes no pueden retirarse o desplazarse
  sin una decisión gobernada; las validaciones Git deben juzgar los objetos que
  se pretenden enviar y las transiciones deben comparar base y head explícitos.
- **FR-006:** el ciclo SDD debe representar una feature activa y el reposo sin
  foco, conservar tombstones de features retiradas, validar relaciones entre
  ADR y exigir trazabilidad de cada criterio de éxito hasta tarea, gate o test y
  evidencia de cierre.
- **FR-007:** la memoria local debe rechazar antes de persistir cualquier tramo
  sin soporte de almacenamiento gobernado, usar permisos mínimos y evitar que
  la CLI revele el contenido almacenado. T2/T3 permanecen bloqueados hasta una
  decisión específica de privacidad y proveedor seguro.
- **FR-008:** ninguna operación de escritura o rollback puede escapar del
  workspace mediante traversal o symlinks, quedar en un walk infinito ni actuar
  sobre precondiciones cambiadas; attachment, setup, receipts y artefactos
  relacionados deben publicarse de forma atómica o dejar un journal o
  compensación recuperable y verificable.
- **FR-009:** el contrato público Python debe quedar acotado a
  `>=3.11,<3.14`; la suite canónica debe ejecutarse en 3.11, 3.12 y 3.13, y la
  documentación y distribución deben declarar exactamente ese rango.
- **FR-010:** cada defecto reproducido debe contar con una prueba adversarial de
  regresión y el conjunto completo de tests y gates debe terminar en verde sin
  rebajar controles existentes.

## Criterios de éxito

- **SC-001:** un agente es rechazado con cada alias observado de verificación de
  outcome y un delegante no puede conceder una capacidad fuera de su autoridad
  efectiva.
- **SC-002:** cuando la policy esperada exige aprobación, un receipt que declara
  `required=false` no la desactiva; una aprobación de otra iniciativa o de un
  actor sin capacidad `approve` es inválida aunque hashes e ids sean correctos.
- **SC-003:** cualquier debilitamiento de aprobación, antigüedad, excepciones o
  sensibilidad se reporta como no aplicable junto con la dimensión violada.
- **SC-004:** un perfil con un control ficticio o sin enlace completo a
  implementación, test y gate no puede resolverse como conforme.
- **SC-005:** mover un gate mínimo fuera de pre-push o CI deja el registro en
  rojo; el hook inspecciona cada rango anunciado y KOM compara snapshots base y
  head distintos cuando existe una transición.
- **SC-006:** el handoff acepta reposo solo con la última feature cerrada, el
  número retirado 006 conserva un tombstone resoluble, las relaciones ADR son
  válidas y todo SC de una feature cerrada enlaza tarea, verificación y evidencia.
- **SC-007:** guardar T2/T3 falla antes de crear contenido; los artefactos locales
  soportados usan permisos restrictivos y la salida CLI no contiene el valor
  persistido.
- **SC-008:** rutas externas o enlazadas se rechazan, `.` termina sin loop, un
  rollback con receipt o destino mutado se detiene y la inyección de una falla
  en cada escritura multiarchivo no deja un conjunto parcialmente publicado sin
  journal o compensación verificable.
- **SC-009:** CI ejecuta la suite en Python 3.11, 3.12 y 3.13; metadata,
  documentación y build/export declaran `>=3.11,<3.14` y sus referencias
  internas permanecen resolubles.
- **SC-010:** las pruebas adversariales nuevas reproducen los fallos previos,
  pasan con el enforcement corregido y `scripts/test.sh` y
  `scripts/validate.sh` finalizan en verde.

## Frontera de claims

T0 técnico. La evidencia de esta feature puede probar contratos y ejecución
local sobre el commit observado. No prueba identidad externa, confidencialidad
del host, firma, operación remota, publicación, adopción ni outcomes.

## Clarifications

1. **Alcance:** la instrucción humana comprende todas las mejoras derivadas de
   los defectos reproducidos; se implementarán en una sola feature ordenada por
   riesgo, sin declarar cierre parcial como cierre total.
2. **Autoridad:** `Principal Architect` fue confirmado explícitamente como owner
   humano y futuro aprobador. La confirmación de identidad no acepta todavía el
   contenido de ADR-0014 ni el plan o las tareas.
3. **T2/T3:** esta feature no inventa cifrado, custodia o proveedor. Esos tramos
   se rechazan antes de persistir y requieren una decisión posterior específica;
   T0/T1 conservan la memoria local no autoritativa.
4. **Compatibilidad y release:** se preservan entradas públicas válidas y se
   endurecen rutas que contradicen el contrato. Los nuevos registros justifican
   Core 3.2.0 y Python queda acotado al rango probado; esto no crea tag, release
   ni publicación.
5. **Criterio de término:** ningún hallazgo se considera resuelto solo por
   documentación. Cada SC requiere regresión ejecutable y evidencia; el cierre
   exige la suite y los gates completos en verde.
