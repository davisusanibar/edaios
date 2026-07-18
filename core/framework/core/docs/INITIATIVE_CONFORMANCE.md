# Conformidad de iniciativas

## Attachment mínimo

Una iniciativa entrega documentos conformes a los schemas públicos de Core:

- InitiativeManifest y PolicyProfile;
- AuthorityRegistry y delegaciones aplicables;
- SensitivityProfile o referencia a un tramo Core;
- ExceptionRecord solo cuando corresponda;
- EvidenceReceipt y ApprovalReceipt separados;
- Outcome únicamente con owner, baseline y fuente reales.

El punto de partida público es
`../templates/initiative/edaios.initiative.json`; sus documentos asociados
están en el mismo directorio. Son plantillas T0, no una adopción preaprobada.

## Perfiles acumulativos

```text
core-release
    ↓ agrega contratos de attachment
initiative-adoption
    ↓ agrega mounts, namespaces y colisiones
federation
```

La resolución fail-closed rechaza ciclos, perfiles desconocidos y un hijo que
retire controles. Una política de iniciativa puede ser más estricta; nunca
menos.

## Ownership

- Principal Architect: Foundation y Constitución.
- Core Maintainer: schemas, profiles, gates y compatibilidad.
- Sponsor/Value Owner: prioridad y outcome.
- Domain/Data Owner: fuentes, semántica y sensibilidad.
- Delivery Lead: ejecución dentro del contrato.
- Revisor independiente: riesgo, arquitectura, seguridad o privacidad.
- Orquestador/agente: coordinación dentro de una delegación, sin aceptación.

El baseline distribuye fixtures T0 ilustrativas. Ninguna representa una
iniciativa institucional ni reserva owner, fuente u outcome.
