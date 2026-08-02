# NEXT_ITERATION

Core 3.1.0 queda como baseline portable de raíz única bajo ADR-0013, con hogar
canónico GitHub por ADR-0017. La feature `009-core-trust-boundary-hardening`
cerró el hardening fail-closed de autoridad, receipts, perfiles, filesystem y
gobierno SDD sin alterar la API funcional ni inventar publicación.

La dirección vigente es RFC-0003 (adopciones gentle-ai y práctica
multi-agente), en ejecución por orden: 011 CI remota y estado vigente, 012
cierre de contratos resolubles, 013 sdd-status máquina, 014 revisión
adversarial preparada, 015 onboarding de consumer real. La feature 010
(reorganización de archivo histórico) permanece propuesta en cola y ortogonal.

El piloto real gobernado sigue siendo la prioridad estratégica y se materializa
como la feature 015 (ADR-0020 resolvió RFC-0002):

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
