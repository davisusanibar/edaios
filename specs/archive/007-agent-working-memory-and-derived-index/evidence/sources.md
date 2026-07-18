# Fuentes y estado del arte

Observación realizada el **2026-07-16**. Estas fuentes describen Engram como
referencia externa; no son autoridad del canon EDAIOS ni promesa de rendimiento.

| Fuente | Versión/fecha observada | Alcance usado | Límite |
|---|---|---|---|
| [Engram README](https://github.com/Gentleman-Programming/engram) | release v1.19.0 observada 2026-07-16 | SQLite + FTS5, CLI/HTTP/MCP/TUI, setup, sesiones y sync | El README presenta capacidades de otro producto; no prueba compatibilidad EDAIOS |
| [Engram DOCS](https://github.com/Gentleman-Programming/engram/blob/main/DOCS.md) | main observado 2026-07-16 | endpoints de health, sessions, observations, search, timeline y conflicts | La detección semántica parte de candidatos lexicales; no descubre todos los conflictos |
| [Engram Architecture](https://github.com/Gentleman-Programming/engram/blob/main/docs/ARCHITECTURE.md) | main observado 2026-07-16 | progressive disclosure, lifecycle y memoria estructurada | Sus summaries son generados por agente y no equivalen a receipts EDAIOS |
| [Engram Agent Setup](https://github.com/Gentleman-Programming/engram/blob/main/docs/AGENT-SETUP.md) | main observado 2026-07-16 | configuración idempotente y detección ambigua fail-closed | EDAIOS restringe writes al proyecto y exige plan/apply/rollback |
| [Engram v1.19.0](https://github.com/Gentleman-Programming/engram/releases/tag/v1.19.0) | v1.19.0 | pin de referencia para el adapter opcional | No instala ni garantiza que el binario exista |
| [Engram LICENSE](https://github.com/Gentleman-Programming/engram/blob/main/LICENSE) | MIT observada 2026-07-16 | evaluación de reutilización | Esta feature reimplementa patrones; no copia código sustancial |

## Estado previo documentado

- `MEMORY_PORT.md` distingue memoria canónica, local y efímera, pero todavía no
  define un provider ejecutable.
- `CoreHarness.memory_port()` clasifica y calcula digest; no persiste ni busca.
- `KnowledgeClient.search()` hace búsqueda substring sobre el corpus completo.
- `.edaios/` está ignorado por Git.
- el adapter SDD ingiere borradores, pero no conserva revisiones
  content-addressed ni expone conflictos.
- AGENT-PARITY sincroniza comandos dentro del repo; no configura un consumer.

Estos hechos describen el punto de partida técnico de la feature y no un release
vigente. El resultado implementado quedó incorporado al baseline day-zero; su
evidencia actual está en `implementation-validation.md`.
