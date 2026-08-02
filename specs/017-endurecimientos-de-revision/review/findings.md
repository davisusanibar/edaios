# Revisión adversarial · Feature 017

Ejecutada el 2026-08-02 por los subagentes reales en paralelo, una pasada
exhaustiva cada uno. Once hallazgos únicos (un duplicado entre lentes
consolidado); ciclo de corrección aplicado íntegro antes del cierre — la
feature que endurece la revisión fue la más revisada del programa.

| Id | Lente | Severidad | Estado | Hallazgo | Refs |
|---|---|---|---|---|---|
| RA-001 | refutador | HIGH | corregido | El reclamo de cierre corría sobre texto crudo: un cierre falso envuelto en dos líneas escapaba (asimetría con la regla en-cola, que sí normalizaba). Fix: _surface_file_checks normaliza TODO el texto antes de aplicar cualquier contrato; regresión con prosa envuelta añadida. | traceability_check.py, test_cierre_falso_envuelto |
| RA-002 | lente-riesgo | MEDIUM | corregido | El disparador del pin de spec era un interruptor de formato: la variante en negrita (el estilo de la casa), sangría o NFD lo evadían en silencio. Fix: disparador laxo (negritas/espacios/NFD normalizados) que activa el contrato estricto; regresión con negrita + 62 hex. | spec_kit_gate.py, test_pin_de_spec |
| RA-003 | lente-riesgo | MEDIUM | corregido | El split por puntos rompía la asociación con `.md` y semver, y las listas la cortaban. Fix: límite de oración `. ` (punto+espacio) sobre texto normalizado; regresión con NOTAS.md y 3.1.0 en la oración; limitación de listas numeradas documentada en el check. | traceability_check.py, test_punto_interno |
| RA-004 | refutador | MEDIUM | corregido | Faltaba la regresión "cierre falso en NEXT_ITERATION" que el plan declaraba — precisamente la que habría expuesto RA-001. Añadida con prosa envuelta como el archivo real. | test_program_surface.py |
| RA-005 | refutador | MEDIUM | corregido | El plan afirmaba "mismo patrón de adyacencia del check de cierres" pero la regla en-cola usa ámbito de oración — contrato distinto, con un falso positivo demostrable ante negaciones. Fix: el plan describe el contrato real y documenta la clase de falso positivo como fail-closed aceptado (se resuelve reescribiendo la oración). | plan.md §Decisión 2 |
| RA-006 | refutador | MEDIUM | corregido | Cifra sin fuente: SC-001 decía "16 specs con línea de pin" cuando el corpus real es 8 spec.md (16 es la cuenta de plan.md). Corregido en la spec — Regla IV contra su aplicador, segunda vez en el programa. | spec.md SC-001, sources SRC-002 |
| RA-007 | refutador | MEDIUM | corregido | NEXT_ITERATION corregido decía "quince archivadas" y "dieciséis cerradas" (reales: 14 dirs + tombstone de la 006 retirada; 15 con estado Cerrado). Conteos alineados al estado verificable. | NEXT_ITERATION.md |
| RA-008 | refutador | MEDIUM | corregido | sc-003-cierre.json se autodeclaraba "verified" mientras su detail admitía la revisión pendiente — evidencia falsa al escribirse. Reescrita al cierre con el estado veraz (esta tabla existente y el ciclo completo). Reportado por ambos lentes. | evidence/sc-003-cierre.json |
| RA-009 | lente-riesgo | LOW | corregido | _feature_state colapsaba no-existencia y ambigüedad en None: ante dos directorios con el mismo número, la cerrada escapaba en silencio de la regla en-cola. Fix: (candidatos, estado); ambigüedad falla cerrado; regresión añadida. | traceability_check.py, test_prefijo_ambiguo |
| RA-010 | lente-riesgo | LOW | corregido | sc-001 atribuía la regresión del pin a un archivo que no la contiene. Campo tests corregido a ambos archivos reales. | evidence/sc-001-pin-spec.json |
| RA-011 | refutador | LOW | corregido | El bloque de pin de spec validaba el body crudo sin strip_fences, a diferencia del contrato del plan ("un fence es un ejemplo, no una declaración"). Fix: mismo ámbito que el plan. | spec_kit_gate.py |

Lo que se intentó refutar y resistió (ambos lentes): la regresión del pin
reproduce fielmente el escape histórico; las 8 líneas de spec normalizadas son
conformes; la exclusión de prefijos con guion evita el falso positivo VL-001;
el escape "En cola: 016" queda cubierto; los conteos de gates cuadran; los
PASS de I, III, V, VI y VII resisten con evidencia.

Veredicto humano: aceptado por el owner en el cierre (autorización expresa de
la sesión del 2026-08-02); los agentes prepararon y bloquearon, no aprobaron.
