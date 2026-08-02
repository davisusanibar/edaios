# Revisión adversarial · Feature 016

Ejecutada el 2026-08-02 por los subagentes reales `edaios-refutador` y
`edaios-lente-riesgo` (proyecciones de la feature 015), una pasada exhaustiva
cada uno, en paralelo. El ciclo de corrección se aplicó antes del cierre: los
dos HIGH y los tres MEDIUM del lente, y los dos MEDIUM del refutador, quedaron
resueltos con código, tests o registro — ninguno con prosa sola.

| Id | Lente | Severidad | Estado | Hallazgo | Refs |
|---|---|---|---|---|---|
| RA-001 | lente-riesgo | HIGH | corregido | Escritura parcial irreparable: gate y sidecar se escribían sin transacción y el corto-circuito idempotente jamás revisaba el sidecar — un sidecar ausente, viejo o manual con gate idéntico pasaba en silencio. Fix: la procedencia se auto-repara en la rama idempotente (convergencia por reintento) con 2 regresiones nuevas. | spec_kit.py seed_gate, test_seed_gate.py sidecar-ausente/manchado, FR-001 |
| RA-002 | lente-riesgo | HIGH | corregido | Canal paralelo no gobernado: `inject-consumer.sh` capa C hacía `cp` incondicional + sidecar manual, pisando deriva en silencio — la conducta que ADR-0020 prohíbe. Fix: capa C recableada a `seed_gate` sin force (una divergencia detiene la inyección); formato manual retirado. | inject-consumer.sh capa C, ADR-0020 |
| RA-003 | lente-riesgo | MEDIUM | corregido | Sin contención física en árbol ajeno: un symlink en `tools/validation` redirigía la siembra fuera de la superficie declarada. Fix: resolución física de destino y sidecar bajo la raíz del consumer, fail-closed, con regresión de symlink que verifica que nada se escribe fuera. | spec_kit.py contención, test_symlink_en_tools_validation |
| RA-004 | lente-riesgo | MEDIUM | corregido | La rama fresca pisaba un sidecar previo sin gate acompañante (el registro de procedencia anterior es evidencia del paso 1 de PLB-005). Fix: sin `force`, un sidecar huérfano detiene la siembra; regresión incluida. | spec_kit.py, test_sidecar_previo_sin_gate |
| RA-005 | lente-riesgo | MEDIUM | corregido | Conflación de autoridades: la confirmación de `force` se archivó como orden del owner de Core, no del owner del consumer. Fix: SRC-007 registra la identidad verificada de ambos owners (mismo usuario git en ambos remotos) y la evidencia re-declara que, con owners distintos, `force` pertenece solo al owner del consumer (PLB-005 paso 3). | evidence/sc-002 confirmacion, sources.md SRC-007 |
| RA-006 | lente-riesgo | LOW | corregido | Puntero sin resolución: la gobernanza nombra `data-kcd2026` y la feature ejecuta sobre `kcd-001` sin declarar equivalencia. Fix consolidado con RA-008. | sources.md SRC-008, ADR-0020, RFC-0003 |
| RA-007 | refutador | MEDIUM | corregido | Dos estados con procedencia ausente o falsa e irreparables por la API: gate copiado a mano sin sidecar reportaba éxito sin dejar procedencia, y una interrupción del camino force dejaba sidecar con digest falso a perpetuidad. Mismo origen que RA-001; el fix convergente cubre ambos casos con regresiones exactas (sidecar ausente se escribe; sidecar con digest viejo se repara en el siguiente run). | spec_kit.py rama idempotente, test_seed_gate.py, VL-001 |
| RA-008 | refutador | MEDIUM | corregido | Verificado en el árbol real: `data-kcd2026` existe como módulo hermano de `kcd-001` sin `tools/validation/` propio — la reconciliación de identidad no podía quedar implícita. Fix: SRC-008 reescrito con el hecho verificado y notas de identidad registradas en ADR-0020 (Consecuencias) y RFC-0003 (plan de evidencia) antes de ratificar. | sources.md SRC-008, ADR-0020 Consecuencias, RFC-0003 ítem 5 |

Veredicto humano: aceptado por el owner en el cierre (autorización expresa de
la sesión del 2026-08-02, owner de Core y del consumer — SRC-007); los agentes
prepararon y bloquearon hasta la corrección, no aprobaron.
