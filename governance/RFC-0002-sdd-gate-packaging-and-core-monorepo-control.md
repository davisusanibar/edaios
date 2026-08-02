# RFC-0002 — ¿Cómo se entrega y selecciona el gate SDD para un consumer sin vendorizar copias ni decidir por nombre de perfil?

**Estado:** Ratificado
**Fecha:** 2026-07-17
**Owner:** Principal Architect
**resolved_by:** ADR-0020

## Problema

ADR-0016 introdujo `consumer-release`: un consumer valida su contrato SDD con el gate
`tools/validation/spec_kit_gate.py` sin imitar una raíz Core. Funciona, pero dejó dos
deudas que su implementación resolvió con atajos, y que conviene cerrar antes de que haya
más de un consumer.

1. **El gate no se empaqueta.** `spec_kit_gate.py` no viaja ni en el wheel `edaios-core`
   ni en el bundle Spec Kit: vive en `tools/validation/` del repo de Core. Un consumer lo
   obtiene **vendorizando** una copia cruda (verificado en `data-kcd2026`), trazada solo por
   un sidecar de procedencia (`spec_kit_gate.SOURCE.md`). Es frágil: si Core evoluciona el
   gate, cada consumer arrastra una copia que puede quedar vieja sin aviso. Agravante: el
   esquema del bundle Spec Kit solo declara `commands`/`hooks`/`presets`/`workflows` — **no
   tiene un tipo de componente para shipear un `.py`** —, así que la vía natural no existe
   sin tocar tooling externo.

2. **El modo estructural se elige por nombre, no por control.** El gate decide si exige el
   bookkeeping del monorepo con `structural = profile != "consumer-release"` — una allowlist
   por string, fail-closed pero tosca. El resto de EDAIOS decide por **controles declarados**
   en los `.profile.json`. Formalizar un control `core-monorepo` colisiona con seis puntos
   que fijan `{core-release, initiative-adoption, federation}` (`baseline_surface_check`,
   `monorepo_structure_check`, `traceability_check`, `core_conformance_check`,
   `spec_kit_gate` y el módulo empaquetado `edaios_conformance/profiles.py`) más la cobertura
   exacta del `control-registry.json`. Por eso ADR-0016 §6 lo dejó como seguimiento.

## Opciones y trade-offs

### Entrega del gate

- **A · El adapter siembra el gate.** Agregar `seed_gate()` a `edaios_sdd_adapter` (junto a
  `seed_speckit_constitution`) que copie el gate al consumer con procedencia, al inyectar.
  Reemplaza la copia manual por una versionada por el paquete; no toca los call sites de Core.
  Mediano-bajo. Sigue habiendo una copia en el consumer, pero su origen y versión quedan
  gobernados por el adapter.
- **B · Empaquetar el gate.** Moverlo al árbol del paquete y exponer
  `edaios-core sdd-gate --feature X --profile P`, y re-cablear los ~8 sitios de Core (gates,
  tests, comandos del preset, CI) para llamar al comando. Elimina toda copia, pero es
  mediano-grande y toca el corazón del self-gating de Core.
- **C · Status quo.** Vendorizar + sidecar. Cero cambio de Core; máxima fragilidad y
  mantenimiento manual por consumer.

### Selección de modo estructural

1. **Control `core-monorepo` de primera clase.** Registrarlo en `control-registry.json`,
   declararlo en `core-release`, y que el gate lea el control en vez del nombre. Coherente con
   el modelo de controles, pero exige un cambio atómico de los 6 puntos + el módulo empaquetado
   + la cobertura exacta del registry, con sus contract tests.
2. **Allowlist por nombre (status quo).** `profile != "consumer-release"`. Simple y
   fail-closed, pero acopla la seguridad del gate a un string y no a una capacidad declarada.

## Impacto y reversibilidad

Ambos cambios son reversibles por versión (SemVer del paquete/perfiles) y no alteran la
autoridad de repositorios existentes. La opción A de entrega es aditiva (una función de
adapter); la B redefine cómo se invoca el gate y debe versionarse con cuidado. La opción 1 de
selección amplía el `control-registry` sin debilitar perfiles (ADR-0004): es monótona. Ningún
cambio instala consumers ni proyecta autoridad.

## Plan de evidencia

- contract tests de `seed_gate()`: el consumer recibe el gate con procedencia y hash del
  origen; una divergencia con la fuente falla;
- rojo/verde de `consumer-release` y `core-release` tras empaquetar, sin regresión en los 366
  checks de Core ni en la suite del gate;
- si se adopta el control `core-monorepo`: prueba de que el registry mantiene cobertura
  exacta, que los 6 puntos leen el control de forma consistente, y que apagar lo estructural
  sigue siendo exclusivo de `consumer-release` (fail-closed);
- distribución reproducible: el gate empaquetado entra en el SBOM/provenance del artefacto.

## Recomendación

Incrementar en dos pasos, no en uno.

- **Entrega:** adoptar **A** (siembra por el adapter) como primer incremento — cierra el 90%
  del dolor (elimina la copia manual y el sidecar) sin desestabilizar Core. Dejar **B**
  (empaquetado + comando `edaios-core sdd-gate`) como evolución posterior cuando haya varios
  consumers que justifiquen re-cablear el self-gating.
- **Selección:** adoptar el control `core-monorepo` (opción 1) **solo** como cambio
  deliberado y atómico sobre los 6 puntos + el módulo empaquetado, con sus contract tests. Hasta
  entonces, la allowlist por nombre de ADR-0016 permanece como estado aceptado y fail-closed.

## Resolución

Ratificado por ADR-0020 (2026-08-01): entrega por siembra del adapter (opción A,
`seed_gate()` con procedencia) y allowlist por nombre conservada con gatillo de
revisión al segundo consumer. La materialización ejecutable corresponde a la
feature `specs/015-onboarding-de-consumer-real` (RFC-0003). El catálogo RFC se
regenera con `python3 tools/publishing/compile_catalogs.py --write`, no se edita
a mano (ADR-0007).
