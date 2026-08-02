# Adapter SDD (`sdd-adapter`)

Borde de interoperabilidad entre EDAIOS (control plane) y las herramientas de delivery SDD externas (ADR-0022, contrato de ADR-0022). Sin dependencias externas (stdlib): la herramienta externa se invoca al borde, pineada; este código es nuestro. El núcleo de conocimiento sigue autocontenido (invariante matizado por ADR-0022/PAT-003).

- **Aguas arriba:** `export_context_bundle` / `seed_speckit_constitution` — proyecta
  la Constitución compilada y agrega el contexto gobernado del dominio sin requerir
  el runtime EKG.
- **Aguas abajo:** `ingest_artifact` — escribe artefactos externos como
  **borradores** en `.edaios/drafts/` con herramienta, versión, ruta y SHA-256;
  promoción humana + ADR.

Spec Kit 0.15.1 es el perfil operativo aceptado por ADR-0022; ADR-0022 conserva
el piloto histórico 0.11.0. El paquete `spec-kit/` contiene preset, extensión,
workflow y bundle locales. Las primitivas se instalan por sus mecanismos
nativos; el bundle fija sus versiones y las registra como una unidad. Los gates
locales comprueban paridad y coherencia del contenido. La validación contra un
catálogo remoto, publicación o instalación mediante el CLI oficial no se reclama
hasta que exista evidencia separada de esa operación.

## `inject-consumer.sh` — inyección de un consumer

Automatiza las 4 capas de inyección en un proyecto externo, idempotente y
fail-closed:

```bash
inject-consumer.sh --workspace DIR --id ID --namespace NS \
                   --owner OWNER --value-owner VALUE_OWNER [--core DIR]
```

- **A** instala/verifica `edaios-core`; **B** proyecta la Constitución
  (`seed_speckit_constitution`) y crea/valida el attachment de iniciativa
  (`initiative-adoption`); **C** instala el bundle Spec Kit gobernado y vendoriza
  el gate con un `SOURCE.md` de procedencia; **D** aplica la memoria de agente en
  `CLAUDE.md`.
- El consumer queda listo para validar features con el perfil `consumer-release`
  (ADR-0016): `spec_kit_gate.py . --feature <dir> --profile consumer-release`.
- **Interim (RFC-0002):** copia el gate y el `integrations.lock.json` porque hoy
  no viajan en el wheel ni en el bundle. Al shipear el gate por el adapter, esas
  copias desaparecen del script.
- Frontera: crea artefactos locales en estado borrador; no acepta, commitea ni
  publica (Artículo VI, ADR-0005).
