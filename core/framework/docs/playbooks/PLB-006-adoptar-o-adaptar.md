---
id: PLB-006
tipo: Playbook
titulo: Adoptar-o-Adaptar (antes de construir una capacidad)
version: 1.0.0
estado: Ratificado
autoridad: Core
idioma: es
owner: Framework
deriva_de: ADR-0003
---

# PLB-006 — Adoptar-o-Adaptar

## Objetivo
Evitar que EDAIOS reimplemente capacidades de *delivery* SDD que el ecosistema externo ya cubre con calidad, concentrando el esfuerzo en su diferencial semántico. Materializa la regla del punto 4 de ADR-0003 (ratifica RFC).

## Cuándo se aplica
Antes de **construir cualquier capacidad nueva** en EDAIOS. No aplica a operar o ampliar lo ya construido y ratificado.

## External Reference Set
Spec Kit, BMAD-METHOD, OpenSpec (MIT/agent-agnostic) y Kiro (AWS/comercial, referencia de patrones). Vigencia y caracterización registradas en ADR-0003.

## Decisión (en orden)
1. **¿Toca el núcleo semántico?** Ontología/Ontología de Dominio, KOM, `edaios_ekg`, *blast-radius*, AIContext, publicación gobernada o validadores de verdad. **Si sí → construir en EDAIOS.**
2. **Si no toca el núcleo: ¿lo cubre algún externo del set con calidad aceptable?**
   - **No lo cubre ninguno → construir en EDAIOS** (documentando el hueco).
   - **Lo cubre → Adoptar** (usar vía adapter en `extensions/`) **o Adaptar** (envolver/configurar). Nunca vendorizar en el core.
3. **Registrar la decisión como ADR**, con la **justificación del contraste** contra el set y, si adopta/adapta, la **versión pineada** de la herramienta. Sin ADR, "adoptar antes de construir" es aspiracional.

## Reglas de frontera (invariantes)
- El núcleo de conocimiento permanece **autocontenido y derivable de Git sin red**; la interoperabilidad SDD vive solo en el **borde de delivery** (`extensions/`), con herramientas pineadas (invariante "no dependencias externas" **matizado por ADR-0003/PAT-003**, no derogado).
- Los artefactos externos entran como **borradores** trazables (`.edaios/drafts/`), con procedencia; promoción humana + ADR. Ningún externo es fuente de verdad.

## Verificación
La decisión queda en un ADR con el contraste explícito; si adopta/adapta, el adapter está en `extensions/` y la herramienta pineada; `validate.sh` en verde (incluido el gate de coherencia de invariantes, ADR-0003).

## Trazabilidad
Implementa el punto 4 de ADR-0003 (ratifica RFC); se apoya en PAT-003 (supersesión) y en el patrón de borradores del Compiler.

## Historial
- 2026-06-27 — Ratificación (ADR-0003). Materializa la regla Adoptar-o-Adaptar de ADR-0003.
