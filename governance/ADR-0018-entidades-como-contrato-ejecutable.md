# ADR-0018 — Dominio de entidades como contrato ejecutable de la gramática de gobierno

**Estado:** Aceptado
**Fecha:** 2026-08-01
**Owner:** Principal Architect

## Contexto

La ontología (`core/foundation/ontology/EDAIOS_ONTOLOGY.md`) declara 28 entidades y
12 relaciones tipadas. Su operacionalización ejecutable vive en
`core/framework/core/profiles/governance-grammar.json`, que hoy solo lleva las
relaciones: el dominio de entidades que KOM-VR-02 valida se extrae raspando la tabla
Markdown con la regex de `tools/validation/kom_gate.py:49`. RFC-0003 (hallazgo D1)
verificó que ese raspado es fail-open: devuelve 38 tokens, no 28, y acepta 10
nombres de relaciones como tipos de entidad válidos — un KO con `tipo: governs`
pasa el gate. Además, nada verifica que la tabla de relaciones del Markdown y las
`relations` del JSON sigan sincronizadas; hoy coinciden por disciplina, no por
contrato.

## Decisión

`governance-grammar.json` incorpora el dominio de entidades como dato explícito:
`"entities": [...]` con los 28 identificadores exactos de la tabla de entidades de
la ontología. La autoridad no cambia: el Knowledge Object de ontología en Foundation
sigue siendo la fuente normativa; la gramática es su proyección ejecutable, igual
que `constitution.md` respecto de `constitution.src.json`.

`kom_gate.py` deja de derivar el dominio del raspado crudo:

- KOM-VR-02 valida `tipo` contra `grammar["entities"]`, nunca contra la regex;
- el gate verifica correspondencia bidireccional y por sección: los ids de
  `grammar["entities"]` deben coincidir exactamente con las filas de la tabla de
  entidades del Markdown, y las claves de `grammar["relations"]` con las filas de
  la tabla de relaciones; cualquier diferencia en cualquier dirección falla cerrado;
- el parseo del Markdown queda acotado a la sección correspondiente de cada tabla,
  de modo que una tabla futura en otra sección no pueda ensanchar el dominio en
  silencio.

## Alternativas

- compilar la gramática completa desde el Markdown: rechazada; reubica la misma
  fragilidad regex dentro de un compilador y convierte prosa en fuente ejecutable
  sin contrato inverso;
- corregir solo la regex para excluir la tabla de relaciones: rechazada; repara el
  síntoma, deja el dominio sin declaración explícita y sin verificación
  bidireccional;
- mover las entidades a un archivo fuente nuevo: rechazada; ya existe un contrato
  ejecutable canónico para la gramática de gobierno y fragmentarlo crearía una
  tercera fuente.

## Consecuencias

Un KO con tipo fuera del dominio ontológico falla KOM de forma determinista. La
deriva entre ontología y gramática se detecta en gate, no en revisión humana. La
edición de la ontología exige tocar la gramática en el mismo cambio (y viceversa),
que es exactamente el acoplamiento que un contrato bidireccional debe imponer.

## Evidencia y frontera del claim

Evidencia: ejecución de la regex actual sobre la ontología (38 tokens, 10
relaciones aceptadas como entidades), registrada en RFC-0003. Frontera: este ADR no
amplía la ontología ni añade entidades nuevas; no modela dominio de ingeniería de
datos; solo cierra el contrato de las 28 entidades y 12 relaciones ya ratificadas.

## Aprobación

Principal Architect · 2026-08-01 · aprobación humana expresa del Owner en sesión
de trabajo: plan de evolución aprobado y orden explícita de continuar tras
revisión del resumen de decisiones. Borrador preparado por IA en la misma sesión.
