# Plan

## Constitution Check

Constitucion verificada: sha256:d57078593e5a78bb302e45cea9f5cc5d581be0c6ab8cbb8c751435febd5fb327

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
