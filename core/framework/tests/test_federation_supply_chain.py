from pathlib import Path
import json
import tempfile
import unittest
import zipfile

from edaios_core.knowledge import (
    KnowledgeCollisionError,
    KnowledgeMount,
    corpus_digest,
)
from edaios_ekg.graph import (
    GraphCollisionError,
    GraphFederationError,
    build_federated_graph,
)
from edaios_query import QueryCollisionError, QueryEngine
from edaios_sdk_consumption import (
    InvalidKnowledge,
    InvalidMount,
    InvalidRoot,
    KOCollision,
    KnowledgeClient,
)
from edaios_supply_chain import (
    SupplyChainError,
    build_supply_chain_artifacts,
    verify_supply_chain_artifacts,
)


def write_ko(root: Path, filename: str, *, ko_id: str, authority: str) -> None:
    (root / filename).write_text(
        "\n".join(
            [
                "---",
                f"id: {ko_id}",
                "tipo: Principle",
                f"titulo: {ko_id}",
                "version: 1.0.0",
                "estado: Ratificado",
                "autoridad: Consumer",
                "idioma: es",
                f"owner: {authority}",
                "deriva_de: NONE",
                "---",
                "",
                f"Contenido {ko_id}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_graph(root: Path, *, cross_target: str | None = None) -> None:
    graph = root / "knowledge-graph"
    graph.mkdir()
    documents = {
        "entity-type.json": {"kind": "entity_type", "name": "Service"},
        "relation-type.json": {
            "kind": "relationship_type",
            "name": "depends_on",
            "domain": "Service",
            "range": "*" if cross_target else "Service",
        },
        "service.json": {
            "kind": "entity",
            "id": "service",
            "type": "Service",
            "name": root.name,
        },
    }
    if cross_target:
        documents["edge.json"] = {
            "kind": "relationship",
            "id": "dependency",
            "type": "depends_on",
            "from": "service",
            "to": cross_target,
        }
    for filename, document in documents.items():
        (graph / filename).write_text(
            json.dumps(document, sort_keys=True) + "\n", encoding="utf-8"
        )


def write_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in (("alpha.txt", b"alpha\n"), ("pkg/module.py", b"VALUE = 1\n")):
            info = zipfile.ZipInfo(name, (2026, 7, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)


def mount(namespace: str, path: Path, authority: str, authorized_root: Path | None = None):
    value = {
        "namespace": namespace if "." in namespace else f"{namespace}.scope",
        "path": path,
        "authority_layer": "Consumer",
        "owner_actor_id": authority,
        "allowed_owner_actor_ids": [authority],
        "authorized_root": authorized_root or path,
        "corpus_sha256": None,
    }
    value["corpus_sha256"] = corpus_digest(KnowledgeMount.from_value(value))
    return value


def companion(root: Path, *, graph: bool = False):
    path = root / "companion"
    path.mkdir(exist_ok=True)
    if graph:
        write_graph(path)
    return mount("companion.scope", path, "Companion", root)


class FederatedKnowledgeTests(unittest.TestCase):
    def test_public_mount_apis_reject_raw_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = root / "alpha"
            beta = root / "beta"
            alpha.mkdir()
            beta.mkdir()
            mounts = [
                mount("alpha.scope", alpha, "Alpha", root),
                mount("beta.scope", beta, "Beta", root),
            ]
            with self.assertRaisesRegex(InvalidMount, "federation-mounts.json"):
                KnowledgeClient.from_mounts(mounts)
            with self.assertRaisesRegex(QueryCollisionError, "federation-mounts.json"):
                QueryEngine.from_mounts(mounts)

    def test_same_local_ko_id_is_valid_across_explicit_namespaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha, beta = root / "alpha", root / "beta"
            alpha.mkdir()
            beta.mkdir()
            write_ko(alpha, "principle.md", ko_id="KO-001", authority="Alpha")
            write_ko(beta, "principle.md", ko_id="KO-001", authority="Beta")

            client = KnowledgeClient._from_validated_mounts(
                [
                    mount("alpha.scope", alpha, "Alpha"),
                    mount("beta.scope", beta, "Beta"),
                ]
            )
            self.assertEqual(
                [item.id for item in client.list_kos()],
                ["alpha.scope:KO-001", "beta.scope:KO-001"],
            )
            self.assertEqual(client.get_ko("beta.scope:KO-001").namespace, "beta.scope")

    def test_get_rechecks_corpus_after_final_content_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = root / "alpha"
            beta = root / "beta"
            alpha.mkdir()
            beta.mkdir()
            write_ko(alpha, "ko.md", ko_id="KO-001", authority="Alpha")
            write_ko(beta, "ko.md", ko_id="KO-002", authority="Beta")
            client = KnowledgeClient._from_validated_mounts([
                mount("alpha.scope", alpha, "Alpha"),
                mount("beta.scope", beta, "Beta"),
            ])
            original_index = client._index

            def raced_index():
                index = original_index()
                (alpha / "ko.md").write_text(
                    (alpha / "ko.md").read_text(encoding="utf-8") + "tamper\n",
                    encoding="utf-8",
                )
                return index

            client._index = raced_index
            with self.assertRaisesRegex(InvalidMount, "lectura final"):
                client.get_ko("alpha.scope:KO-001")

    def test_explicit_authorized_root_allows_a_nested_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            authorized = Path(tmp) / "initiatives"
            alpha = authorized / "alpha"
            alpha.mkdir(parents=True)
            write_ko(alpha, "principle.md", ko_id="KO-001", authority="Alpha")

            client = KnowledgeClient._from_validated_mounts(
                [
                    mount("alpha.scope", alpha, "Alpha", authorized),
                    companion(Path(tmp)),
                ]
            )

            self.assertEqual([item.id for item in client.list_kos()], ["alpha.scope:KO-001"])

    def test_traversal_or_path_outside_authorized_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            authorized = root / "authorized"
            nested = authorized / "nested"
            outside = root / "outside"
            nested.mkdir(parents=True)
            outside.mkdir()
            write_ko(outside, "principle.md", ko_id="KO-001", authority="Alpha")

            rejected = (
                authorized / "nested" / ".." / ".." / "outside",
                outside,
            )
            for candidate in rejected:
                with self.subTest(candidate=candidate), self.assertRaises(InvalidMount):
                    KnowledgeClient._from_validated_mounts(
                        [
                            {
                                "namespace": "alpha.scope",
                                "path": candidate,
                                "authority_layer": "Consumer",
                                "owner_actor_id": "Alpha",
                                "allowed_owner_actor_ids": ["Alpha"],
                                "authorized_root": authorized,
                                "corpus_sha256": None,
                            },
                            companion(root),
                        ]
                    )

    def test_mount_or_ko_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            authorized = root / "authorized"
            mount = authorized / "alpha"
            outside = root / "outside"
            mount.mkdir(parents=True)
            outside.mkdir()
            write_ko(outside, "principle.md", ko_id="KO-001", authority="Alpha")

            mount_link = authorized / "linked-mount"
            mount_link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(InvalidMount):
                KnowledgeClient._from_validated_mounts(
                    [
                        {
                            "namespace": "alpha.scope",
                            "path": mount_link,
                            "authority_layer": "Consumer",
                            "owner_actor_id": "Alpha",
                            "allowed_owner_actor_ids": ["Alpha"],
                            "authorized_root": authorized,
                            "corpus_sha256": None,
                        },
                        companion(root),
                    ]
                )

            (mount / "linked-ko.md").symlink_to(outside / "principle.md")
            client = KnowledgeClient._from_validated_mounts(
                [
                    {
                        "namespace": "alpha.scope",
                        "path": mount,
                        "authority_layer": "Consumer",
                        "owner_actor_id": "Alpha",
                        "allowed_owner_actor_ids": ["Alpha"],
                        "authorized_root": authorized,
                        "corpus_sha256": None,
                    },
                    companion(root),
                ]
            )
            with self.assertRaises(InvalidMount):
                client.list_kos()

    def test_collision_inside_one_namespace_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_ko(root, "one.md", ko_id="KO-001", authority="Alpha")
            write_ko(root, "two.md", ko_id="KO-001", authority="Alpha")
            client = KnowledgeClient._from_validated_mounts(
                [mount("alpha.scope", root, "Alpha"), companion(root)]
            )
            with self.assertRaises(KOCollision):
                client.list_kos()

    def test_mounted_ko_requires_consumer_layer_and_active_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = root / "alpha"
            alpha.mkdir()
            write_ko(alpha, "ko.md", ko_id="KO-001", authority="INACTIVE")
            client = KnowledgeClient._from_validated_mounts([
                mount("alpha.scope", alpha, "ACTIVE"), companion(root),
            ])
            with self.assertRaisesRegex(InvalidMount, "no está activo"):
                client.list_kos()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = root / "alpha"
            alpha.mkdir()
            write_ko(alpha, "ko.md", ko_id="KO-001", authority="ACTIVE")
            ko_path = alpha / "ko.md"
            ko_path.write_text(
                ko_path.read_text(encoding="utf-8").replace(
                    "autoridad: Consumer", "autoridad: Core"
                ),
                encoding="utf-8",
            )
            client = KnowledgeClient._from_validated_mounts([
                mount("alpha.scope", alpha, "ACTIVE"), companion(root),
            ])
            with self.assertRaisesRegex(InvalidMount, "authority layer"):
                client.list_kos()

    def test_duplicate_namespace_or_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_ko(root, "one.md", ko_id="KO-001", authority="Alpha")
            aliased = mount("beta.scope", root, "Alpha")
            aliased["path"] = f"{root}/."
            with self.assertRaises(KOCollision):
                KnowledgeClient._from_validated_mounts(
                    [
                        mount("alpha.scope", root, "Alpha"),
                        aliased,
                    ]
                )

    def test_local_reader_rejects_incomplete_ko_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            foundation = root / "core/foundation"
            governance = root / "governance"
            foundation.mkdir(parents=True)
            governance.mkdir()
            (root / "README.md").write_text("root\n")
            (governance / "ADR_CATALOG.md").write_text("# catalog\n")
            (foundation / "bad.md").write_text(
                "---\nid: KO-001\n---\n\nincomplete\n",
            )
            with self.assertRaises(InvalidKnowledge):
                KnowledgeClient(root).list_kos()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            foundation = root / "core/foundation"
            governance = root / "governance"
            outside = root / "outside.md"
            foundation.mkdir(parents=True)
            governance.mkdir()
            (root / "README.md").write_text("root\n")
            (governance / "ADR_CATALOG.md").write_text("# catalog\n")
            outside.write_text("outside\n")
            (foundation / "linked.md").symlink_to(outside)
            with self.assertRaises(InvalidKnowledge):
                KnowledgeClient(root).list_kos()

    def test_local_reader_rejects_symlinked_root_or_authority_component(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            actual = parent / "actual"
            foundation = actual / "core/foundation"
            governance = actual / "governance"
            foundation.mkdir(parents=True)
            governance.mkdir()
            (actual / "README.md").write_text("root\n")
            (governance / "ADR_CATALOG.md").write_text("# catalog\n")
            write_ko(foundation, "ko.md", ko_id="KO-001", authority="Core")
            linked_root = parent / "linked-root"
            try:
                linked_root.symlink_to(actual, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks no disponibles: {exc}")
            with self.assertRaises(InvalidRoot):
                KnowledgeClient(linked_root)

        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "program"
            outside_core = parent / "outside-core"
            governance = root / "governance"
            (outside_core / "foundation").mkdir(parents=True)
            governance.mkdir(parents=True)
            (root / "README.md").write_text("root\n")
            (governance / "ADR_CATALOG.md").write_text("# catalog\n")
            write_ko(
                outside_core / "foundation", "ko.md",
                ko_id="KO-001", authority="Core",
            )
            (root / "core").symlink_to(outside_core, target_is_directory=True)
            with self.assertRaises(InvalidRoot):
                KnowledgeClient(root)

    def test_local_reader_rejects_truncated_or_duplicate_front_matter(self):
        documents = {
            "truncated.md": "---\nid: KO-001\ntipo: Principle\n",
            "duplicate.md": "\n".join([
                "---", "id: KO-001", "id: KO-002", "tipo: Principle",
                "titulo: Duplicate", "version: 1.0.0", "estado: Ratificado",
                "autoridad: Core", "idioma: es", "owner: Core",
                "deriva_de: NONE", "---", "", "body", "",
            ]),
            "invalid-state.md": "\n".join([
                "---", "id: KO-001", "tipo: Principle",
                "titulo: Invalid", "version: 1.0.0", "estado: UNKNOWN",
                "autoridad: Foundation", "idioma: es", "owner: Foundation",
                "deriva_de: NONE", "---", "", "body", "",
            ]),
            "empty-id.md": "\n".join([
                "---", "id: ", "tipo: Principle", "titulo: Invalid",
                "version: 1.0.0", "estado: Ratificado",
                "autoridad: Foundation", "idioma: es", "owner: Foundation",
                "deriva_de: NONE", "---", "", "body", "",
            ]),
        }
        for filename, content in documents.items():
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                foundation = root / "core/foundation"
                governance = root / "governance"
                foundation.mkdir(parents=True)
                governance.mkdir()
                (root / "README.md").write_text("root\n")
                (governance / "ADR_CATALOG.md").write_text("# catalog\n")
                (foundation / filename).write_text(content)
                with self.assertRaises(InvalidKnowledge):
                    KnowledgeClient(root).list_kos()


class FederatedGraphTests(unittest.TestCase):
    def test_explicit_mounts_namespace_nodes_and_resolve_cross_mount_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha, beta = root / "alpha", root / "beta"
            alpha.mkdir()
            beta.mkdir()
            write_graph(alpha, cross_target="beta.scope:service")
            write_graph(beta)
            mounts = [
                mount("alpha.scope", alpha, "Alpha"),
                mount("beta.scope", beta, "Beta"),
            ]

            graph = build_federated_graph(mounts)
            self.assertEqual(
                {node["id"] for node in graph["nodes"]},
                {"alpha.scope:service", "beta.scope:service"},
            )
            engine = QueryEngine._from_validated_mounts(mounts)
            self.assertEqual(
                [node.id for node in engine.dependencies("alpha.scope:service")],
                ["beta.scope:service"],
            )
            self.assertEqual(
                [node.id for node in engine.find(namespace="beta.scope")],
                ["beta.scope:service"],
            )

    def test_implicit_recursive_discovery_does_not_create_federation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / "initiative"
            child.mkdir()
            write_graph(child)
            self.assertEqual(QueryEngine(root).find(), [])

    def test_unresolved_global_reference_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = root / "alpha"
            beta = root / "beta"
            alpha.mkdir()
            beta.mkdir()
            write_graph(alpha, cross_target="missing:service")
            write_graph(beta)
            with self.assertRaises(GraphFederationError):
                build_federated_graph(
                    [
                        mount("alpha.scope", alpha, "Alpha"),
                        mount("beta.scope", beta, "Beta"),
                    ]
                )

    def test_symlinked_graph_corpus_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            authorized = root / "authorized"
            alpha = authorized / "alpha"
            outside = root / "outside"
            alpha.mkdir(parents=True)
            outside.mkdir()
            write_graph(outside)
            (alpha / "knowledge-graph").symlink_to(
                outside / "knowledge-graph", target_is_directory=True
            )
            beta = authorized / "beta"
            beta.mkdir()
            write_graph(beta)

            with self.assertRaises(GraphFederationError):
                build_federated_graph(
                    [
                        {
                            "namespace": "alpha.scope",
                            "path": alpha,
                            "authority_layer": "Consumer",
                            "owner_actor_id": "Alpha",
                            "allowed_owner_actor_ids": ["Alpha"],
                            "authorized_root": authorized,
                            "corpus_sha256": None,
                        },
                        mount("beta.scope", beta, "Beta", authorized),
                    ]
                )

    def test_query_rejects_duplicate_ids_even_for_direct_graph(self):
        graph = {
            "entity_types": {},
            "relationship_types": {},
            "nodes": [{"id": "same"}, {"id": "same"}],
            "edges": [],
        }
        with self.assertRaises(QueryCollisionError):
            QueryEngine.from_graph(graph)

    def test_local_graph_rejects_symlinked_root_and_duplicate_type_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            actual = parent / "actual"
            actual.mkdir()
            write_graph(actual)
            linked_root = parent / "linked-root"
            try:
                linked_root.symlink_to(actual, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks no disponibles: {exc}")
            with self.assertRaises(QueryCollisionError):
                QueryEngine(linked_root)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph = root / "knowledge-graph"
            graph.mkdir()
            for filename in ("type-a.json", "type-b.json"):
                (graph / filename).write_text(json.dumps({
                    "kind": "entity_type", "name": "Service",
                }))
            with self.assertRaises(GraphCollisionError):
                QueryEngine(root)

    def test_local_graph_rejects_invalid_json_and_orphan_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph = Path(tmp) / "knowledge-graph"
            graph.mkdir()
            (graph / "broken.json").write_text("{not-json")
            with self.assertRaises(GraphFederationError):
                QueryEngine(tmp)
        with tempfile.TemporaryDirectory() as tmp:
            graph = Path(tmp) / "knowledge-graph"
            graph.mkdir()
            documents = {
                "entity-type.json": {"kind": "entity_type", "name": "Service"},
                "relation-type.json": {
                    "kind": "relationship_type", "name": "depends_on",
                },
                "service.json": {
                    "kind": "entity", "id": "service", "type": "Service",
                },
                "edge.json": {
                    "kind": "relationship", "id": "edge",
                    "type": "depends_on", "from": "service", "to": "missing",
                },
            }
            for name, value in documents.items():
                (graph / name).write_text(json.dumps(value))
            with self.assertRaises(GraphFederationError):
                QueryEngine(tmp)


class SupplyChainTests(unittest.TestCase):
    def test_sidecars_are_reproducible_and_verifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subject = root / "edaios_core-2.0.0-py3-none-any.whl"
            material = root / "source.py"
            material.write_text("VALUE = 1\n", encoding="utf-8")
            write_zip(subject)
            materials = {"src/source.py": material}
            first = build_supply_chain_artifacts(
                subject, root / "first", version="2.0.0", materials=materials
            )
            second = build_supply_chain_artifacts(
                subject, root / "second", version="2.0.0", materials=materials
            )
            for key in ("checksum", "sbom", "provenance"):
                self.assertEqual(first[key].read_bytes(), second[key].read_bytes())
            result = verify_supply_chain_artifacts(
                first["subject"], first["checksum"], first["sbom"],
                first["provenance"], materials=materials,
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["signature"], "absent")

    def test_subject_or_sidecar_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subject = root / "core.whl"
            write_zip(subject)
            artifacts = build_supply_chain_artifacts(
                subject, root / "out", version="2.0.0"
            )
            artifacts["provenance"].write_text("{}\n", encoding="utf-8")
            with self.assertRaises(SupplyChainError):
                verify_supply_chain_artifacts(
                    artifacts["subject"], artifacts["checksum"], artifacts["sbom"],
                    artifacts["provenance"],
                )


if __name__ == "__main__":
    unittest.main()
