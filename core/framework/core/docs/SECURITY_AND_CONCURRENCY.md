# Seguridad y concurrencia del control plane

## Principios

- deny by default y least privilege por fase;
- un branch y worktree por unidad concurrente;
- resultados inmutables e idempotentes;
- locks locales para writers cooperativos;
- Git, PR y CI para concurrencia distribuida;
- secrets y PII fuera de memoria y telemetria.

## Capabilities

`../profiles/security-policy.json` define capacidades por fase. El host valida
actor y `DelegationGrant` y recibe allowed/denied; la ausencia de grant deniega.
En modo controlled se niegan red no acotada, lectura de credenciales, force push
y merge sin gate. Los human gates no admiten como aprobador a CI o un agente.

## Concurrencia

| Frontera | Mecanismo | Limite |
|---|---|---|
| Mismo proceso | estructuras in-memory | no persiste |
| Mismo worktree | lock cooperativo + atomic write + CAS | solo writers EDAIOS |
| Worktrees locales | branch, base SHA, path isolation | filesystem compartido |
| Maquinas distintas | Git, PR, CI, CODEOWNERS | concurrencia optimista |
| Memoria entre agentes | puerto externo futuro | no concede autoridad |

El lock local no se presenta como lock distribuido. EvidenceReceipt v2 lleva base/head
SHA para detectar staleness; la integracion final sigue protegida por el host Git.

## Review budget y chain

El repositorio configura límites internos por riesgo en
`../profiles/review-policy.json`.
No son un benchmark de industria. Cuando una superficie excede el presupuesto,
el harness recomienda unidades menores y `stacked` si existen dependencias. Cada
unidad conserva un veredicto y rollback propios.

## Rollback y cierre

Un run publicable requiere `RollbackPlan` con target, base SHA, owner, trigger,
steps y evidence. `ArchiveManifest` inventaria resultados, artefactos y rollback
por digest. Archivar no borra ni muta recibos previos.

El lifecycle del propio Core aplica la misma regla. Upgrade prepara un plan,
verifica versión/digest, escribe un transition receipt y vuelve a ejecutar
`core-release`. Solo una acción humana posterior puede reemplazar
`edaios.lock.json`. Rollback usa una entrada verificable del historial; no acepta
metadata reconstruida por el caller.

Un SHA-256 local prueba integridad respecto del contenido observado, no identidad
corporativa, firma criptográfica ni no repudio.
