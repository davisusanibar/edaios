# Integración de iniciativas y consumers

Una iniciativa declara namespace, owners, versión/digest Core, source, autoridad,
sensibilidad, policy profile y gates. La relación es contractual por archivos:
no requiere importar Core en su runtime.

```text
Foundation → Core public contract → initiative attachment → consumer
       gates/receipts ←───────────────────────────────────────┘
```

La iniciativa conserva implementación, canon y evidencia durable. Core conserva
gobierno, schemas y conformance; no ejecuta el data plane. El attachment se
valida con `initiative-adoption`. `federation` solo aplica a mounts ya gobernados
y produce una vista derivada.

Crear un attachment desde template no actualiza `repositories.json` ni
`edaios.lock.json` de Core y no instala un consumer.
