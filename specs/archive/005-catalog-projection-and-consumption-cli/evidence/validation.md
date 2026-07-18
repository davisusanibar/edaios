# Evidencia de validación

Fecha: **2026-07-16** · Alcance: local, sin publicación.

| Control | Resultado | Observado |
|---|---|---|
| Tests unitarios y contractuales | PASS | 55 tests OK, incluidos catálogo (2) y CLI de consumo (2). |
| CATALOG-PROJECTION | PASS | `--check` reproduce ambos catálogos byte a byte. |
| Corpus inválido | PASS | Duplicado, heading ajeno y estado inválido producen `CatalogError`. |
| CLI kos/query | PASS | Sobre `edaios.cli-output/v1` con frontera; id no resoluble → `blocked`, exit 2. |
| CLAIM-SURFACE | PASS | 14 claims · 12 enforced; markers de ambos claims demostrados. |
| Gates pre-push | PASS | 12 gates en verde vía `scripts/validate.sh`. |

## Límite de la evidencia

Demuestra proyección, consulta local y contratos. No demuestra adopción,
iniciativas reales, distribución pública ni operación remota. Commit y push
requieren autorización explícita separada.
