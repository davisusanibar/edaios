# NEXT_ITERATION

Core 3.1.0 queda como baseline portable de raíz única bajo ADR-0013, con hogar
canónico GitHub por ADR-0017. La feature `009-core-trust-boundary-hardening`
cerró el hardening fail-closed de autoridad, receipts, perfiles, filesystem y
gobierno SDD sin alterar la API funcional ni inventar publicación.

RFC-0003 está Ratificado y ejecutado por completo, y el programa está en
idle: las quince features con spec del corpus están cerradas — catorce
archivadas bajo `specs/archive/`, la 006 retirada vía tombstone, y la 010
(reorganización de archivo histórico) como última cerrada en la raíz de
`specs/`, conforme a la regla de superficie del índice de archivo. Próximas decisiones del owner: vendor update Spec Kit,
receipts in-toto, y la review de VL-001 (2026-11-02 o segundo consumer).

El piloto real gobernado se materializó en la feature 016 (ADR-0020 resolvió
RFC-0002). Para el segundo consumer, la secuencia gobernada es:

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
