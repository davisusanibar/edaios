# Scripts

`test.sh` ejecuta tests Python de kernel, conformance, federation, supply chain y
la vista Core.
`validate.sh` ejecuta los gates scope `pre-push` declarados en
`.specify/gates.json` (una sola fuente de verdad). `install-hooks.sh` instala
el hook `pre-push` que ejecuta `validate.sh` antes de cada push. Son el
contrato CI neutral; no seleccionan consumer, runtime ni proveedor.
