# SDK Consumption

API Python read-only para descubrir Knowledge Objects sin publicar, mutar o
promover conocimiento.

- `KnowledgeClient(root)` consume el corpus local de Foundation.
- `KnowledgeClient.from_mounts(path)` consume exclusivamente un documento
  `federation-mounts.json` gobernado. Valida attachments, AuthorityRegistry,
  owner activo, fronteras de ruta y digests; además revalida esa autoridad y el
  corpus antes y después de cada lectura pública.
- Las listas autoafirmadas de mounts no forman parte de la API pública. La capa
  de autoridad (`Consumer`) y la identidad humana del owner son contratos
  distintos y ambos deben permanecer resolubles.

El SDK es agnóstico de plataforma y sus vistas derivadas nunca reemplazan el
Git canónico de una iniciativa.
