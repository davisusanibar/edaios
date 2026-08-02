# Value Ledger

Cada entrada declara: apuesta, outcome, owner de beneficio, baseline con
fuente y fecha, target, acción, evidencia, atribución, limitaciones, fecha de
review y estado. Un gate técnico no cierra un outcome.

## VL-001 — Entrega gobernada del gate al primer consumer real

| Campo | Valor |
|---|---|
| Apuesta | La entrega gobernada del gate (`seed_gate`, ADR-0020) elimina la deriva silenciosa de las copias vendorizadas en consumers reales. |
| Outcome esperado | Cero deriva silenciosa del gate en consumers: toda divergencia se reporta con digests y toda re-siembra queda con procedencia verificable. |
| Owner de beneficio | Principal Architect (owner del consumer `kcd-001` y del Core). |
| Baseline | Copia manual vendorizada en `kcd-001/tools/validation/` pineada al commit `0c60544` por `inject-consumer.sh`; divergente del Core vigente (`8ef5f5ec…` vs `60365b02…`) tras cinco features sin ningún aviso. Fuente: sidecar previo y digests, 2026-08-02 (specs/016, SRC-002). |
| Target | Divergencia detectada y reportada en el 100% de las siembras; ninguna sobrescritura sin confirmación explícita. |
| Acción | `seed_gate()` en el adapter SDD + PLB-005; ejecutado sobre el consumer real el 2026-08-02. |
| Evidencia | `specs/archive/016-onboarding-de-consumer-real/evidence/sc-002-consumer-real.json` (negativa con digests, re-siembra con sidecar gobernado, corridas 43/43 y 18/18 con `--profile consumer-release`). |
| Atribución | Directa: la negativa y la re-siembra son salidas de la acción; sin factores externos. |
| Limitaciones | Un solo consumer; la detección ocurre al sembrar, no de forma continua; el outcome no se declara logrado por esta corrida. |
| Review | 2026-11-02 (o al incorporar el segundo consumer, lo que ocurra primero — gatillo de ADR-0020). |
| Estado | En observación. |
