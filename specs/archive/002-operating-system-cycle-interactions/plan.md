# Plan técnico · Interacciones del ciclo del Operating System

## Contexto y decisión

El modelo vigente conserva etapas, escenas, evidencia y el mapa entre ambas,
pero el renderer actual materializa escenas estáticas y mantiene estados
independientes. Se restaurará una sola máquina de estado cuyo dato primario es
la escena seleccionada; la etapa se deriva de la relación validada en el config.

Decisión:

1. validar fail-closed órdenes, cobertura y coherencia del mapa etapa-escena;
2. renderizar controles nativos, relaciones ARIA, paneles ricos y estados
   iniciales desde el config vigente;
3. hacer que una única función de selección actualice etapa, paneles, escena,
   contador, foco y límites de navegación;
4. restaurar estilos de selección, foco visible, banner, toolbar, responsive e
   impresión sin introducir assets ni dependencias;
5. ampliar `CORE-BASE-DEMO` para verificar estáticamente el contrato generado y
   completar una revisión conductual en navegador local.

Alternativas descartadas:

- CSS sin estado JavaScript: no puede resolver de forma consistente la relación
  de varias escenas con una etapa ni los controles secuenciales.
- dos estados independientes para etapa y escena: permite combinaciones
  contradictorias y fue la causa funcional de la pérdida observada.
- copiar el HTML histórico: viola source-first y reintroduciría narrativa que ya
  no pertenece al Core Base.
- incorporar una librería web o un runner nuevo: aumenta superficie y no es
  necesario para esta interacción offline.

## Materialización

### Config y validación

- `docs/demos/edaios-operating-system.config.json` permanece como fuente
  semántica sin cambiar sus claims.
- `generate_day_zero_demos.py` exige órdenes consecutivos, ocho relaciones
  válidas, cobertura de las siete etapas y equivalencia entre el mapa y
  `scene.stage`.

### Render y estado

- Las etapas se renderizan como tabs nativos enlazados a sus paneles.
- Las escenas se renderizan como botones enlazados a paneles narrativos.
- `selectScene` deriva la etapa y actualiza todos los estados observables.
- Elegir una etapa conserva la escena actual si pertenece a ella; en otro caso
  elige su primera escena.
- Iniciar y reiniciar seleccionan la escena inicial; anterior y siguiente se
  deshabilitan en los extremos.
- La navegación por teclado usa flechas, Inicio y Fin; Enter y Espacio son
  provistos por los botones nativos.

### Estilos y fallback

- La selección combina color, borde y estado ARIA; el foco usa un aro ámbar
  visible.
- En anchos estrechos los grids se apilan y los controles envuelven.
- Con movimiento reducido se eliminan transiciones no esenciales.
- Sin JavaScript y en impresión el contenido permanece legible.

## Estructura de archivos

```text
docs/demos/edaios-operating-system.config.json    fuente semántica existente
tools/publishing/generate_day_zero_demos.py       validación, HTML, CSS y JS
docs/demos/edaios-operating-system.html           derivado regenerado
tools/validation/day_zero_demo_check.py            contrato estático
specs/archive/002-operating-system-cycle-interactions/     contrato y evidencia
```

## Pruebas

1. Gate específico de la feature antes y después de implementar.
2. Generación y `--check` para determinismo config→HTML.
3. `day_zero_demo_check.py` para cardinalidad, mapa, ARIA, acciones, estado
   inicial, CSS seleccionado y ausencia de assets externos.
4. Navegador local para etapa 3, escenas 6–7, controles, teclado, foco y tamaños
   de escritorio/móvil, sin errores de consola.
5. `scripts/test.sh` y `scripts/validate.sh` como sello del repositorio.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | El config vigente conserva el contenido; el renderer solo lo proyecta. |
| II. Spec antes que artefacto | PASS | Spec, checklist y este plan preceden el cambio de fuente. |
| III. El canon crece por decisión | PASS | Es hardening de una vista bajo ADR-0002/0003, sin frontera estructural nueva. |
| IV. Cero cifras sin fuente | PASS | Etapas, escenas y mapa derivan del config y constan en `evidence/sources.md`. |
| V. Una fuente, muchas vistas | PASS | Se modifica el generador y se regenera el HTML; el derivado no se edita como autoridad. |
| VI. La IA consume; el humano firma | PASS | La solicitud del Principal Architect define aceptación visual; la herramienta no acepta canon. |
| VII. Privacidad por diseño | N/A | T0 local, sin datasets, PII, secretos, red o consumidor instalado. |

Constitucion verificada: 1.0.0 · sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `SDD-CONTRACT`: identidad, fase, trazas, Constitución y cobertura.
- `CORE-BASE-DEMO`: derivación, estructura interactiva y contenido vigente.
- `FND-PROJECTION`, `KOM`, `TRACEABILITY` y `MONOREPO-STRUCTURE`: confirman que
  la restauración no deriva autoridad ni topología.
- `TEST` y `VALIDATE`: ejecutan el cierre integral.

## Impacto y reversa

- Arquitectura, ontología, datos, IA y privacidad: sin cambio material.
- Costo: solo generación y validación local; ninguna dependencia nueva.
- Blast radius: generador de la única guía, su derivado y gate específico.
- Despliegue: regenerar la guía offline; no existe publicación automática.
- Reversa: revertir el renderer, el check y el derivado en un mismo cambio; el
  config y Foundation permanecen intactos.
