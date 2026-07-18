---
id: EDAIOS-OPERATING-SYSTEM-CYCLE-INTERACTIONS
estado: Cerrado
fase: implemented
dominio: core
tramo_sensibilidad: T0
owner: Principal Architect
tipo_cambio: hardening
trazas:
  - ADR-0002
  - ADR-0003
spec_tipada: specs/archive/002-operating-system-cycle-interactions/feature.spec.yaml
fuentes:
  - docs/demos/edaios-operating-system.config.json
  - tools/publishing/generate_day_zero_demos.py
  - tools/validation/day_zero_demo_check.py
  - specs/archive/002-operating-system-cycle-interactions/evidence/sources.md
value_ledger: "N/A: hardening visual de una vista derivada sin outcome institucional"
hipotesis_valor: Una ruta guiada sincronizada permite explicar el gobierno de Core sin perder la relación entre etapa, escena y evidencia
---

# Interacciones del ciclo del Operating System

## Alcance

Restaurar en la guía offline la experiencia visual e interactiva del recorrido
EDAIOS usando únicamente el contenido vigente de Core Base. La configuración
canónica declara siete etapas, ocho escenas y su relación; la vista debe hacer
visible esa relación sin introducir una fuente de verdad paralela.

## Requisitos

- **FR-001:** toda selección de etapa debe mostrar su detalle y resaltar la
  escena correspondiente; toda selección de escena debe mostrar su detalle y
  resaltar la etapa que la gobierna.
- **FR-002:** la ruta guiada debe permitir iniciar, retroceder, avanzar y
  reiniciar el recorrido, manteniendo un contador visible y un único estado
  seleccionado.
- **FR-003:** cada etapa y escena debe exponer el contenido de gobierno ya
  disponible en la configuración: pregunta, entrada, control, salida, evidencia
  y límite de claim según corresponda.
- **FR-004:** las selecciones y controles deben ser operables con teclado,
  comunicar su estado a tecnologías de asistencia y reacomodarse sin pérdida de
  contenido en pantallas estrechas.
- **FR-005:** el HTML debe continuar siendo un derivado determinista y offline;
  el contrato interactivo debe quedar cubierto por el gate de la demo.

## Criterios de éxito

- **SC-001:** al elegir `3. Decisión`, quedan visibles el panel de decisión y la
  escena `3. Canon + decisión`, con el contador `03 / 08`.
- **SC-002:** al elegir la escena `7. Muchas vistas`, permanece seleccionada la
  etapa `6. Publicación`, queda seleccionada solo esa escena y el contador
  muestra `07 / 08`.
- **SC-003:** iniciar y reiniciar llevan a la primera escena; anterior y
  siguiente recorren las ocho escenas sin salir de sus límites.
- **SC-004:** las etapas admiten flechas izquierda/derecha, Inicio y Fin; las
  escenas admiten flechas en las cuatro direcciones, Inicio y Fin; el foco
  visible identifica el control activo.
- **SC-005:** generación, check de drift, pruebas y validación terminan en verde
  sin assets de red ni cambios a Foundation, ADR o contenido semántico del
  baseline.

## Frontera

Sensibilidad T0. El cambio mejora una proyección local; no acepta decisiones,
no altera el Core Base 1.0.0 y no demuestra runtime, publicación u outcome.

## Aclaraciones resueltas

- La relación etapa-escena proviene de `operating_cycle.stage_scene_map` y de
  `scene.stage`; ambas declaraciones deben coincidir.
- Cuando una etapa gobierna más de una escena, elegir la etapa conserva la
  escena actual si ya pertenece a ella; desde otra etapa selecciona su primera
  escena.
- Los controles de recorrido se limitan a la primera y última escena; no existe
  reproducción automática ni temporizador.
- La restauración reutiliza exclusivamente textos y claims del config vigente;
  una versión histórica sirve como referencia de interacción, no como fuente
  semántica.
