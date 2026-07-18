# ADR-0013 — Genealogía portable de raíz única y hogar canónico edaiosv

**Estado:** Aceptado
**Fecha:** 2026-07-16
**Owner:** Principal Architect

## Contexto

El baseline Core 3.1.0 debe trasladarse como un snapshot final a un repositorio
nuevo, sin heredar commits de trabajo. El contrato v1 de
`CoreReleaseState` embebía `root_commit` y `root_tree` dentro del propio árbol.
Un repositorio de un único commit no puede contener el hash de ese mismo commit
o de su árbol: modificar el manifest para escribirlos vuelve a cambiar el árbol
y produce una autorreferencia sin punto fijo.

Conservar el pin anterior haría que los gates dependieran de objetos ausentes en
la nueva genealogía. Usar `HEAD`, ceros o un sentinel ambiguo aparentaría una
verificación que no existe.

## Decisión

`edaios.core-release-state/v2` declara una genealogía portable:

```json
{
  "kind": "single-root",
  "root_derivation": "unique-reachable-root",
  "canonical_branch": "main"
}
```

El gate deriva el root desde el grafo Git alcanzable por `HEAD` y falla cerrado
si el repositorio es shallow, si hay grafts o replace refs, o si no existe
exactamente un commit sin padres. El reporte calcula y expone el commit y árbol
del baseline; esos valores son evidencia derivada, no inputs autorreferenciales.

El hash exacto se fija fuera del tree después del commit mediante la ref remota,
un tag o un receipt verificable. Esta derivación no convierte el baseline en
release: `publication` permanece `not-claimed` y `promotion_allowed` permanece
`false` sin candidato explícito.

El hogar Git canónico para la nueva genealogía es
`bitbucket.org/data_and_ia/edaiosv`, rama `main`. Su bootstrap puede crear
`main` como un único commit raíz después de tests y gates locales en verde y de
observar el remoto vacío. Crear un tag, afirmar publicación o sellar una release
continúa requiriendo el flujo de ADR-0010, CI y evidencia remota proporcional.

Esta decisión reemplaza únicamente el pin literal de genealogía y el hogar
remoto concreto descritos por ADR-0012. Se conservan su baseline 3.1.0, la
ausencia de candidato y todas sus fronteras de claims.

## Alternativas

- crear dos commits, snapshot más pin: válida pero innecesaria; agrega un estado
  intermedio inválido al baseline que se desea entregar como unidad;
- copiar los hashes de la genealogía anterior: rechazada porque los objetos no
  existirían en el repositorio nuevo;
- excluir el manifest al calcular un digest propio: rechazada porque crea otra
  identidad parcial y más débil que el grafo Git;
- instalar Engram o una iniciativa durante el cutover: rechazado; el adapter ya
  forma parte de Core, mientras el runtime y todo consumer siguen externos.

## Consecuencias

El mismo snapshot puede convertirse en un root verificable sin reescribir sus
archivos después del commit. Los clones completos calculan la misma raíz y el
mismo árbol. Los clones shallow y las genealogías manipuladas fallan cerrado.

El repositorio contiene la capacidad vNext acumulada bajo la versión Core
3.1.0, incluida memoria operativa, índice derivado, sesiones, conflictos y el
adapter Engram opcional. No existe una rama llamada `vNext`, Engram no se
instala y ningún runtime se declara operativo.

## Aprobación

Principal Architect · 2026-07-16 · autorización humana expresa para eliminar
la historia Git anterior, conservar el conocimiento final y publicar el
snapshot completo como raíz única de `edaiosv/main` por SSH.
