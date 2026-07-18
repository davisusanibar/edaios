---
id: KO-GOVERNANCE
tipo: Governance
titulo: Modelo de gobierno EDAIOS
version: 1.0.0
estado: Ratificado
autoridad: Foundation
idioma: es
owner: Foundation
deriva_de: Foundation
---

# Modelo de gobierno

## Autoridad

Foundation → Core → Consumer. La autoridad nunca fluye hacia arriba. Git
conserva el conocimiento; las vistas derivan. La IA prepara y verifica; una
persona autorizada acepta.

## Triage

```text
intención
  ├─ cambio constitucional → ADR + owner de Foundation
  ├─ opciones abiertas      → RFC → ADR
  ├─ decisión estructural   → ADR
  └─ contrato claro         → feature Spec Kit
```

El ADR estructural debe estar Aceptado antes de implementar. El RFC Ratificado
apunta a la decisión que lo resuelve.

Los estados especializados se comparan mediante el lifecycle del KOM: un ADR
`Aceptado` equivale a un KO `Ratificado`; una feature `Cerrado` equivale a
`Ratificado`. El resource ejecutable
`core/framework/core/profiles/governance-grammar.json` materializa esta
gramática sin redefinir Foundation.

## Cadena de entrega

intención → spec → checklist → plan → tareas → analyze → implementación → gates
→ evidencia → revisión humana → promoción.

Warnings, referencias rotas, tareas huérfanas o claims superiores a su evidencia
fallan cerrado. Commit, push, release y publicación son permisos separados.

## Memoria y concurrencia

Git es durable; estado local es reconstruible y RAM efímera. Cada writer usa un
worktree/clone. Escrituras compartidas usan atomic write, lock o CAS.
