# ADR-0006 — Federación explícita, compatibilidad y supply chain verificable

**Estado:** Aceptado
**Fecha:** 2026-07-15
**Owner:** Principal Architect
**Deriva de:** RFC-0001

## Contexto

La consulta actual descubre rutas de forma implícita y puede ocultar colisiones.
El release es privado y local; no existe aún un contrato completo de upgrade,
deprecación, SBOM, provenance o firma externa.

## Decisión

La federación usa mounts declarados y namespaces globales; nunca `rglob` abierto
como autoridad. IDs duplicados, tipos incompatibles y referencias no resolubles
fallan cerrado. El Git de cada iniciativa permanece canónico y el índice
federado es regenerable.

Core publica una política de compatibilidad, schemas versionados, ventana de
deprecación y receipts de migración/reversa. Cada distribución local produce
checksum, SBOM y provenance verificables. Registry, firma externa y publicación
requieren infraestructura y autorización posteriores; su ausencia bloquea el
claim, no la validación local.

## Alternativas

- descubrimiento recursivo implícito: rechazado por mezcla accidental;
- índice central como autoridad: rechazado por invertir Git-first;
- afirmar supply chain firmada con hashes locales: rechazado por claim falso.

## Consecuencias

Iniciativas independientes pueden compartir Core y proyectar conocimiento sin
ceder autoridad. Upgrades y reversas tienen contratos explícitos. La plataforma
organizacional puede añadirse después como consumer derivado.

## Evidencia y frontera del claim

Fixtures locales prueban mounts, colisiones, compatibilidad y artefactos de
distribución. No prueban registry, firma, despliegue o federación remota.

## Aprobación

Principal Architect · 2026-07-15 · autorización humana expresa de esta
implementación gobernada.
