# Gramatica de artefactos SDD

## Tipos comunes

| Tipo | Identidad | Relacion principal |
|---|---|---|
| Intent | `INT-*` | origina una Feature |
| WorkRequest | `REQUEST-*` | se clasifica como RouteDecision |
| FeatureSpec | `SPEC-*` | contiene Requirements |
| Decision | `ADR-NNNN` / `RFC-NNNN` | gobierna una FeatureSpec |
| Plan | `PLAN-*` | implementa Requirements y delega trabajo |
| Task | `TASK-*` | descompone un Plan |
| Delegation | `DELEG-*` | acota un executor |
| TestEvidence | `TEST-*` | verifica un Requirement |
| PhaseResult | `RESULT-*` | concluye una Phase contra un commit |
| VerificationReport | derivada del result | acepta o rechaza evidencia |
| ArtifactRecord | `ART-*` | registra una salida material |
| MemoryRecord | `MEM-*` | conserva working o canonical memory |
| SkillFeedback | `SKILLFB-*` | evalua resolucion de skills |
| RollbackPlan | `ROLLBACK-*` | protege una publicacion |
| ArchiveManifest | `ARCHIVE-*` | cierra un run sin borrar evidencia |
| TelemetryEvent | `EVENT-*` | observa una decision del control plane |
| Outcome | `OUT-*` | evalua valor de una Feature |

## Reglas

1. Toda identidad es estable y los records inmutables evolucionan por
   supersesion.
2. Toda relacion apunta a una identidad resoluble o a una URI con digest.
3. `candidate` no equivale a `accepted`; solo el receipt v2 aceptado alimenta el
   State Reducer.
4. Evidencia y artefactos registran path y SHA-256; un expected head distinto
   invalida el resultado.
5. Un human gate requiere actor humano aunque CI o un agente prepare evidencia.
6. MemoryRecord `accepted` requiere decision, actor y fuente ligada a commit.
7. ArchiveManifest cierra; no elimina recibos, memoria ni artefactos.

El recurso ejecutable vive en
`../../modules/conformance-core/src/edaios_conformance/resources/artifact-grammar.json`.
La gramática de gobierno vive en `../profiles/governance-grammar.json`; templates
y gates deben derivar de ella.
