# Knowledge Templates

Plantillas por tipo de Knowledge Object. Cada plantilla incluye el front-matter
del KOM y aplica los patrones de `core/framework/docs/patterns/`, de modo que
crear un KO nuevo sea consistente por construcción.

Uso: copia la plantilla, reemplaza los placeholders `<...>` y elimina las notas entre paréntesis.

| Plantilla | tipo | Para |
|---|---|---|
| `knowledge-object.md` | (cualquiera) | Base genérica de un KO |
| `article.md` | Article | Artículo constitucional |
| `adr.md` | ADR | Decisión arquitectónica |
| `rfc.md` | RFC | Propuesta de cambio |
| `pattern.md` | Pattern | Patrón de conocimiento |

Aplican: PAT-001 (front-matter), PAT-002 (relaciones tipadas), PAT-003 (versionado/supersesión).
