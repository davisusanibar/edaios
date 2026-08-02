# Revisión adversarial · Feature 018

Ejecutada el 2026-08-02 por los subagentes reales en paralelo (una pasada
cada uno). Tres hallazgos duplicados entre lentes consolidados con la
severidad máxima reportada; seis únicos, todos corregidos antes del cierre —
incluido un fail-open vivo en el borde de inyección demostrado con el CLI
real del owner.

| Id | Lente | Severidad | Estado | Hallazgo | Refs |
|---|---|---|---|---|---|
| RA-001 | lente-riesgo | HIGH | corregido | El precheck de inyección era fail-open: solo verificaba presencia del CLI y el ">=0.15.1" vivía únicamente en el mensaje de error, mientras ADR-0022 afirmaba en canon que "la inyección verifica el mínimo" — control declarado sin implementar, con el CLI global del owner (0.12.11) recorriendo esa ruta. Fix: comparación real contra `specify --version` (sort -V), demostrada fail-closed con el CLI real: `FAIL: specify 0.12.11 < 0.15.1`. | inject-consumer.sh precheck; ADR-0022 Consecuencias |
| RA-002 | lente-riesgo | MEDIUM | corregido | Las estampas de procedencia del consumer (apéndice de constitución, lock, tool_version) derivan de constantes, nunca del CLI usado: con RA-001 abierto, una inyección con 0.12.x habría producido procedencia entera declarando 0.15.1, indetectable por el gate. Fix: el piso real de RA-001 cierra el vector en la ruta gobernada; ADR-0022 declara ahora que las estampas afirman el perfil aceptado garantizado por ese piso, y que sembrar fuera del script queda fuera del claim. | spec_kit.py estampas; ADR-0022 Consecuencias |
| RA-003 | refutador | HIGH | corregido | SC-002 conservaba la letra pre-sandbox "inyección en verde con --events false" — criterio insatisfacible que la propia evidencia de la feature refutó, con verified declarado encima. Fix: SC-002 reescrito a la letra empírica (verificación de events sin flag, sin archivos); reportado por ambos lentes. | spec.md SC-002; sc-002-sandbox.json |
| RA-004 | refutador | HIGH | corregido | El barrido global de versiones corrompió la línea de pendientes de CURRENT_STATE ("vendor update 0.15.1→0.15.x"): transición sin sentido, procedencia misquoteada y una decisión ya tomada (ADR-0022) declarada pendiente. Fix: pendientes veraces — receipts in-toto; el vendor update figura decidido y ejecutado. Reportado por ambos lentes. | CURRENT_STATE.md pendientes |
| RA-005 | refutador | MEDIUM | corregido | La cadena de enmienda nacía apuntando al ADR equivocado: "Amends: ADR-0003" y el OVERVIEW citaban un ADR que en el catálogo vigente es Core Base y no gobierna el pin de Spec Kit (colisión de numeración preexistente que el canon nuevo formalizaba). Fix: Amends → ADR-0002 (delivery Spec Kit), contexto citando ADR-0002/ADR-0016/PLB-006, y OVERVIEW acreditando el perfil a ADR-0022. Reportado por ambos lentes. | ADR-0022 Amends/Contexto; OVERVIEW.md; spec trazas |
| RA-006 | refutador | LOW | corregido | El inventario de supervivientes de 0.12.11 en la evidencia nombraba "archivo" (cero ocurrencias reales) y omitía spec/plan/tasks de la propia 018. Fix: inventario preciso en sc-001. | evidence/sc-001-pin.json |

Lo que se intentó refutar y resistió (ambos lentes): lock correcto en ambas
claves y copia fiel en capa D; 4 manifiestos con piso; 4 fixtures sin
debilitar aserciones; cifras 196 tests y 14 gates exactas; commit de sources
verificado en reflog; sc-002-sandbox honesta sobre la refutación del flag;
ninguna superficie de events en repo ni bundle; ninguna referencia vigente a
0.12.11.

Veredicto humano: aceptado por el owner en el cierre (orden expresa "Procede
con el vendor update" y "Continúa con el cierre de la 018", sesión
2026-08-02); los agentes prepararon y bloquearon, no aprobaron.
