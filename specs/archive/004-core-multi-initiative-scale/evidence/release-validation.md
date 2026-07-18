# Evidencia de Core 2.0.0

Fecha de validación: **2026-07-15**

Scope: Foundation y Core 2.0.0 local; schemas, perfiles, harnesses, receipts,
federación sobre fixtures, CLI, distribución reproducible y gates. Ninguna
iniciativa, runtime, registry o firma externa instalada.

| Control | Resultado | Evidencia observada |
|---|---|---|
| Gramática y gobierno | PASS | RFC de cuatro dígitos, seis ADR aceptados, un RFC ratificado, catálogos dinámicos y 7 pruebas de gobierno verdes. |
| KOM-VR-01..11 | PASS | 41 KOs; once reglas ejecutadas individualmente; 0 errores y 0 avisos. |
| Core conformance | PASS | Perfiles `core-release`, `initiative-adoption` y `federation` acumulativos; 9 schemas, 4 templates y 12 harnesses verificados. |
| Harnesses y receipts v2 | PASS | 23 pruebas de conformance cubren operaciones positivas/negativas, autoridad humana, digests, tampering, staleness, base/head y reversa. |
| Federación explícita | PASS | 13 pruebas cubren mounts/namespaces, root autorizado, colisiones, referencias, traversal y symlinks fail-closed. |
| Distribución y supply chain local | PASS | Dos wheels limpios idénticos; checksum, SBOM CycloneDX-like y provenance local verificados; todos los paquetes públicos importan como 2.0.0. |
| Tests | PASS | 48/48 pruebas unitarias, contractuales, de integración y adversariales. |
| Validate | PASS | 11/11 gates pre-push; Spec Kit 156/156; demo offline cerrada 16/16. |

## Comandos observados

```text
python3 tools/publishing/compile_constitution.py --check
python3 tools/publishing/sync_spec_kit_integrations.py --check
python3 tools/validation/spec_kit_gate.py . --profile federation
python3 tools/validation/kom_gate.py .
python3 tools/validation/monorepo_structure_check.py . --require-git
python3 tools/validation/traceability_check.py . --profile federation
python3 tools/validation/baseline_surface_check.py . --profile federation
python3 tools/validation/core_conformance_check.py . --profile federation
python3 tools/validation/claim_surface_check.py .
python3 tools/validation/core_distribution_check.py .
./scripts/test.sh
./scripts/validate.sh
```

## Límite de la evidencia

El sello demuestra contratos locales sobre los bytes y fixtures observados.
No demuestra adopción organizacional, verdad o datos institucionales, identidad
o firma externa, publicación, registry, operación remota, seguridad de
producción, rendimiento, disponibilidad ni outcomes. Los digests locales
demuestran integridad y reproducibilidad; no identidad ni no repudio.
