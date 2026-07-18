# Plan técnico · Glosario del EDAIOS Operating System

## Contexto y decisión

La guía usa vocabulario de Foundation, gobierno, KOM y Spec Kit sin una ruta de
consulta contextual. Existe un glosario constitucional, pero es deliberadamente
resumido y no explica los identificadores operativos de una feature ni las
ambigüedades visibles de `ART` y `VAL`.

Decisión:

1. añadir al config una colección tipada de términos derivados y una guía para
   leer identificadores;
2. validar fail-closed unicidad, categorías, campos, términos mínimos y rutas
   fuente antes de renderizar;
3. proyectar una séptima vista con buscador, filtro de categoría, contador vivo,
   estado vacío y entradas expandibles nativas;
4. normalizar búsqueda en cliente sin mayúsculas ni diacríticos, dejando todo el
   contenido disponible cuando JavaScript no existe;
5. reemplazar la etiqueta confusa `KOM + gates VAL` por `KOM + gates de
   validación`, conservando en el glosario la explicación histórica y su límite;
6. ampliar el gate estático y completar una revisión conductual local sin tocar
   Foundation ni crear una segunda fuente de verdad.

Alternativas descartadas:

- editar `ART-008-GLOSARIO.md`: el usuario necesita onboarding operativo y el
  cambio a Foundation requeriría otra decisión; la demo debe derivar y explicar.
- glosario solo como tabla: dificulta explorar más de veinte conceptos y no
  permite mostrar límites/contexto sin perder legibilidad.
- copiar definiciones históricas de T1–T3 o VAL: elevaría referencias retiradas
  a verdad vigente.
- librería de búsqueda o assets externos: innecesarios para una vista offline.
- editar el HTML: rompe la derivación config → generador → vista.

## Modelo de contenido

`glossary` declara título, introducción, categorías, una cadena didáctica de
identificadores y entradas. Cada entrada conserva:

- `id` estable para render y pruebas;
- término y expansión opcional;
- categoría cerrada;
- explicación simple;
- uso dentro del repositorio;
- ejemplo o límite de interpretación;
- una o más rutas fuente resolubles;
- estado `vigente`, `parcial`, `referencial` o `convencion` para acotar el
  claim.

Los textos son explicaciones en español, no duplicados normativos. `source`
permite volver desde la vista a la autoridad observada.

## Interacción y accesibilidad

- El tab superior usa el patrón existente y participa en flechas, Inicio y Fin.
- `input type=search` y `select` tienen labels visibles.
- Cada término usa `details/summary`, operable por teclado sin JavaScript.
- El contador `aria-live=polite` informa resultados; el estado vacío se muestra
  solo cuando el filtro no encuentra entradas.
- El índice de búsqueda se genera como atributos escapados y se normaliza en el
  navegador con Unicode NFD y eliminación de diacríticos.
- Sin JavaScript y en impresión se muestran controles no operativos ocultos y
  todas las definiciones abiertas o legibles.
- Responsive: guía de códigos, controles y cards pasan a una columna en anchos
  estrechos; no hay scroll horizontal requerido para leer una entrada.

## Estructura de archivos

```text
docs/demos/edaios-operating-system.config.json    vocabulario y fuentes derivadas
tools/publishing/generate_day_zero_demos.py       contrato, HTML, CSS y JS
docs/demos/edaios-operating-system.html           derivado regenerado
tools/validation/day_zero_demo_check.py            gate estático y de fuentes
docs/demos/README.md                               índice actualizado
specs/archive/003-operating-system-glossary/               contrato y evidencia
```

## Pruebas

1. Gate Spec Kit en cada fase y analyze sin hallazgos HIGH/CRITICAL.
2. Generación y `--check` para determinismo.
3. `day_zero_demo_check.py` para séptimo tab, vocabulario mínimo, fuentes,
   semántica accesible, límites VAL/ART/T0 y marcadores de filtro.
4. Navegador local: abrir `#glossary`, buscar ADR y conocimiento, filtrar
   sensibilidad, provocar cero resultados, limpiar, abrir VAL/ART y recorrer el
   tab por teclado; después repetir una interacción del ciclo como regresión.
5. `scripts/test.sh`, `scripts/validate.sh` y `git diff --check` como sello.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. El conocimiento manda | PASS | Cada entrada enlaza fuentes gobernadas; el glosario declara su carácter derivado. |
| II. Spec antes que artefacto | PASS | Spec, aclaraciones, checklist y este plan preceden el cambio del config y renderer. |
| III. El canon crece por decisión | PASS | Es hardening bajo ADR-0002/0003, sin modificar Foundation ni contratos públicos. |
| IV. Cero cifras sin fuente | PASS | Cardinalidades y ejemplos se registran en `evidence/sources.md`; no se importan métricas externas. |
| V. Una fuente, muchas vistas | PASS | El config y las fuentes gobiernan; el HTML se regenera determinísticamente. |
| VI. La IA consume; el humano firma | PASS | La solicitud humana fija la necesidad; la vista no ratifica ADR, KO ni outcome. |
| VII. Privacidad por diseño | N/A | T0 local, sin datasets, PII, secretos, red, LLM o consumer instalado. |

Constitucion verificada: 1.0.0 · sha256:d57078593e5a78bb302e45cea9f5cc5d581be0c6ab8cbb8c751435febd5fb327

## Gate Impact

- `SDD-CONTRACT`: fases, fuentes, trazas, Constitución y cobertura.
- `CORE-BASE-DEMO`: navegación, derivación, vocabulario y contrato interactivo.
- `FND-PROJECTION`: confirma que Foundation no cambió.
- `KOM` y `TRACEABILITY`: conservan identidades y referencias resolubles.
- `MONOREPO-STRUCTURE`: confirma topología Core Base sin extensiones nuevas.
- `TEST` y `VALIDATE`: cierre integral del repositorio.

## Impacto y reversa

- Arquitectura: nueva vista derivada; sin cambio de dependencias o autoridad.
- Ontología: sin cambio; la vista resume entidades ya existentes.
- Datos, IA y privacidad: T0, sin datos ni ejecución de modelos.
- Costo: generación y filtrado local; ninguna dependencia o servicio.
- Blast radius: config, renderer, HTML, gate específico e índice de demos.
- Despliegue: regeneración offline; commit, push y publicación siguen separados.
- Reversa: retirar la colección, tab, renderer y checks en un mismo cambio; las
  fuentes Foundation permanecen intactas.
