# ADR-0003 — Core Base portable, módulo único y memoria Git-first

**Estado:** Aceptado
**Fecha:** 2026-07-15
**Owner:** Principal Architect

## Contexto

La base reusable debe poder validarse, distribuirse y evolucionar sin depender
de un consumidor, un dominio o un servicio externo.

## Decisión

Existe una raíz Git y un único módulo requerido: `core`. Foundation vive dentro
de `core/foundation/` como autoridad; Framework materializa contratos, harnesses,
templates, Spec Kit y gates. No se instala ningún consumer concreto.
Git es memoria durable; estado local es reconstruible y RAM es efímera. Cada
writer trabaja aislado. Escrituras gobernadas usan atomic write, locks o CAS
cuando comparten estado. Manifests, digests y receipts deben ser reproducibles.

Un consumer, dominio, registry, federación, memoria externa o proveedor CI solo
puede ingresar por necesidad actual, spec, owner, decisión cuando corresponda y
evidencia propia.

## Consecuencias

Los catálogos declaran exactamente Core. Una feature futura no puede crear
imports inversos, repositorios anidados ni convertir un template en instalación.

## Evidencia y frontera

Los gates prueban la topología local y contratos instalados, no distribución
pública ni interoperabilidad remota.

## Aprobación

Principal Architect · 2026-07-15 · instrucción humana de congelar Core Base.
