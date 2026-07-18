# Arquitectura de Core

```text
Foundation
   ↓
Core kernel: schemas + profiles + harness + memory + SDD
   ↓
conformance + receipts + public Python/files
   ↓
initiative attachment (fuera de Core)
   ↓
adapter/runtime (fuera de Core)
```

Dependencias externas entran por puertos explícitos; ninguna es autoridad. El
grafo local permanece latente con un grafo vacío; una federación requiere mounts
y namespaces explícitos. No existe una iniciativa instalada; cuando aparezca,
dependerá del contrato público de Core sin introducir una dependencia inversa.

Un catálogo o índice organizacional será una proyección reconstruible. Ninguna
vista federada puede aceptar decisiones ni sustituir el Git canónico del owner.
