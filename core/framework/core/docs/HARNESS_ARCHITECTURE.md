# Harness Architecture

Core 3.1.0 publica doce harnesses para orquestación SDD, routing, DAG, TDD,
artefactos, resultados, memoria, permisos, aceptación humana, rollback,
telemetría y comandos.

`enforced` exige operación determinista, prueba positiva y negativa y evidencia
local. `contracted` significa contrato presente con enforcement pendiente y no
puede presentarse como capacidad ejecutada. `integrated` y `operational` se
reservan a adapters/runtimes observados fuera del baseline.

El orquestador devuelve la siguiente fase; no ejecuta tareas ni aprueba. El
permission guard valida una delegación; no concede autoridad. Human acceptance
solo valida un ApprovalReceipt preparado por un actor humano autorizado.
