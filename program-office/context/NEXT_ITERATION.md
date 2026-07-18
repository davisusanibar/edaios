# NEXT_ITERATION

Core 3.1.0 queda como baseline portable de raíz única bajo ADR-0013. La feature
`008-core-baseline-normalization` cerró la coherencia de estado, handoff, demo,
genealogía y gates sin alterar la API funcional ni inventar publicación.

El siguiente cambio debe ser un piloto real, pequeño, actual y gobernado:

1. partir de una necesidad y un owner reales;
2. abrir una feature Spec Kit con fuentes y límites explícitos;
3. completar InitiativeManifest, autoridad, sensibilidad y PolicyProfile sin
   copiar fixtures como verdad;
4. decidir mediante ADR cualquier nueva frontera, incluido el primer consumer;
5. ejecutar `initiative-adoption` y crear el módulo únicamente después de
   aprobar contrato y plan;
6. medir onboarding y evidencia con fuente antes de abrir un segundo piloto;
7. no crear dominios, productos, portal o infraestructura por anticipación.

Ningún trabajo futuro hereda outcomes, owners, receipts o fuentes de otra
genealogía. Un release futuro nace mediante una feature propia y un candidato
explícito; el baseline no se auto-promueve. Engram runtime, una rama `vNext`,
dominios y consumers no se crean por anticipación.
