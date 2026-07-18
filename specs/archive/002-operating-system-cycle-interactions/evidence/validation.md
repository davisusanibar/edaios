# Evidencia de restauración del ciclo

Fecha: **2026-07-15**
Alcance: guía offline `edaios-operating-system.html`, renderer y gate específico.

## Evidencia automática

| Control | Resultado | Observación |
|---|---|---|
| Compilación Python | PASS | Generator y validator compilan sin error. |
| Generación | PASS | HTML regenerado desde config y fuentes canónicas. |
| Drift | PASS | `generate_day_zero_demos.py --check`. |
| Demo gate | PASS | Estructura de siete etapas, ocho escenas, mapa, ARIA, acciones y estado inicial. |
| Tests | PASS | Tres pruebas Core y gate de demo en verde. |
| Validate | PASS | Nueve gates pre-push en verde. |
| Revisión independiente | PASS | Sin hallazgos funcionales bloqueantes; se corrigieron foco de inicio y tipos booleanos. |

## Evidencia conductual en navegador local

Viewport observado: **1280 × 720**. La adaptación estrecha queda además cubierta
por reglas source-first verificadas en el HTML (`1100 px`, `980 px`, `700 px` y
preferencia de movimiento reducido); el browser local disponible no expuso
emulación de viewport.

| Escenario | Resultado observado |
|---|---|
| Seleccionar `3. Decisión` | Etapa y panel 3 activos, escena `Canon + decisión` sombreada, panel narrativo visible y contador `03 / 08`. |
| Seleccionar escena 7 | Etapa `6. Publicación`, escena `Muchas vistas`, contador `07 / 08`. |
| Volver a elegir etapa 6 | Conserva escena 7 si ya pertenece a Publicación. |
| Entrar a etapa 6 desde etapa 5 | Selecciona escena 6; Siguiente pasa a escena 7 y conserva etapa 6. |
| Límites | En escena 1, Anterior está deshabilitado; en escena 8, Siguiente está deshabilitado. |
| Iniciar y Reiniciar | Regresan a etapa 1, escena 1 y `01 / 08`. |
| Teclado | Fin/Inicio recorren etapas; flecha derecha y Fin recorren escenas; Escape reinicia. |
| Accesibilidad visible | Tabs y botones comunican estado; el foco muestra aro ámbar y la selección conserva borde además del color. |
| Consola | `demoTab.dev.logs()` devolvió una lista vacía tras el recorrido. |

## Frontera

La evidencia prueba la proyección local y su interacción. No prueba publicación,
compatibilidad exhaustiva entre navegadores, runtime consumidor u outcome.
