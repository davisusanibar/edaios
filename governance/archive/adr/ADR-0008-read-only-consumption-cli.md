# ADR-0008 — Superficie CLI de consumo de solo lectura

**Estado:** Aceptado
**Fecha:** 2026-07-16
**Owner:** Principal Architect

## Contexto

El wheel `edaios-core` embarca `KnowledgeClient` y `QueryEngine`, pero la CLI
no expone consulta de conocimiento ni análisis de impacto. Un operador o un
agente de iniciativa que no embebe Python inventaría scripts divergentes para
leer el mismo contrato.

## Decisión

`edaios-core` incorpora subcomandos de consumo estrictamente read-only como
paridad del contrato Python ya distribuido: `kos list|get` sobre
`KnowledgeClient` y `query find|impact|neighborhood` sobre `QueryEngine`. Toda
salida usa el sobre JSON estable `edaios.cli-output/v1` y declara su
`claim_boundary`: la consulta local no confiere autoridad, aceptación ni
publicación. Los subcomandos no escriben estado, no descubren mounts
implícitos y fallan cerrado ante identidades no resolubles.

## Alternativas

- dejar la API Python como única superficie: excluye agentes y operadores
  shell y multiplica wrappers no gobernados;
- integrar `impact()` dentro del gate SDD: rechazada; el gate permanece sin
  dependencias y el análisis de impacto informa, no decide.

## Consecuencias

Cada iniciativa consume el mismo punto de entrada y el mismo schema de salida.
La CLI sigue el invariante del control plane: valida y prepara; no acepta,
mergea ni publica.

## Evidencia y frontera del claim

Tests contractuales prueban la salida, el sobre y la frontera en local. No
prueban adopción, integraciones externas ni operación remota.

## Aprobación

Principal Architect · 2026-07-16 · instrucción humana expresa de ejecutar los
pendientes del roadmap multi-iniciativa.
