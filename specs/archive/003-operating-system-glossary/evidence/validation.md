# Evidencia del glosario del Operating System

Fecha: **2026-07-15**
Alcance: séptimo tab, contenido source-first, renderer, interacción y gate de la
guía offline `edaios-operating-system.html`.

## Evidencia automática

| Control | Resultado | Observación |
|---|---|---|
| Compilación Python | PASS | Generator y validator compilan sin error. |
| Generación | PASS | HTML regenerado desde config y fuentes gobernadas. |
| Drift | PASS | `generate_day_zero_demos.py --check`. |
| Demo gate | PASS | Siete vistas, términos mínimos, fuentes, semántica accesible, filtro y regresión del ciclo. |
| Tests | PASS | Tres pruebas Core y gate de demo en verde. |
| Validate | PASS | Nueve gates pre-push; Spec Kit 118/118 con estado `Cerrado`, fase `implemented` y 7/7 tareas. |
| Revisión independiente | PASS con ajustes | Sin bloqueantes; se precisó VAL no materializado, convenciones externas RACI/PII y print sin filtros. |

## Evidencia conductual en navegador local

Viewport observado: **1280 × 720**. La adaptación estrecha y la impresión
quedan además cubiertas por contratos CSS verificados en el HTML; el browser
local disponible no expuso emulación de viewport o print.

| Escenario | Resultado observado |
|---|---|
| Abrir `#glossary` | El séptimo tab `Glosario` queda seleccionado y muestra guía de códigos, controles y 38 términos. |
| Buscar `ADR` | Se muestran 6 términos relacionados, incluido ADR. |
| Buscar `constitucion` | Encuentra `Constitución` y relacionados sin exigir tilde. |
| Buscar `conocimiento` | Muestra 10 términos e incluye KO y KOM. |
| Filtrar sensibilidad | Muestra exactamente T0, T1/T2/T3 y PII. |
| Cero resultados | Contador `0 términos` y estado vacío visible. |
| Limpiar | Restablece búsqueda, categoría y 38 términos; devuelve foco al buscador. |
| Abrir VAL | Declara que no existe catálogo ni gate activo `VAL-*`; enlaza KOM y gates vigentes. |
| Abrir ART | Distingue artículo constitucional de ArtifactRecord por contexto. |
| Teclado de vistas | Flecha izquierda lleva de Glosario a Evidencia; Fin vuelve a Glosario. |
| Regresión Ciclo 1–7 | `3. Decisión` conserva `Canon + decisión` y contador `03 / 08`. |
| Consola | Sin errores ni warnings después del recorrido. |

## Frontera

La evidencia demuestra la proyección local, búsqueda, filtros y regresión
observada. No convierte el glosario en fuente normativa, no define T1–T3, no
materializa VAL-004 y no prueba compatibilidad exhaustiva entre navegadores,
publicación, adopción u outcome.
