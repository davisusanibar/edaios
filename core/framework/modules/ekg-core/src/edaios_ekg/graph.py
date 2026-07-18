from pathlib import Path
import json
from edaios_core.io import write_text
from edaios_core.knowledge import (
    FederationError,
    KnowledgeMount,
    corpus_digest,
    global_identity,
    iter_mount_files,
    normalize_mounts,
    resolve_authorized_path,
)


class GraphFederationError(FederationError):
    """La vista EKG derivada no puede construirse sin ambigüedad."""


class GraphCollisionError(GraphFederationError):
    """Dos artefactos EKG reclaman la misma identidad global."""


def load_ekg_specs(specs_dir):
    specs_root = Path(specs_dir)
    if specs_root.is_symlink():
        raise GraphFederationError(f"raíz EKG symlink no permitida: {specs_root}")
    graph_dir = specs_root / "knowledge-graph"
    specs = []
    if graph_dir.is_symlink():
        raise GraphFederationError(f"knowledge-graph symlink no permitido: {graph_dir}")
    if not graph_dir.exists():
        return specs
    if not graph_dir.is_dir():
        raise GraphFederationError(f"knowledge-graph no es directorio: {graph_dir}")

    def visit(directory):
        for entry in sorted(directory.iterdir()):
            if entry.is_symlink():
                raise GraphFederationError(f"knowledge-graph contiene symlink: {entry}")
            if entry.is_dir():
                yield from visit(entry)
            elif entry.is_file() and entry.suffix == ".json":
                yield entry

    for p in visit(graph_dir):
        try:
            value = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GraphFederationError(f"{p}: JSON inválido") from exc
        if not isinstance(value, dict):
            raise GraphFederationError(f"{p}: la raíz JSON debe ser objeto")
        kind = value.get("kind")
        if kind not in {"entity_type", "relationship_type", "entity", "relationship"}:
            raise GraphFederationError(f"{p}: kind inválido {kind!r}")
        identity = value.get("name") if kind.endswith("_type") else value.get("id")
        if not isinstance(identity, str) or not identity.strip():
            raise GraphFederationError(f"{p}: identidad ausente")
        specs.append((p, value))
    return specs


def build_graph(specs_dir):
    nodes = []
    edges = []
    entity_types = {}
    relationship_types = {}
    entity_type_sources = {}
    relationship_type_sources = {}

    for path, spec in load_ekg_specs(specs_dir):
        kind = spec.get("kind")
        if kind == "entity_type":
            if spec["name"] in entity_types:
                raise GraphCollisionError(
                    f"entity_type duplicado {spec['name']!r}: "
                    f"{entity_type_sources[spec['name']]} y {path}"
                )
            entity_types[spec["name"]] = spec
            entity_type_sources[spec["name"]] = path
        elif kind == "relationship_type":
            if spec["name"] in relationship_types:
                raise GraphCollisionError(
                    f"relationship_type duplicado {spec['name']!r}: "
                    f"{relationship_type_sources[spec['name']]} y {path}"
                )
            relationship_types[spec["name"]] = spec
            relationship_type_sources[spec["name"]] = path
        elif kind == "entity":
            node = {
                "id": spec["id"],
                "type": spec.get("type"),
                "name": spec.get("name"),
                "owner": spec.get("owner"),
                "status": spec.get("status"),
                "source": str(path.relative_to(specs_dir)),
                "attributes": spec.get("attributes", {}),
            }
            # Preserve curated provenance/metadata for consumers without changing
            # the canonical node contract used by existing code.
            for key in ("etiqueta", "standards", "source_evidence", "justified_by", "provisional"):
                if key in spec:
                    node[key] = spec[key]
            nodes.append(node)
        elif kind == "relationship":
            edge = {
                "id": spec["id"],
                "type": spec.get("type"),
                "from": spec.get("from"),
                "to": spec.get("to"),
                "source": str(path.relative_to(specs_dir)),
                "attributes": spec.get("attributes", {}),
            }
            for key in ("standards", "source_evidence", "justified_by", "provisional"):
                if key in spec:
                    edge[key] = spec[key]
            edges.append(edge)

    graph = {
        "entity_types": entity_types,
        "relationship_types": relationship_types,
        "nodes": nodes,
        "edges": edges,
    }
    errors = validate_graph(graph)
    if errors:
        raise GraphFederationError("; ".join(errors))
    return graph


def _qualified(namespace, value, *, allow_wildcard=False):
    if not isinstance(value, str) or not value.strip():
        raise GraphFederationError(
            f"{namespace}: una referencia EKG requiere un string no vacío"
        )
    value = value.strip()
    if allow_wildcard and value == "*":
        return value
    return value if ":" in value else global_identity(namespace, value)


def _qualified_constraint(namespace, value):
    if value is None:
        return None
    if isinstance(value, str):
        return _qualified(namespace, value, allow_wildcard=True)
    if isinstance(value, list):
        return [
            _qualified(namespace, item, allow_wildcard=True) for item in value
        ]
    raise GraphFederationError(
        f"{namespace}: domain/range debe ser string o lista de strings"
    )


def _graph_specs_root(mount: KnowledgeMount):
    path = mount.path
    if path.name == "knowledge-graph" and path.is_dir():
        return resolve_authorized_path(
            path,
            mount.authorized_root or mount.path,
            expected="directory",
            label=f"{mount.namespace}: knowledge-graph",
        )
    graph = path / "knowledge-graph"
    if graph.exists() or graph.is_symlink():
        return resolve_authorized_path(
            graph,
            mount.authorized_root or mount.path,
            expected="directory",
            label=f"{mount.namespace}: knowledge-graph",
        )
    raise GraphFederationError(f"mount EKG sin knowledge-graph explícito: {path}")


def build_federated_graph(mounts, *, minimum_mounts=2):
    """Construye una vista derivada solo desde mounts declarados.

    Los IDs y tipos locales se califican como ``namespace:id``. Referencias ya
    calificadas permiten relaciones entre mounts, pero deben resolverse al
    terminar. La función nunca busca automáticamente repositorios vecinos.
    """
    try:
        normalized = normalize_mounts(mounts, minimum=minimum_mounts)
    except FederationError as exc:
        raise GraphFederationError(str(exc)) from exc
    graph = {
        "schema": "edaios.ekg.federation/v1",
        "derived": True,
        "mounts": [
            {
                "namespace": mount.namespace,
                "path": str(mount.path),
                "authority_layer": mount.authority_layer,
                "owner_actor_id": mount.owner_actor_id,
            }
            for mount in normalized
        ],
        "entity_types": {},
        "relationship_types": {},
        "nodes": [],
        "edges": [],
    }
    identities = {
        "entity_type": set(),
        "relationship_type": set(),
        "entity": set(),
        "relationship": set(),
    }

    for mount in normalized:
        try:
            if (
                mount.corpus_sha256 is not None
                and corpus_digest(mount) != mount.corpus_sha256
            ):
                raise GraphFederationError(
                    f"{mount.namespace}: digest de corpus no coincide antes del consumo"
                )
            graph_dir = _graph_specs_root(mount)
            graph_paths = list(iter_mount_files(mount, graph_dir, suffix=".json"))
        except FederationError as exc:
            if isinstance(exc, GraphFederationError):
                raise
            raise GraphFederationError(str(exc)) from exc
        for path in graph_paths:
            try:
                spec = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise GraphFederationError(
                    f"{mount.namespace}:{path.relative_to(graph_dir)}: JSON inválido"
                ) from exc
            if not isinstance(spec, dict):
                raise GraphFederationError(
                    f"{mount.namespace}:{path.relative_to(graph_dir)}: raíz no es objeto"
                )
            kind = spec.get("kind")
            if kind not in identities:
                raise GraphFederationError(
                    f"{mount.namespace}:{path.relative_to(graph_dir)}: kind inválido {kind!r}"
                )
            local_id = spec.get("name") if kind.endswith("_type") else spec.get("id")
            gid = global_identity(mount.namespace, str(local_id or ""))
            if gid in identities[kind]:
                raise GraphCollisionError(
                    f"{kind} duplicado en {mount.namespace}: {local_id}"
                )
            identities[kind].add(gid)
            item = dict(spec)
            item.update(
                {
                    "namespace": mount.namespace,
                    "local_id": str(local_id),
                    "mount_authority": mount.authority_layer,
                    "mount_owner_actor_id": mount.owner_actor_id,
                    "source": (
                        f"{mount.namespace}:"
                        f"{path.relative_to(graph_dir).as_posix()}"
                    ),
                }
            )
            if kind == "entity_type":
                item["name"] = gid
                graph["entity_types"][gid] = item
            elif kind == "relationship_type":
                item["name"] = gid
                if "domain" in item:
                    item["domain"] = _qualified_constraint(
                        mount.namespace, item["domain"]
                    )
                if "range" in item:
                    item["range"] = _qualified_constraint(
                        mount.namespace, item["range"]
                    )
                graph["relationship_types"][gid] = item
            elif kind == "entity":
                item["id"] = gid
                item["type"] = _qualified(mount.namespace, item.get("type"))
                graph["nodes"].append(item)
            else:
                item["id"] = gid
                item["type"] = _qualified(mount.namespace, item.get("type"))
                item["from"] = _qualified(mount.namespace, item.get("from"))
                item["to"] = _qualified(mount.namespace, item.get("to"))
                graph["edges"].append(item)
        if (
            mount.corpus_sha256 is not None
            and corpus_digest(mount) != mount.corpus_sha256
        ):
            raise GraphFederationError(
                f"{mount.namespace}: corpus cambio durante el consumo"
            )

    errors = validate_graph(graph)
    if errors:
        raise GraphFederationError("; ".join(errors))
    return graph


def _allowed(actual_type, allowed):
    if not allowed:
        return True
    if isinstance(allowed, str):
        allowed = [allowed]
    return "*" in allowed or actual_type in set(allowed)


def validate_graph(graph):
    errors = []
    node_values = [n.get("id") for n in graph["nodes"]]
    edge_values = [e.get("id") for e in graph["edges"]]
    node_ids = {value for value in node_values if value}
    if len(node_ids) != len(node_values):
        errors.append("Identidades de entidad vacías o duplicadas")
    if len({value for value in edge_values if value}) != len(edge_values):
        errors.append("Identidades de relación vacías o duplicadas")
    node_types = {n["id"]: n.get("type") for n in graph["nodes"]}
    for edge in graph["edges"]:
        from_id, to_id, rel_type = edge.get("from"), edge.get("to"), edge.get("type")
        if from_id not in node_ids:
            errors.append(f"Relación {edge.get('id')} apunta from inexistente: {from_id}")
        if to_id not in node_ids:
            errors.append(f"Relación {edge.get('id')} apunta to inexistente: {to_id}")
        rel_spec = graph["relationship_types"].get(rel_type)
        if rel_spec is None:
            errors.append(f"Relación {edge.get('id')} usa tipo no definido: {rel_type}")
            continue
        # Semantic constraints are opt-in: only relationship specs that declare
        # `domain`/`range` are checked. This keeps backward compatibility with
        # older minimal graphs.
        if from_id in node_types and rel_spec.get("domain") and not _allowed(node_types[from_id], rel_spec.get("domain")):
            errors.append(
                f"Relación {edge.get('id')} ({rel_type}) viola domain: "
                f"from {from_id} es {node_types[from_id]}, esperado {rel_spec.get('domain')}"
            )
        if to_id in node_types and rel_spec.get("range") and not _allowed(node_types[to_id], rel_spec.get("range")):
            errors.append(
                f"Relación {edge.get('id')} ({rel_type}) viola range: "
                f"to {to_id} es {node_types[to_id]}, esperado {rel_spec.get('range')}"
            )
    for node in graph["nodes"]:
        if node.get("type") not in graph["entity_types"]:
            errors.append(f"Entidad {node.get('id')} usa tipo no definido: {node.get('type')}")
    return errors


def export_graph(graph, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    write_text(output / "ekg.json", json.dumps(graph, indent=2, ensure_ascii=False))
    write_text(output / "ekg.mmd", to_mermaid(graph))
    write_text(output / "README.md", graph_readme(graph))


def to_mermaid(graph):
    lines = ["flowchart TD"]
    for node in graph["nodes"]:
        safe_id = _safe(node["id"])
        label = f"{node['name']}\n({node['type']})"
        lines.append(f'  {safe_id}["{label}"]')
    for edge in graph["edges"]:
        lines.append(f"  {_safe(edge['from'])} -- {edge['type']} --> {_safe(edge['to'])}")
    return "\n".join(lines) + "\n"


def graph_readme(graph):
    return f"""# EDAIOS Enterprise Knowledge Graph

## Nodes

{len(graph['nodes'])}

## Edges

{len(graph['edges'])}

## Entity Types

{', '.join(sorted(graph['entity_types'].keys()))}

## Relationship Types

{', '.join(sorted(graph['relationship_types'].keys()))}
"""


def _safe(value):
    return str(value).replace("-", "_").replace(".", "_").replace(":", "_")
