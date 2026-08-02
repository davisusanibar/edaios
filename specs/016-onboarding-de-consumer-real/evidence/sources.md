# Registro de fuentes · Feature 016

Observación local fechada el 2026-08-02 sobre el commit `4e25108` (worktree
limpio tras cerrar 015). Reproducciones locales; no assessment de producción.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | Instrucción humana de esta sesión | 2026-08-02 | Owner ordena continuar con la feature 016, última del roadmap RFC-0003 | No acepta artefactos aún no presentados |
| SRC-002 | `~/Documents/ddsa/wks/kcd/live/data-evolutionary/kcd-001/tools/validation/spec_kit_gate.{py,SOURCE.md}` | 2026-08-02 | Copia vendorizada pineada al commit `0c60544` por `inject-consumer.sh`; digest actual `8ef5f5ec…` vs gate vigente de Core `60365b02…` — deriva real tras las features 011-015 | La deriva es el baseline de VL-001; ningún aviso automático la detectaba |
| SRC-003 | `git -C data-evolutionary log/remote` | 2026-08-02 | Consumer real con historia propia: módulo `kcd-001` gobernado por EDAIOS SDD (features 001 revenue-ventana-cliente y 002 persistencia-iceberg), remoto github.com/davisusanibar/data-evolutionary | Repo del consumer: sus commits pertenecen a su owner; esta feature no commitea allí |
| SRC-004 | `core/framework/extensions/sdd-adapter/src/edaios_sdd_adapter/spec_kit.py` | 2026-08-02 | `seed_speckit_constitution` establece el patrón de siembra (root autoritativo → out_dir de delivery); no existe siembra del gate | `seed_gate()` espeja el patrón por ADR-0020 |
| SRC-005 | `governance/VALUE_LEDGER.md` | 2026-08-02 | Ledger vacío: "No hay outcomes registrados en el baseline"; campos declarados para entradas futuras | VL-001 es la primera entrada; su outcome queda en observación por regla del propio ledger |
| SRC-006 | `core/framework/docs/playbooks/` | 2026-08-02 | Numeración PLB-001..004 y PLB-006; el hueco PLB-005 está libre (sin tombstone) | PLB-005 lo ocupa el playbook de onboarding |
| SRC-007 | `git -C data-evolutionary remote -v` y `git -C edaios remote -v` | 2026-08-02 | Ambos remotos pertenecen al usuario `davisusanibar`: el owner del Core y el owner del consumer son la misma persona (Principal Architect); su orden de ejecutar la 016 constituye la confirmación del owner del consumer | Cuando los owners difieran, `force` pertenece solo al owner del consumer (PLB-005 paso 3) |
| SRC-008 | Árbol de `data-evolutionary` (verificado por el refutador) y `governance/RFC-0002` §1 | 2026-08-02 | Reconciliación de identidad: `data-kcd2026` existe como módulo Maven hermano de `kcd-001` SIN `tools/validation/` propio; la única copia vendorizada del gate que RFC-0002 describe (sidecar con pin `0c60544`) vive en `kcd-001` — las menciones de gobernanza a `data-kcd2026` referían al proyecto y su objeto gobernado es `kcd-001`; el re-mapeo queda registrado con notas de identidad en ADR-0020 y RFC-0003 | El nombre canónico del consumer gobernado en adelante es `data-evolutionary/kcd-001`; el módulo hermano `data-kcd2026` no porta superficie EDAIOS |
