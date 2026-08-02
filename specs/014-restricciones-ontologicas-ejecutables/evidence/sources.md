# Registro de fuentes · Feature 014

Observación local fechada el 2026-08-02 sobre el commit `658934c` (worktree
limpio tras cerrar 013). Reproducciones locales; no assessment de producción.

| Rótulo | Fuente | Fecha | Alcance observado | Límite |
|---|---|---|---|---|
| SRC-001 | Instrucción humana de esta sesión | 2026-08-02 | Owner ordena: "agrega las recomendaciones que mejor consideres de este video a la ontología de EDAIOS. Materialízalos" | La selección de qué recomendaciones aplican queda delegada al criterio técnico, registrada en ADR-0021 |
| SRC-002 | `core/foundation/ontology/EDAIOS_ONTOLOGY.md` (líneas 65-71) | 2026-08-02 | `## Invariantes` es lista de prosa numerada: 5 reglas sin id, sin ámbito, sin enforcement declarado | La verificación de esas reglas existe dispersa en gates; el vínculo regla→verificador no está declarado |
| SRC-003 | `.specify/gates.json` y `tools/validation/kom_gate.py` | 2026-08-02 | 15 ids de gate declarados; reglas KOM-VR-01..11 + DERIVA-PROSA activas en el gate | El dominio de enforcement válido es la unión de ambos conjuntos |
| SRC-004 | Charla "Why Agentic Systems Need Ontologies" (F. Coyle, AI Engineer), youtube.com/watch?v=Sir59K8ZDPU, descripción y marcadores oficiales | 2026-08-02 | Recomendaciones: ontología = entidades + relaciones + restricciones tipificadas (dominios de estado, cardinalidad, disyunción); validador externo al modelo ("Pydantic en la puerta, la ontología en el libro mayor"); excepciones difíciles en prosa → pocas líneas de lógica | Referencia externa verificada, no promesa; EDAIOS ya cubre el validador externo (gates + firma humana); lo faltante es la tipificación de restricciones |
| SRC-005 | `governance/ADR-0018-entidades-como-contrato-ejecutable.md` y `specs/012-cierre-de-contratos-resolubles/` | 2026-08-02 | Mecanismo bidireccional MD↔JSON operativo para entidades y relaciones; patrón extensible por sección | La extensión a Invariantes requiere ADR propio (ADR-0021, Aceptado) |
