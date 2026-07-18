# EDAIOS Validator

Los gates se resuelven mediante perfiles acumulativos:

- `core-release`: proyección Foundation, gobierno/KOM, contrato SDD, harnesses,
  claims, distribución reproducible, demo y tests;
- `initiative-adoption`: hereda Core y exige manifest, autoridad, sensibilidad,
  política y evidencia del attachment;
- `federation`: hereda adopción y exige mounts explícitos, namespaces,
  identidades inequívocas y relaciones resolubles.

Cada hijo agrega controles y no puede retirarlos. El validador falla cerrado
ante warning, schema desconocido, mount implícito o deriva entre superficie
pública y paquete. Un PASS demuestra el contrato del perfil seleccionado: no
acepta una decisión, no instala una iniciativa y no prueba producción.
