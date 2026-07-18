# Release y cutover de EDAIOS Core

Este procedimiento parte de un baseline instalado. El estado
`.specify/release.json` puede declarar que no existe candidato; eso es un
resultado válido y no equivale a una release.

Commit, push, tag, protección, publicación y cambio de configuración del
proveedor requieren autorización explícita y evidencia observable.

## 1. Abrir una feature de release

1. Declarar versión, alcance, owner, reversa y frontera de claims.
2. Registrar ADR cuando cambie una frontera estructural o de compatibilidad.
3. Crear contratos propios de la versión bajo la feature: PolicyProfile,
   AuthorityRegistry y GitCutoverTarget.
4. Seleccionar esos paths explícitamente; nunca reutilizar manifest, policy,
   authority, target o receipts de otra versión.

Sin feature y contratos aprobados, el release gate debe permanecer en
`baseline-no-candidate` con `promotion_allowed: false`.

## 2. Preparar el candidato determinista

1. Ejecutar `./scripts/test.sh`, `./scripts/validate.sh` y `./scripts/ci.sh`.
2. Generar el manifest mediante un path relativo explícito como último derivado
   antes del commit.
3. Confirmar versión, inputs, tree base, wheel, export, checksum, SBOM,
   provenance y comandos de validación.
4. Inspeccionar el diff y comprobar que el manifest excluye únicamente sus
   propios bytes para evitar autorreferencia.

El manifest declara `prepared`; no codifica limpieza, aprobación ni estado
remoto mutable.

## 3. Fijar el commit candidato

Crear un commit con fuentes, contratos y manifest. No regenerar el manifest
después: su `base_head` corresponde al estado observado durante la preparación.
El checker solo puede declarar `ready-for-approval` cuando el worktree está
limpio y el manifest coincide con el commit.

## 4. Aprobar localmente

El Principal Architect revisa alcance, reversa, evidencia y riesgo residual.
EvidenceReceipt y ApprovalReceipt son objetos separados. La verificación local
debe comprobar:

- mismo Core version y HEAD candidato;
- policy, authority y target canónicos de esa versión;
- contratos cubiertos por digest;
- sensibilidad permitida;
- aprobación humana reciente y autoridad resoluble.

`locally-approved` no afirma push, tag, protección, default branch o
publicación.

## 5. Observar el cutover remoto

Solo con autorización explícita:

1. ejecutar todos los gates sobre el commit candidato;
2. avanzar la rama canónica sin reescribir historia;
3. crear el tag de la versión sobre el mismo commit;
4. observar los checks CI requeridos y branch protection;
5. conservar evidencia durable del proveedor con URI, digest y tamaño;
6. publicar EvidenceReceipt y ApprovalReceipt en un destino permitido;
7. materializar un GitCutoverReceipt que enlace commit, tree, rama, tag,
   checks, protección, default branch, evidencias y observer autorizado;
8. ejecutar el checker con `--require-final-seal` y todos los contratos
   explícitos.

Solo ese resultado puede declarar `sealed-by-authorized-observation`. El
checker verifica la evidencia aportada; no consulta al proveedor en vivo ni
produce firma criptográfica externa.

## 6. Reversa

Antes del cutover, retirar el candidato sin debilitar contratos. Después del
cutover, restaurar la ref aprobada anterior y registrar la incidencia. Nunca
reutilizar un tag, mezclar genealogías o alterar receipts para forzar un estado.

## Frontera

Este procedimiento demuestra identidad y reproducibilidad hasta el alcance de
la evidencia observada. No demuestra registry, adopción, producción,
rendimiento, disponibilidad, firma externa u outcomes.
