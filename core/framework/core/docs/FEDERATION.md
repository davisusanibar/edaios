# Federación Git-first

Cada mount declara namespace dotted, path, root autorizado, attachment,
`authority_layer: Consumer`, `owner_actor_id` y digests de manifest,
AuthorityRegistry y corpus. La capa expresa el nivel de gobierno; el actor
expresa quién responde por la iniciativa y debe estar activo con rol
`initiative-owner`. No se infiere uno desde el otro ni desde el contenido. El
namespace forma la identidad global. El perfil `federation` exige dos o más
attachments conformes antes de leer el corpus y compara `corpus_sha256` antes y
después de cada operación pública para detectar drift concurrente. SDK y Query
revalidan además documento y AuthorityRegistry en ambos extremos; una revocación
o cambio exige reconstruir la vista. Core rechaza:

- mounts implícitos, autoafirmados, únicos o duplicados;
- manifest, authority registry, corpus o digest no resolubles;
- traversal y symlinks que escapen del root;
- identidades globales repetidas;
- tipos incompatibles bajo la misma identidad;
- relaciones cuyo destino no sea resoluble.

El Git de cada iniciativa es canónico. EKG, Query, catálogo y un futuro
Knowledge Hub son proyecciones derivadas y reconstruibles. Federar no concede a
Core autoridad sobre el dominio y no permite que una iniciativa gobierne
Foundation.

El contrato portable vive en
`../templates/initiative/federation-mounts.json` y su schema empaquetado. La
implementación verificable de attachments, mounts e identidades globales vive
en `../../modules/conformance-core/src/edaios_conformance/attachment.py` y
`../../modules/ekg-core/src/edaios_ekg/graph.py`; las APIs públicas
`KnowledgeClient.from_mounts(path)` y `QueryEngine.from_mounts(path)` exigen la
ruta al documento gobernado. SDK y Query no aceptan listas crudas ni descubren
repositorios de manera recursiva.
