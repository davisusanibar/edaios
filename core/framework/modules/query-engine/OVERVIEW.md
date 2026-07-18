# Query Engine

Consulta read-only sobre un EKG. `find` puede devolver una lista vacía; las
consultas dirigidas (`neighborhood`, dependencias, justificaciones, soporte e
impacto) bloquean un identificador que no exista, también cuando el grafo está
vacío.

`QueryEngine.from_mounts(path)` acepta únicamente un documento
`federation-mounts.json` gobernado. Valida attachments, AuthorityRegistry,
owner activo, fronteras de ruta y digests, y revalida documento, autoridad y
corpus antes y después de cada consulta pública. Las listas autoafirmadas de
mounts quedan reservadas al acoplamiento interno ya validado.

El motor informa relaciones e impacto desde una vista derivada; no decide, no
inventa nodos y no adquiere autoridad sobre los Git canónicos.
