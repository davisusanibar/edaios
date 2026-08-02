# ADR-0017 — Hogar canónico GitHub y superficie de CI remota

**Estado:** Aceptado
**Fecha:** 2026-08-01
**Owner:** Principal Architect

## Contexto

ADR-0013 fijó el hogar Git canónico en `bitbucket.org/data_and_ia/edaiosv`. El
repositorio opera hoy con remoto `github.com/davisusanibar/edaios` (verificable con
`git remote -v`), y la única superficie de CI es `bitbucket-pipelines.yml`: los 14
gates declarados con scope `ci` en `.specify/gates.json` no se ejecutan en ningún
remoto real. El fail-closed depende del hook `pre-push` local, que requiere
instalación manual (`scripts/install-hooks.sh`), tal como admite
`docs/quick-start.md`. Operar en un hogar distinto del decidido, sin decisión que lo
respalde, contradice el Principio III (el canon crece por decisión). RFC-0003
documenta este hallazgo como D2.

## Decisión

El hogar Git canónico pasa a ser `github.com/davisusanibar/edaios`, rama `main`.
Esta decisión reemplaza únicamente la cláusula de hogar remoto de ADR-0013; su
genealogía portable de raíz única, la derivación `unique-reachable-root`, el
fail-closed ante clones shallow y todas sus fronteras de claims se conservan
íntegras.

Se autoriza `.github/workflows/` como superficie de ejecución remota de gates, con
requisitos obligatorios:

- checkout con historia completa (`fetch-depth: 0`): ADR-0013 falla cerrado en
  clones shallow y `kom_gate` consulta `git show HEAD:ruta`;
- verificación de integridad `GITHUB_SHA == git rev-parse HEAD`, equivalente a la
  que `bitbucket-pipelines.yml` ya declara para `BITBUCKET_COMMIT`;
- matriz Python 3.11, 3.12 y 3.13 ejecutando `scripts/ci.sh`, la misma entrada que
  la superficie Bitbucket — una fuente, muchas vistas también para CI.

Se autoriza además un job informativo de tamaño de diff por PR que reporte contra
`review_unit` de la política de revisión. Es no bloqueante: convertirlo en bloqueo
con una cifra concreta exige primero un baseline propio respaldado por el Value
Ledger (Principio IV: cero cifras sin fuente).

`bitbucket-pipelines.yml` se conserva como superficie secundaria mientras el espejo
exista: sigue siendo archivo requerido por `monorepo_structure_check.py`
(`REPOSITORY_INTEGRATIONS`). Retirarlo exigirá una enmienda futura que toque ese
check y este ADR; no se decide aquí.

## Alternativas

- mantener Bitbucket como canónico y tratar GitHub como espejo: rechazada; invierte
  la realidad operativa verificada y dejaría el CI remoto en un hogar donde el
  trabajo no ocurre;
- dual-home sin canónico único: rechazada; dos autoridades de igual rango violan el
  invariante de una sola fuente de autoridad por dominio;
- añadir el workflow de Actions sin enmendar ADR-0013: rechazada; ratificaría un
  re-homing por la vía de los hechos, exactamente lo que el Principio III prohíbe.

## Consecuencias

Los 14 gates de scope `ci` pasan a ejecutarse en el remoto real en cada push y PR.
La evidencia de aceptación de las features 011-015 (RFC-0003) puede citar runs
remotos verificables. `CURRENT_STATE.md` y todo KO que mencione el hogar Bitbucket
deben actualizarse en la feature 011 para no contradecir esta decisión. El espejo
Bitbucket queda sin garantía de frescura hasta que su retiro se decida.

## Evidencia y frontera del claim

Evidencia: `git remote -v` (remoto GitHub), ausencia de `.github/workflows/` en el
árbol actual, `bitbucket-pipelines.yml` presente, `.specify/gates.json` con 14
gates de scope `ci`. Frontera: este ADR no afirma release sellada, ni publicación,
ni adopción organizacional; no altera perfiles de conformidad ni controles; la
protección de rama y los secretos del remoto quedan fuera del claim hasta contar
con evidencia remota archivada.

## Aprobación

Principal Architect · 2026-08-01 · aprobación humana expresa del Owner en sesión
de trabajo: plan de evolución aprobado y orden explícita de continuar tras
revisión del resumen de decisiones. Borrador preparado por IA en la misma sesión.
