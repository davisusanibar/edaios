# Ways of working

- El baseline instalado es Foundation → Core; no hay consumers instalados.
- Un writer por branch + worktree/clone.
- Spec, checklist, plan y tareas preceden implementación gobernada.
- Cambios compartidos usan escritura atómica, lock o comparación de baseline.
- RAM y caches son efímeros; receipts y digests son reproducibles.
- Los gates de superficie juzgan lo versionado; el estado local `.edaios/` es
  reconstruible y no constituye una instalación.
- Conflictos, warnings y referencias rotas fallan cerrado.
- El reviewer evalúa diff, evidencia y límites de claim.
- La persona autorizada conserva aceptación, promoción y publicación.
- Una extensión futura nace por necesidad, spec y decisión; una plantilla no la
  convierte en módulo instalado.
