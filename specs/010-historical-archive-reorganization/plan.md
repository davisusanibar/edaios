# Plan

## Constitution Check

Constitucion verificada: sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

| Principio | Veredicto | Evidencia |
|---|---|---|
| I | PASS | Git y fuentes conservan autoridad. |
| II | PASS | Foundation gobierna Core. |
| III | PASS | Spec Kit gobierna cambios. |
| IV | PASS | No se inventan claims ni owners. |
| V | PASS | Gates fail-closed. |
| VI | PASS | La IA prepara; el humano acepta. |
| VII | PASS | No se agrega runtime ni producto. |

## Gate Impact

CATALOG-PROJECTION, SDD-CONTRACT, TRACEABILITY, CORE-BASE-DEMO y TEST.

## Secuencia

1. Inventariar archivos y dependencias. [INGEST]
2. Crear índice y mover solo artefactos aprobados.
3. Regenerar derivados.
4. Ejecutar tests y gates. [GATES] [LEDGER] [SEAL]
