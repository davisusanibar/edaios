# ADR-0014 — Hardening fail-closed de las fronteras de confianza de Core

**Estado:** Aceptado
**Fecha:** 2026-07-16
**Owner:** Principal Architect

## Contexto

La revisión adversarial local del baseline Core 3.1.0 encontró rutas donde un
contrato declarativo puede divergir de su enforcement: vocabularios de acciones
distintos, verificación parcial de políticas y autoridad, herencia que solo
compara controles, gates desplazables por `scope`, hooks que observan el
worktree en lugar de los objetos enviados y memoria local que acepta tramos para
los que Core no instala almacenamiento seguro.

También existen vacíos de gobierno mecánico: los perfiles admiten controles sin
implementación demostrable, la cadena SC → tarea → gate/test → evidencia no es
exigida, el handoff no representa reposo, una feature retirada carece de
tombstone y las relaciones entre decisiones no tienen validación tipada.

Estos defectos no autorizan una iniciativa, un runtime, un proveedor ni claims
de producción. Exigen fortalecer el kernel y sus gates conservando
`Foundation → Core`.

## Decisión propuesta

Core adoptará los siguientes invariantes acumulativos y fail-closed:

1. Un único vocabulario canónico identificará capacidades y acciones
   reservadas. Las variantes desconocidas se rechazan; un agente nunca puede
   aprobar, aceptar riesgo ni verificar outcomes.
2. Una delegación no puede ampliar las capacidades, el scope ni la vigencia de
   quien delega. La autoridad efectiva se calcula dentro de la misma iniciativa.
3. Un EvidenceReceipt se verifica contra toda la PolicyProfile esperada, no
   solo contra su identidad y digest. Los parámetros del caller solo pueden
   endurecerla. ApprovalReceipt debe corresponder al mismo receipt e iniciativa
   y a una persona activa con rol y capacidad `approve` explícitos.
4. La monotonía de políticas cubre parent, controles, aprobación, antigüedad
   máxima, excepciones y sensibilidad. Un perfil solo agrega controles a sus
   padres. Todo control debe resolver en un registro versionado hacia
   implementación, test y gate; un control ficticio falla.
5. El registro SDD de gates fija ids, comandos y scopes mínimos. El runner valida
   el registro antes de seleccionar; pre-push consume las refs de Git y verifica
   cada objeto local en un worktree aislado, y los checks de transición reciben
   base y head explícitos.
6. Spec Kit representa el reposo sin feature activa, conserva números retirados
   mediante tombstones, valida relaciones ADR y exige la cadena completa
   requisito/criterio → tarea → gate/test → evidencia antes del cierre.
7. La memoria local instalada admite únicamente los tramos para los que existe
   un contrato de almacenamiento verificable. T2/T3 fallan antes de persistir o
   imprimir contenido hasta una decisión específica de privacidad y proveedor.
   Los directorios y archivos locales usan permisos mínimos y la CLI redacta
   valores sensibles.
8. Toda escritura local verifica contención física, rechaza symlinks en la ruta,
   es atómica y vuelve a verificar precondiciones dentro del lock antes de
   rollback. Las operaciones multiarchivo de attachment, setup y receipts usan
   staging, journal o compensación verificable. Los walks terminan incluso con
   la raíz o `.`.
9. El contrato Python se acota a `>=3.11,<3.14` y CI ejecuta 3.11, 3.12 y 3.13;
   distribución y documentación se derivan del mismo rango. El hardening añade
   pruebas adversariales sin introducir dependencias, servicios o autoridad
   externa.
10. La adición de registros y contratos de lifecycle se identifica como Core
    3.2.0, incremento MINOR. Esa identidad no autoriza tag, release ni
    publicación.

ADR-0014 enmienda la frontera de persistencia local de ADR-0011 y precisa el
enforcement de ADR-0002, ADR-0004, ADR-0005 y ADR-0012; no los sustituye
íntegramente. La proyección de relaciones deberá distinguir enmienda, reemplazo
y derogación.

## Relaciones

- Amends: ADR-0002, ADR-0004, ADR-0005, ADR-0011, ADR-0012

## Alternativas

- corregir solo los casos reproducidos: rechazada porque permitiría nuevas
  divergencias entre contrato y enforcement;
- admitir T2/T3 con permisos de filesystem como control suficiente: rechazada;
  esos permisos no instalan cifrado, custodia, retención ni autorización;
- confiar en CI o en el hook como autoridad: rechazada; ambos verifican objetos,
  pero una persona autorizada conserva la aceptación;
- crear un proveedor seguro dentro de esta feature: rechazada por ampliar el
  producto y requerir decisiones de privacidad, operación y costo ausentes.

## Compatibilidad y migración

EvidenceReceipt conserva su schema actual y la lectura de handoff admite la
versión previa durante la migración; los nuevos enlaces de control y
trazabilidad son aditivos. Se mantiene compatibilidad para entradas válidas;
comportamientos antes aceptados por omisión y contrarios al contrato pasan a
fallar cerrado. El contrato Python deja de prometer versiones futuras no
probadas y queda acotado al rango ejecutado. Las features cerradas permanecen
resolubles y una retirada se registra como tombstone, nunca como conocimiento
borrado.

Core 3.2.0 identifica el contrato implementado, no una release publicada.
Cualquier tag o promoción requiere un proceso separado y evidencia observada.

## Consecuencias

La superficie local será más estricta: delegaciones amplificadas, receipts
parciales, perfiles inventados, scopes debilitados, pushes no inspeccionados,
rutas enlazadas y memoria T2/T3 serán rechazados. Los consumers que dependían de
esos comportamientos deberán corregir su configuración en lugar de recibir una
excepción implícita.

## Evidencia y frontera del claim

La suite puede demostrar enforcement local, trazabilidad mecánica, permisos de
archivos y compatibilidad en los intérpretes ejecutados. No demuestra identidad
corporativa, firma criptográfica, privacidad de producción, seguridad del host,
adopción, disponibilidad ni outcomes.

## Aprobación pendiente

Principal Architect · 2026-07-16 · aceptación humana expresa de ADR-0014, el
plan técnico y las tareas de la feature 009. No autoriza tag, push, release ni
publicación.
