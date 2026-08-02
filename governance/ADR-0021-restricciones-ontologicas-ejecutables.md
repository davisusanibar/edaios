# ADR-0021 — Restricciones ontológicas como contrato ejecutable

**Estado:** Aceptado
**Fecha:** 2026-08-02
**Owner:** Principal Architect

## Contexto

La ontología declara cinco invariantes como lista de prosa numerada, sin tipo,
sin ámbito y sin enforcement declarado. ADR-0018 cerró el contrato ejecutable
de entidades y relaciones; los invariantes quedaron fuera. La charla "Why
Agentic Systems Need Ontologies" (F. Coyle, AI Engineer, youtube.com/watch?v=Sir59K8ZDPU),
ya citada por RFC-0003 como validación externa, precisa la pieza faltante: una
ontología operativa son entidades, relaciones **y restricciones tipificadas**
(dominios de estado, cardinalidad, disyunción), con un validador externo al
modelo — "las excepciones difíciles de escribir en prosa se reducen a unas
pocas líneas de lógica". EDAIOS ya tiene el validador (gates fail-closed y
firma humana: lógica fuera, razonamiento probabilístico dentro); le falta que
sus propias restricciones sean datos verificados y no párrafos.

## Decisión

1. La ontología incorpora la entidad `Constraint` (restricción tipificada
   verificable del dominio). El dominio de entidades pasa de 28 a 29.
2. La sección `## Invariantes` se convierte en tabla tipada: cada restricción
   declara `id` (`INV-NNN`), regla, `aplica_a` (subconjunto del dominio de
   entidades) y `verificado_por` (ids de enforcement resolubles).
3. `governance-grammar.json` incorpora `constraints` como datos ejecutables,
   con el mismo mecanismo de ADR-0018: el Markdown conserva la autoridad, el
   JSON es el contrato, y `kom_gate` verifica correspondencia bidireccional
   por sección — ids, ámbitos y enforcers.
4. El dominio válido de `verificado_por` son los ids de gates declarados en
   `.specify/gates.json`, las reglas `KOM-VR-01..11` y `DERIVA-PROSA`. **Una
   restricción sin enforcement resoluble falla cerrado**: en esta ontología no
   existen invariantes aspiracionales — solo restricciones verificadas o
   ninguna.
5. Solo se materializan restricciones cuyo enforcement ya existe. Los cinco
   invariantes vigentes se tipifican con sus verificadores reales y se añaden
   únicamente restricciones que documentan enforcement ya operativo
   (unicidad de identidad, dominio y transiciones de ciclo de vida, tipo
   único, resolución de RFC, linaje resoluble, cambio estructural con ADR).

## Alternativas

- migrar a RDFS/OWL con razonador: rechazada por ahora; añade runtime y
  dependencias que Core stdlib no admite, y el beneficio (inferencia) no se
  necesita para restricciones enumerables — LinkML/OWL siguen anotados en
  RFC-0003 como camino futuro;
- dejar los invariantes como prosa y validar solo en gates: rechazada; es el
  statu quo que Coyle identifica como capa faltante — la regla viviría lejos
  de su declaración;
- permitir restricciones sin enforcer como "documentación": rechazada; repite
  el patrón decorativo que D1 demostró letal.

## Consecuencias

Los invariantes dejan de ser prosa y pasan a ser filas verificadas: eliminar
un gate que da enforcement a una restricción rompe el gate KOM; declarar una
restricción nueva exige señalar quién la verifica. La edición de la ontología
y de la gramática quedan acopladas también en esta sección (deliberado). La
versión del KO de ontología sube a 1.1.0 (cambio aditivo).

## Evidencia y frontera del claim

Evidencia: sección Invariantes actual (prosa sin enforcement declarado),
mecanismo bidireccional operativo de ADR-0018 (specs/012), recomendaciones de
la charla citada con sus marcadores de tiempo. Frontera: no se afirma
inferencia semántica ni razonamiento OWL; las restricciones cubren el dominio
de gobierno de EDAIOS, no dominios de datos de consumidores; la lista inicial
no pretende completitud — crece por decisión.

## Aprobación

Principal Architect · 2026-08-02 · orden humana expresa del Owner en sesión de
trabajo: incorporar las recomendaciones del video referido a la ontología y
materializarlas. Borrador preparado por IA en la misma sesión.
