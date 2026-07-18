# Checklist de calidad de requisitos

Evaluación de `spec.md`, `feature.spec.yaml`, ADR-0014 propuesto, Constitución
operativa y registro de fuentes antes de planificar.

- [x] El alcance se limita a hardening de Core y excluye iniciativa, producto, proveedor, runtime, remoto y release.
- [x] `Principal Architect` está declarado y fue confirmado como owner humano; la aprobación futura no se infiere.
- [x] Cada FR describe una obligación observable sin prescribir una librería, servicio o proveedor.
- [x] Cada FR posee al menos un SC adversarial y medible con resultado fail-closed.
- [x] Autoridad, delegación, evidencia y aprobación distinguen identidad, rol, capacidad, iniciativa y receipt.
- [x] La monotonía cubre todas las dimensiones que pueden debilitar una política, no solo la lista de controles.
- [x] Gates, objetos Git y comparación base/head tienen criterios verificables independientes del worktree.
- [x] El ciclo SDD conserva conocimiento retirado y exige cadena SC → tarea → verificación → evidencia.
- [x] La sensibilidad de la feature es T0 y cualquier dato T2/T3 queda bloqueado antes de persistir o mostrarse.
- [x] Las expectativas de permisos, contención, atomicidad y rollback incluyen casos negativos reproducibles.
- [x] El rango Python observado y el rango acotado propuesto están registrados; CI 3.11/3.12/3.13 es finito y verificable.
- [x] No se citan benchmarks, outcomes, madurez, adopción, disponibilidad o cifras de producción.
- [x] Las trazas ADR existen; ADR-0014 permanece Propuesto y bloquea cambios estructurales hasta aceptación humana.
- [x] La hipótesis de valor no sustituye un Value Ledger ni atribuye valor a una iniciativa inexistente.
- [x] Las fronteras de claim separan ejecución local, seguridad del host, identidad externa y producción.
- [x] No quedan `TBD`, preguntas abiertas ni ambigüedades críticas para preparar un plan condicionado.

**Resultado:** checklist en verde. Habilita plan técnico, pero no implementación;
ADR-0014, el plan y las tareas todavía requieren aprobación del owner.
