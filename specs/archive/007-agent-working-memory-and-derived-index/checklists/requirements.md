# Checklist de calidad de requisitos

Evaluado el 2026-07-16 contra `spec.md`, `feature.spec.yaml`, ADR-0011 y la
Constitución operativa.

- [x] Alcance acotado: working memory, índice, conflictos, sesiones, setup y un
  adapter opcional; excluye cloud, TUI, juez, sync y promoción.
- [x] Los diez FR poseen criterios SC observables y no dependen de outcomes no
  disponibles.
- [x] Owner, autoridad, valor habilitante y frontera T0 están declarados.
- [x] La jerarquía Foundation → Core → Consumer y la autoridad Git-first no se
  invierten.
- [x] Toda cifra o versión externa citada tiene fuente, fecha, alcance y límite
  en `evidence/sources.md`.
- [x] Engram está tratado como referencia/provider opcional, no como dependencia
  o fuente de verdad.
- [x] Conflictos, timelines y summaries no aceptan decisiones ni fabrican
  evidencia.
- [x] Privacidad: T2/T3 y hosts remotos quedan fail-closed y fuera del alcance T0.
- [x] Compatibilidad: la búsqueda canónica conserva su default y el índice es
  una superficie aditiva.
- [x] El estado de release está separado del trabajo local y de la instalación
  de la capacidad.
- [x] Se declaran errores y casos adversariales de root, encoding, concurrencia,
  staleness, provider, setup y no auto-promoción.
- [x] No quedan `TBD` ni ambigüedades críticas que impidan planificar.

**Resultado:** checklist en verde; habilita plan técnico.
