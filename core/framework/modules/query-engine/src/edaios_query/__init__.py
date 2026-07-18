"""EDAIOS Query Engine (QRY-002) — núcleo de consulta de solo lectura sobre el EKG.

Implementa el contrato descrito en
`core/framework/modules/query-engine/OVERVIEW.md` (ADR-0003):
consultas de vecindad, dependencias, justificación, soporte e impacto (*blast-radius*)
sobre el grafo de dominio que construye `edaios_ekg`.

Principios (heredados): solo lectura; deriva del grafo (no inventa); informa el impacto
pero no decide. ``find`` puede devolver vacío; las consultas dirigidas bloquean un id
que no se pueda resolver, incluso cuando el grafo está vacío.
"""
from __future__ import annotations

import json
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from hashlib import sha256
from pathlib import Path

__version__ = "3.1.0"

JUSTIFY_RELATIONS = ("justified_by", "derives_from")


class NodeNotFound(Exception):
    """El node_id no existe en un grafo no vacío."""


class QueryCollisionError(ValueError):
    """El grafo no posee identidades inequívocas para consulta."""


def _mounts_fingerprint(mounts) -> str:
    return json.dumps(
        mounts, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )


def _mounts_document_snapshot(path: str | Path) -> tuple[Path, str]:
    raw_path = Path(path).expanduser()
    if raw_path.is_symlink():
        raise QueryCollisionError("federation mounts symlink no admitido")
    try:
        resolved = raw_path.resolve(strict=True)
    except OSError as exc:
        raise QueryCollisionError(
            f"federation mounts no resoluble: {raw_path}"
        ) from exc
    if not resolved.is_file():
        raise QueryCollisionError(
            f"federation mounts no es archivo: {resolved}"
        )
    try:
        digest = sha256(resolved.read_bytes()).hexdigest()
    except OSError as exc:
        raise QueryCollisionError(
            f"federation mounts no legible: {resolved}"
        ) from exc
    return resolved, digest


def _validate_stable_mounts_document(
    path: str | Path,
) -> tuple[Path, str, list[dict]]:
    from edaios_conformance import validate_federation_mounts

    before_path, before_digest = _mounts_document_snapshot(path)
    try:
        mounts = validate_federation_mounts(before_path)
    except (OSError, ValueError) as exc:
        raise QueryCollisionError(str(exc)) from exc
    after_path, after_digest = _mounts_document_snapshot(before_path)
    if before_path != after_path or before_digest != after_digest:
        raise QueryCollisionError(
            "federation mounts cambió durante la validación"
        )
    return after_path, after_digest, mounts


def _governed_query(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._governed_operation():
            return method(self, *args, **kwargs)

    return wrapped


@dataclass(frozen=True)
class NodeRef:
    id: str
    type: str | None
    name: str | None
    source: str | None = None
    namespace: str | None = None
    local_id: str | None = None

    def to_dict(self) -> dict:
        result = {
            "id": self.id, "type": self.type, "name": self.name,
            "source": self.source,
        }
        if self.namespace is not None:
            result["namespace"] = self.namespace
        if self.local_id is not None:
            result["local_id"] = self.local_id
        return result


@dataclass(frozen=True)
class EdgeRef:
    id: str
    type: str | None
    from_: str
    to: str
    namespace: str | None = None
    local_id: str | None = None

    def to_dict(self) -> dict:
        result = {
            "id": self.id, "type": self.type, "from": self.from_, "to": self.to,
        }
        if self.namespace is not None:
            result["namespace"] = self.namespace
        if self.local_id is not None:
            result["local_id"] = self.local_id
        return result


@dataclass(frozen=True)
class Subgraph:
    nodes: list
    edges: list

    def to_dict(self) -> dict:
        return {"nodes": [n.to_dict() for n in self.nodes], "edges": [e.to_dict() for e in self.edges]}


@dataclass(frozen=True)
class ImpactResult:
    root: NodeRef
    affected: list
    decisions: list
    paths: list

    def to_dict(self) -> dict:
        return {
            "root": self.root.to_dict(),
            "affected": [n.to_dict() for n in self.affected],
            "decisions": [n.to_dict() for n in self.decisions],
            "paths": self.paths,
        }


def _empty_graph() -> dict:
    return {"entity_types": {}, "relationship_types": {}, "nodes": [], "edges": []}


class QueryEngine:
    """Motor de consulta de solo lectura sobre el grafo de dominio (EKG)."""

    def __init__(self, root: str | Path = "."):
        from edaios_ekg.graph import build_graph

        local_root = Path(root).expanduser()
        if local_root.is_symlink():
            raise QueryCollisionError(
                f"la raíz EKG no puede ser symlink: {local_root}"
            )
        if local_root.name == "knowledge-graph":
            local_root = local_root.parent
        graph = build_graph(local_root)
        self._load(graph)

    @classmethod
    def from_graph(cls, graph: dict) -> "QueryEngine":
        self = cls.__new__(cls)
        self._load(graph)
        return self

    @classmethod
    def from_mounts(cls, mounts_document: str | Path) -> "QueryEngine":
        """Consume un FederationMount gobernado; no acepta listas autoafirmadas."""
        if not isinstance(mounts_document, (str, Path)):
            raise QueryCollisionError(
                "from_mounts exige la ruta a federation-mounts.json gobernado"
            )
        document, document_sha256, mounts = _validate_stable_mounts_document(
            mounts_document
        )
        graph_mounts = [
            mount for mount in mounts
            if (Path(str(mount["path"])) / "knowledge-graph").is_dir()
            or Path(str(mount["path"])).name == "knowledge-graph"
        ]
        if not graph_mounts:
            self = cls.from_graph(_empty_graph())
        else:
            self = cls._from_validated_mounts(graph_mounts, allow_single=True)
        self._mounts_document = document
        self._mounts_document_sha256 = document_sha256
        self._governed_mounts_fingerprint = _mounts_fingerprint(mounts)
        self._revalidate_governed_mounts()
        return self

    @classmethod
    def _from_validated_mounts(cls, mounts, *, allow_single: bool = False) -> "QueryEngine":
        """Construye desde mounts ya validados por conformance (uso interno)."""
        from edaios_ekg.graph import build_federated_graph

        self = cls.__new__(cls)
        graph = build_federated_graph(
            mounts, minimum_mounts=1 if allow_single else 2
        )
        self._load(graph)
        return self

    def _load(self, graph: dict) -> None:
        from edaios_ekg.graph import validate_graph

        self._mounts_document: Path | None = None
        self._mounts_document_sha256: str | None = None
        self._governed_mounts_fingerprint: str | None = None
        graph = {
            "nodes": list(graph.get("nodes", [])),
            "edges": list(graph.get("edges", [])),
            "entity_types": dict(graph.get("entity_types", {})),
            "relationship_types": dict(graph.get("relationship_types", {})),
        }
        validation_errors = validate_graph(graph)
        if validation_errors:
            raise QueryCollisionError("; ".join(validation_errors))
        nodes = list(graph.get("nodes", []))
        edges = list(graph.get("edges", []))
        node_ids = [n.get("id") for n in nodes]
        edge_ids = [e.get("id") for e in edges]
        if None in node_ids or len(node_ids) != len(set(node_ids)):
            raise QueryCollisionError("entidades con id vacío o duplicado")
        if None in edge_ids or len(edge_ids) != len(set(edge_ids)):
            raise QueryCollisionError("relaciones con id vacío o duplicado")
        self._nodes = {n["id"]: n for n in nodes}
        self._edges = edges
        self._out: dict[str, list] = {}
        self._in: dict[str, list] = {}
        for e in self._edges:
            self._out.setdefault(e.get("from"), []).append(e)
            self._in.setdefault(e.get("to"), []).append(e)
        self._entity_types = dict(graph.get("entity_types", {}))
        self._relationship_types = dict(graph.get("relationship_types", {}))

    # --- helpers ---
    def _revalidate_governed_mounts(self) -> None:
        if self._mounts_document is None:
            return
        document, document_sha256, mounts = _validate_stable_mounts_document(
            self._mounts_document
        )
        if (
            document != self._mounts_document
            or document_sha256 != self._mounts_document_sha256
            or _mounts_fingerprint(mounts)
            != self._governed_mounts_fingerprint
        ):
            raise QueryCollisionError(
                "federation mounts o su autoridad cambiaron; reconstruya el motor"
            )

    @contextmanager
    def _governed_operation(self):
        self._revalidate_governed_mounts()
        try:
            yield
        except BaseException:
            raise
        else:
            self._revalidate_governed_mounts()

    def _ref(self, node_id: str) -> NodeRef:
        n = self._nodes[node_id]
        return NodeRef(
            n["id"], n.get("type"), n.get("name"), n.get("source"),
            n.get("namespace"), n.get("local_id"),
        )

    def _present(self, node_id: str) -> bool:
        """True si hay que procesar; False si el grafo está vacío (latente).

        Lanza NodeNotFound si el grafo no está vacío pero el nodo no existe.
        """
        if node_id not in self._nodes:
            raise NodeNotFound(node_id)
        return True

    def _relation(self, node_id: str, relation: str) -> str:
        """Resuelve una relación local dentro del namespace del nodo."""
        if ":" in relation or ":" not in node_id:
            return relation
        namespace, _local = node_id.split(":", 1)
        return f"{namespace}:{relation}"

    # --- API (contrato QRY-001/ADR-0003) ---
    @_governed_query
    def find(
        self, type: str | None = None, name: str | None = None,
        namespace: str | None = None,
    ) -> list:
        out = []
        for n in self._nodes.values():
            if type is not None and n.get("type") != type:
                continue
            if name is not None and n.get("name") != name:
                continue
            if namespace is not None and n.get("namespace") != namespace:
                continue
            out.append(self._ref(n["id"]))
        out.sort(key=lambda item: item.id)
        return out

    @_governed_query
    def neighborhood(self, node_id: str, depth: int = 1, max_nodes: int | None = None) -> Subgraph:
        if not self._present(node_id):
            return Subgraph([], [])
        seen = {node_id}
        frontier = [node_id]
        edges_seen: dict = {}
        for _ in range(max(0, depth)):
            nxt = []
            for nid in frontier:
                for e in self._out.get(nid, []) + self._in.get(nid, []):
                    edges_seen[e.get("id")] = e
                    for other in (e.get("from"), e.get("to")):
                        if other in self._nodes and other not in seen:
                            if max_nodes is not None and len(seen) >= max_nodes:
                                continue
                            seen.add(other)
                            nxt.append(other)
            frontier = nxt
            if not frontier:
                break
        nodes = [self._ref(i) for i in sorted(seen)]
        edges = [
            EdgeRef(
                e.get("id"), e.get("type"), e.get("from"), e.get("to"),
                e.get("namespace"), e.get("local_id"),
            )
            for _edge_id, e in sorted(edges_seen.items())
        ]
        return Subgraph(nodes, edges)

    @_governed_query
    def dependents(self, node_id: str, relation: str = "depends_on") -> list:
        """Nodos que necesitan a node_id (aristas entrantes `relation`)."""
        if not self._present(node_id):
            return []
        relation = self._relation(node_id, relation)
        return [self._ref(e["from"]) for e in self._in.get(node_id, [])
                if e.get("type") == relation and e.get("from") in self._nodes]

    @_governed_query
    def dependencies(self, node_id: str, relation: str = "depends_on") -> list:
        """Nodos que node_id necesita (aristas salientes `relation`)."""
        if not self._present(node_id):
            return []
        relation = self._relation(node_id, relation)
        return [self._ref(e["to"]) for e in self._out.get(node_id, [])
                if e.get("type") == relation and e.get("to") in self._nodes]

    @_governed_query
    def justifications(self, node_id: str, relations: tuple = JUSTIFY_RELATIONS) -> list:
        """Nodos `Decision`/`ADR` que justifican a node_id."""
        if not self._present(node_id):
            return []
        relations = tuple(self._relation(node_id, relation) for relation in relations)
        return [self._ref(e["to"]) for e in self._out.get(node_id, [])
                if e.get("type") in relations and e.get("to") in self._nodes]

    @_governed_query
    def supporters(self, objective_id: str, relation: str = "supports") -> list:
        """Capacidades que soportan un objetivo (aristas entrantes `relation`)."""
        if not self._present(objective_id):
            return []
        relation = self._relation(objective_id, relation)
        return [self._ref(e["from"]) for e in self._in.get(objective_id, [])
                if e.get("type") == relation and e.get("from") in self._nodes]

    @_governed_query
    def impact(self, node_id: str, via: tuple = ("depends_on",)) -> ImpactResult:
        """Blast-radius: alcanzabilidad inversa transitiva por relaciones `via`.

        `A depends_on B` = A necesita a B (ADR-0003); por eso `impact(B)` recorre
        aristas entrantes para hallar todo lo que (transitivamente) necesita a B.
        """
        self._present(node_id)
        via = tuple(self._relation(node_id, relation) for relation in via)

        pred: dict[str, str] = {}
        order: list[str] = []
        visited = {node_id}
        q = deque([node_id])
        while q:
            cur = q.popleft()
            for e in self._in.get(cur, []):
                if e.get("type") in via:
                    dep = e.get("from")
                    if dep in self._nodes and dep not in visited:
                        visited.add(dep)
                        pred[dep] = cur
                        order.append(dep)
                        q.append(dep)

        affected = [self._ref(i) for i in order]
        paths = []
        for a in order:
            path = [a]
            cur = a
            while cur in pred:
                cur = pred[cur]
                path.append(cur)
            paths.append(path)

        dec_ids: list[str] = []
        seen_dec = set()
        for nid in [node_id] + order:
            justify_relations = {
                self._relation(nid, relation) for relation in JUSTIFY_RELATIONS
            }
            for e in self._out.get(nid, []):
                if e.get("type") in justify_relations and e.get("to") in self._nodes:
                    tid = e.get("to")
                    if tid not in seen_dec:
                        seen_dec.add(tid)
                        dec_ids.append(tid)
        decisions = [self._ref(i) for i in dec_ids]
        return ImpactResult(self._ref(node_id), affected, decisions, paths)
