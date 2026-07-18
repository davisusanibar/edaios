# RFC-0001 — ¿Cómo escala Core sin absorber las iniciativas?

**Estado:** Ratificado
**Fecha:** 2026-07-15
**Owner:** Principal Architect
**resolved_by:** ADR-0004, ADR-0005, ADR-0006

## Problema

Core Base conserva una frontera agnóstica, pero sus gates certifican una
topología cerrada y varios contratos de autoridad, evidencia, seguridad y
federación permanecen narrativos. Incorporar cada iniciativa dentro de Core
destruiría portabilidad y autoridad local; conservar solo documentación no
permitiría validar adopción de forma repetible.

## Opciones y trade-offs

1. **Core monolítico con packs por tecnología.** Simplifica el primer arranque,
   pero acopla runtimes, owners y ciclos de release al kernel.
2. **Kernel + contrato de iniciativa + perfiles acumulativos.** Core publica
   schemas y conformance; cada iniciativa conserva implementación y canon local.
   Requiere versionado, namespaces y evidencia interoperable.
3. **Templates sin enforcement.** Mantiene Core pequeño, pero desplaza la
   coherencia a revisión manual y hace que la adopción derive entre equipos.

## Impacto y reversibilidad

La opción 2 añade contratos y validadores sin instalar consumers. Es reversible
por versión: los perfiles y schemas se publican con SemVer y no alteran la
autoridad de repositorios ya existentes. Una futura plataforma solo consumirá
receipts e índices derivados.

## Plan de evidencia

- contract tests de manifests, políticas, autoridad, receipts y excepciones;
- conformance de `core-release`, `initiative-adoption` y `federation`;
- fixtures ilustrativas temporales, sin registrar una iniciativa institucional;
- distribución reproducible con checksum, SBOM y provenance local;
- frontera explícita para firma, publicación y operación remota no instaladas.

## Recomendación

Adoptar la opción 2. Mantener Foundation central, Core versionado y cada
iniciativa en su propio scope Git; federar únicamente vistas derivadas mediante
mounts explícitos y namespaces globales.

## Resolución

Ratificado por instrucción humana de implementar el plan completo. La decisión
se materializa en ADR-0004, ADR-0005 y ADR-0006.
