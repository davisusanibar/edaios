---
id: PLB-005
tipo: Playbook
titulo: Onboarding de consumer real
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Core Maintainers
deriva_de: ADR-0020
---

# PLB-005 — Onboarding de consumer real

Entrega gobernada del gate SDD a un consumer (ADR-0020, resuelve RFC-0002).
Cada paso está respaldado por código existente; nada aspiracional.

1. Verifica la deriva: compara el sha256 del gate del consumer contra el del
   Core vigente; el sidecar `spec_kit_gate.SOURCE.md` declara la procedencia
   anterior.
2. Siembra con `edaios_sdd_adapter.spec_kit.seed_gate(core_root, consumer)`:
   ante copia divergente la función se niega y reporta ambos digests — esa
   negativa es evidencia, archívala.
3. Re-siembra solo con confirmación explícita del owner del consumer
   (`force=True`); el sidecar queda actualizado con versión, digest, fecha y
   vía.
4. Valida el módulo del consumer con su gate sembrado:
   `python3 tools/validation/spec_kit_gate.py <módulo> --feature <feature> --profile consumer-release`.
5. Archiva las salidas (negativa, re-siembra, corrida verde) como evidencia
   de la feature de Core que gobierna el onboarding.
6. Registra el outcome en `governance/VALUE_LEDGER.md` con baseline, fuente y
   fecha; el estado queda en observación — un gate técnico no cierra un
   outcome.
7. El commit en el repositorio del consumer pertenece a su owner; el Core
   nunca commitea árboles ajenos.
