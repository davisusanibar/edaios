---
id: PLB-004
tipo: Playbook
titulo: Ejecutar un cambio gobernado
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Core Maintainers
deriva_de: ADR-0002
---

# PLB-004 — Cambio gobernado

1. Captura intención, owner, fuentes, sensibilidad y valor.
2. Aísla branch + worktree y selecciona la feature.
3. Ejecuta Spec Kit hasta analyze.
4. Obtén aceptación cuando la decisión lo requiera.
5. Implementa tareas aprobadas y regenera derivados.
6. Ejecuta tests/gates y registra límites.
7. Revisa diff, rollback y evidencia antes de promoción.
