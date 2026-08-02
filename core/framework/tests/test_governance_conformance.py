"""Contract tests for governance grammar, KOM and cumulative profiles."""

from __future__ import annotations

import importlib.util
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr
from hashlib import sha256
from pathlib import Path

from edaios_conformance import initialize_attachment
from edaios_core.knowledge import KnowledgeMount, corpus_digest
from edaios_query import QueryCollisionError, QueryEngine
from edaios_sdk_consumption import InvalidMount, KnowledgeClient


ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves postponed annotations through sys.modules.
    import sys
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class GovernanceGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grammar = json.loads(
            (ROOT / "core/framework/core/profiles/governance-grammar.json").read_text(
                encoding="utf-8"
            )
        )
        registry = json.loads(
            (ROOT / "core/framework/core/profiles/validation-profiles.json").read_text(
                encoding="utf-8"
            )
        )
        cls.profiles = {
            row["id"]: json.loads((ROOT / row["path"]).read_text(encoding="utf-8"))
            for row in registry["profiles"]
        }

    def test_rfc_identity_and_specialized_states_are_canonical(self) -> None:
        pattern = re.compile(self.grammar["id_patterns"]["RFC"])
        self.assertIsNotNone(pattern.fullmatch("RFC-0001"))
        self.assertIsNone(pattern.fullmatch("RFC-" + "001"))
        self.assertEqual(
            self.grammar["state_mappings"]["ADR"]["Aceptado"], "Ratificado"
        )
        self.assertEqual(
            self.grammar["state_mappings"]["Feature"]["Cerrado"], "Ratificado"
        )

    def test_profiles_are_strictly_cumulative(self) -> None:
        rows = self.profiles
        self.assertIsNone(rows["core-release"]["parent"])
        self.assertEqual(rows["initiative-adoption"]["parent"], "core-release")
        self.assertEqual(rows["federation"]["parent"], "initiative-adoption")
        core = set(rows["core-release"]["controls"])
        adoption = core | set(rows["initiative-adoption"]["controls"])
        federation = adoption | set(rows["federation"]["controls"])
        self.assertLess(core, adoption)
        self.assertLess(adoption, federation)

    def test_all_rfc_templates_use_four_digits(self) -> None:
        templates = (
            ROOT / "governance/templates/rfc.md",
            ROOT / "core/framework/templates/governance/rfc-template.md",
        )
        for template in templates:
            text = template.read_text(encoding="utf-8")
            self.assertIn("RFC-NNNN", text)
            self.assertNotRegex(text, r"RFC-NNN(?!N)")


class KomGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kom = load_module("test_kom_gate", "tools/validation/kom_gate.py")
        cls.grammar, cls.entities = cls.kom.load_contracts(ROOT)

    def _federation_document(self, root: Path) -> tuple[Path, list[dict[str, str]]]:
        mounts: list[dict[str, str]] = []
        for suffix in ("one", "two"):
            owner = f"OWNER-{suffix.upper()}"
            attachment = root / suffix
            attachment.mkdir()
            (attachment / ".git").mkdir()
            (attachment / "README.md").write_text(f"{suffix}\n", encoding="utf-8")
            initialize_attachment(
                attachment,
                initiative_id=f"kom-{suffix}",
                namespace=f"kom.{suffix}",
                owner=owner,
                value_owner=f"VALUE-{suffix.upper()}",
            )
            manifest_path = attachment / "edaios.initiative.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["conformance_profile"] = "federation"
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
            )
            corpus = attachment / "corpus"
            corpus.mkdir()
            (corpus / f"ko-{suffix}.md").write_text(
                "\n".join(
                    [
                        "---",
                        f"id: KO-{suffix.upper()}",
                        "tipo: Standard",
                        f"titulo: Fixture {suffix}",
                        "version: 1.0.0",
                        "estado: Ratificado",
                        "autoridad: Consumer",
                        "idioma: es",
                        f"owner: {owner}",
                        "deriva_de: Foundation",
                        "---",
                        "",
                        f"Fixture {suffix}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            authority_path = attachment / ".edaios/authority-registry.json"
            mounts.append(
                {
                    "namespace": f"kom.{suffix}",
                    "path": str(corpus),
                    "authorized_root": str(attachment),
                    "authority_layer": "Consumer",
                    "owner_actor_id": owner,
                    "attachment": str(attachment),
                    "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
                    "authority_registry_sha256": sha256(
                        authority_path.read_bytes()
                    ).hexdigest(),
                    "corpus_sha256": corpus_digest(
                        KnowledgeMount.from_value(
                            {
                                "namespace": f"kom.{suffix}",
                                "path": corpus,
                                "authorized_root": attachment,
                                "authority_layer": "Consumer",
                                "owner_actor_id": owner,
                                "allowed_owner_actor_ids": [owner],
                                "corpus_sha256": None,
                            }
                        )
                    ),
                }
            )
        mounts_path = root / "federation-mounts.json"
        mounts_path.write_text(
            json.dumps(
                {"schema": "edaios.federation-mounts/v1", "mounts": mounts},
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return mounts_path, mounts

    def test_installed_corpus_executes_vr_01_to_11(self) -> None:
        objects = self.kom.scan_scope(
            ROOT, self.kom.CORE_NAMESPACE, core_scope=True
        )
        rules = self.kom.evaluate(ROOT, objects, self.grammar, self.entities)
        self.assertEqual(
            [rule.id for rule in rules],
            [f"KOM-VR-{n:02d}" for n in range(1, 12)] + ["DERIVA-PROSA"],
        )
        self.assertTrue(all(rule.checked > 0 for rule in rules))
        self.assertEqual([], [error for rule in rules for error in rule.errors])

    def test_unresolved_mount_relation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scope = Path(temporary)
            (scope / ".git").mkdir()
            (scope / "broken.md").write_text(
                """---
id: KO-BROKEN
tipo: Standard
titulo: Broken fixture
version: 1.0.0
estado: Borrador
autoridad: Consumer
idioma: es
owner: Fixture
deriva_de: KO-MISSING
---

# Broken fixture
""",
                encoding="utf-8",
            )
            core = self.kom.scan_scope(
                ROOT, self.kom.CORE_NAMESPACE, core_scope=True
            )
            mounted = self.kom.scan_scope(
                scope, "fixture.scope", core_scope=False
            )
            rules = self.kom.evaluate(ROOT, core + mounted, self.grammar, self.entities)
            vr05 = next(rule for rule in rules if rule.id == "KOM-VR-05")
            self.assertTrue(any("KO-MISSING" in error for error in vr05.errors))

    def test_kom_frontmatter_truncado_o_duplicado_falla_cerrado(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            truncated = root / "truncated.md"
            truncated.write_text("---\nid: KO-BROKEN\ntipo: Standard\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "truncado"):
                self.kom.markdown_ko(truncated, "fixture.scope", root)

            duplicate = root / "duplicate.md"
            duplicate.write_text(
                "---\nid: KO-ONE\nid: KO-TWO\ntipo: Standard\n---\nbody\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicada"):
                self.kom.markdown_ko(duplicate, "fixture.scope", root)

    def test_only_governed_federation_mounts_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mounts_path, mounts = self._federation_document(root)
            objects = self.kom.load_federated_objects(mounts_path)
            self.assertEqual(
                [item.namespace for item in objects], ["kom.one", "kom.two"]
            )
            rules = self.kom.evaluate(ROOT, objects, self.grammar, self.entities)
            self.assertEqual([], [error for rule in rules for error in rule.errors])
            self.assertEqual(
                [item.id for item in KnowledgeClient.from_mounts(mounts_path).list_kos()],
                ["kom.one:KO-ONE", "kom.two:KO-TWO"],
            )
            self.assertEqual(QueryEngine.from_mounts(mounts_path).find(), [])

            corpus_file = root / "one/corpus/ko-one.md"
            original = corpus_file.read_text(encoding="utf-8")
            corpus_file.write_text(original + "tamper\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest de corpus"):
                self.kom.load_federated_objects(mounts_path)
            corpus_file.write_text(original, encoding="utf-8")

            mounts[0]["manifest_sha256"] = "f" * 64
            mounts_path.write_text(
                json.dumps(
                    {"schema": "edaios.federation-mounts/v1", "mounts": mounts}
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "digest"):
                self.kom.load_federated_objects(mounts_path)

    def test_governed_consumers_revalidate_authority_each_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mounts_path, mounts = self._federation_document(root)
            client = KnowledgeClient.from_mounts(mounts_path)
            engine = QueryEngine.from_mounts(mounts_path)

            authority_path = root / "one/.edaios/authority-registry.json"
            authority = json.loads(authority_path.read_text(encoding="utf-8"))
            authority["actors"][0]["active"] = False
            authority_path.write_text(
                json.dumps(authority, sort_keys=True) + "\n", encoding="utf-8"
            )
            mounts[0]["authority_registry_sha256"] = sha256(
                authority_path.read_bytes()
            ).hexdigest()
            mounts_path.write_text(
                json.dumps(
                    {"schema": "edaios.federation-mounts/v1", "mounts": mounts},
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            sdk_operations = (
                client.list_kos,
                lambda: list(client.iter_kos()),
                lambda: client.get_ko("kom.one:KO-ONE"),
                lambda: client.get_representation("kom.one:KO-ONE"),
                lambda: client.search("Fixture"),
            )
            for operation in sdk_operations:
                with self.subTest(operation=operation):
                    with self.assertRaises(InvalidMount):
                        operation()
            with self.assertRaises(QueryCollisionError):
                engine.find()

    def test_governed_consumers_reject_mount_document_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mounts_path, _mounts = self._federation_document(root)
            client = KnowledgeClient.from_mounts(mounts_path)
            engine = QueryEngine.from_mounts(mounts_path)

            mounts_path.write_text(
                mounts_path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(InvalidMount, "reconstruya"):
                client.list_kos()
            with self.assertRaisesRegex(QueryCollisionError, "reconstruya"):
                engine.find()

    def test_governed_consumers_revalidate_corpus_each_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mounts_path, _mounts = self._federation_document(root)
            client = KnowledgeClient.from_mounts(mounts_path)
            engine = QueryEngine.from_mounts(mounts_path)

            corpus_file = root / "one/corpus/ko-one.md"
            corpus_file.write_text(
                corpus_file.read_text(encoding="utf-8") + "tamper\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(InvalidMount, "digest de corpus"):
                client.list_kos()
            with self.assertRaisesRegex(QueryCollisionError, "digest de corpus"):
                engine.find()

    def test_self_asserted_mount_and_single_segment_namespace_are_rejected(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            self.kom.argument_parser().parse_args(
                [".", "--mount", "team.scope=/tmp/team"]
            )
        self.assertEqual(caught.exception.code, 2)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mounts_path, mounts = self._federation_document(root)
            mounts[0]["namespace"] = "team"
            mounts_path.write_text(
                json.dumps(
                    {"schema": "edaios.federation-mounts/v1", "mounts": mounts}
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "namespace"):
                self.kom.load_federated_objects(mounts_path)

    def test_federated_corpus_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mounts_path, _mounts = self._federation_document(root)
            linked_document = root / "linked-mounts.json"
            linked_document.symlink_to(mounts_path)
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.kom.load_federated_objects(linked_document)

            outside = root / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            (root / "one/corpus/linked.md").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.kom.load_federated_objects(mounts_path)


class ProfileAwareGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec_gate = load_module(
            "test_spec_kit_gate", "tools/validation/spec_kit_gate.py"
        )
        cls.structure = load_module(
            "test_monorepo_structure", "tools/validation/monorepo_structure_check.py"
        )

    def test_spec_gate_resolves_every_profile_without_weakening(self) -> None:
        for profile in ("core-release", "initiative-adoption", "federation"):
            results = self.spec_gate.Results()
            controls = self.spec_gate.load_validation_profile(ROOT, profile, results)
            self.assertTrue(results.ok, profile)
            self.assertTrue(controls)

    def test_attachment_must_be_external_and_explicit(self) -> None:
        with self.assertRaises(ValueError):
            self.structure.attachment("team=" + str(ROOT / "specs"), ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            namespace, path = self.structure.attachment(
                "team.scope=" + temporary, ROOT
            )
            self.assertEqual(namespace, "team.scope")
            self.assertEqual(path, Path(temporary).resolve())


if __name__ == "__main__":
    unittest.main()


class ResolvableContractsTests(unittest.TestCase):
    """Regresiones de specs/012: contratos resolubles (ADR-0018, RFC-0003 D1)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.kom = load_module("test_kom_gate_012", "tools/validation/kom_gate.py")
        cls.conformance = load_module(
            "test_core_conformance_012", "tools/validation/core_conformance_check.py"
        )
        cls.grammar, cls.entities = cls.kom.load_contracts(ROOT)

    def _fixture_ko(self, path, tipo: str, body: str = "") -> None:
        path.write_text(
            "---\n"
            "id: KO-FIXTURE-DOCE\n"
            f"tipo: {tipo}\n"
            "titulo: Fixture specs/012\n"
            "version: 1.0.0\n"
            "estado: Borrador\n"
            "autoridad: Consumer\n"
            "idioma: es\n"
            "owner: Fixture\n"
            "deriva_de: Foundation\n"
            "---\n\n# Fixture\n" + body,
            encoding="utf-8",
        )

    def test_tipo_relacion_falla_cerrado(self) -> None:
        # D1: el raspado fail-open aceptaba `governs` como tipo de entidad.
        with tempfile.TemporaryDirectory() as temporary:
            scope = Path(temporary)
            (scope / ".git").mkdir()
            self._fixture_ko(scope / "governs.md", "governs")
            mounted = self.kom.scan_scope(scope, "fixture.scope", core_scope=False)
            rules = self.kom.evaluate(ROOT, mounted, self.grammar, self.entities)
            vr02 = next(rule for rule in rules if rule.id == "KOM-VR-02")
            self.assertTrue(any("governs" in error for error in vr02.errors), vr02.errors)

    def test_mismatch_bidireccional_falla_cerrado(self) -> None:
        import shutil
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profiles = root / "core/framework/core/profiles"
            ontology = root / "core/foundation/ontology"
            profiles.mkdir(parents=True)
            ontology.mkdir(parents=True)
            shutil.copy(
                ROOT / "core/foundation/ontology/EDAIOS_ONTOLOGY.md",
                ontology / "EDAIOS_ONTOLOGY.md",
            )
            source = json.loads(
                (ROOT / "core/framework/core/profiles/governance-grammar.json").read_text(
                    encoding="utf-8"
                )
            )
            solo_grammar = dict(source)
            solo_grammar["entities"] = list(source["entities"]) + ["Fantasma"]
            (profiles / "governance-grammar.json").write_text(
                json.dumps(solo_grammar), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "divergen"):
                self.kom.load_contracts(root)
            solo_ontologia = dict(source)
            solo_ontologia["entities"] = [
                item for item in source["entities"] if item != "Playbook"
            ]
            (profiles / "governance-grammar.json").write_text(
                json.dumps(solo_ontologia), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "divergen"):
                self.kom.load_contracts(root)

    def test_prosa_fantasma_e_historico_vivo_fallan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            foundation = root / "core/foundation"
            foundation.mkdir(parents=True)
            (foundation / "vivo.md").write_text("contenido\n", encoding="utf-8")
            self._fixture_ko(
                foundation / "fixture.md",
                "Standard",
                "\n**Deriva de:** `NO-EXISTE.md`\n"
                "\n**Deriva de:** `vivo.md` (histórico, genealogía anterior)\n",
            )
            objects = self.kom.scan_scope(foundation, "fixture.scope", core_scope=False)
            rules = self.kom.evaluate(root, objects, self.grammar, self.entities)
            prosa = next(rule for rule in rules if rule.id == "DERIVA-PROSA")
            self.assertTrue(
                any("NO-EXISTE.md" in error for error in prosa.errors), prosa.errors
            )
            self.assertTrue(
                any("archivo vivo" in error for error in prosa.errors), prosa.errors
            )

    def test_control_pointer_no_resoluble_falla(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "tools").mkdir()
            (root / "tools/x.py").write_text("", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests/y.py").write_text("", encoding="utf-8")
            source = root / "core/framework/modules/m1/src"
            source.mkdir(parents=True)
            (source / "mod.py").write_text("", encoding="utf-8")
            ok_rows = [
                {"id": "x", "implementation": "tools/x.py", "tests": "tests/y.py"},
                {"id": "m", "implementation": "mod:Thing", "tests": "tests"},
            ]
            self.conformance.validate_control_pointers(root, ok_rows)
            with self.assertRaisesRegex(
                self.conformance.ConformanceCheckError, "no resoluble"
            ):
                self.conformance.validate_control_pointers(
                    root,
                    [{"id": "kom", "implementation": "tools/x.py", "tests": "tests/nada.py"}],
                )
            with self.assertRaisesRegex(
                self.conformance.ConformanceCheckError, "no resoluble"
            ):
                self.conformance.validate_control_pointers(
                    root,
                    [{"id": "m2", "implementation": "modx:Thing", "tests": "tests/y.py"}],
                )


class OntologyConstraintsTests(unittest.TestCase):
    """Regresiones de specs/014: restricciones ontológicas ejecutables (ADR-0021)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.kom = load_module("test_kom_gate_014", "tools/validation/kom_gate.py")
        cls.grammar, cls.entities = cls.kom.load_contracts(ROOT)

    def _root_with_contracts(self) -> Path:
        import shutil
        tmp = Path(tempfile.mkdtemp(prefix="edaios-constraints-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for relative in (
            "core/foundation/ontology/EDAIOS_ONTOLOGY.md",
            "core/framework/core/profiles/governance-grammar.json",
            ".specify/gates.json",
        ):
            target = tmp / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / relative, target)
        return tmp

    def _write_grammar(self, root: Path, mutate) -> None:
        path = root / "core/framework/core/profiles/governance-grammar.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_enforcer_desconocido_falla_cerrado(self) -> None:
        root = self._root_with_contracts()

        def mutate(data):
            data["constraints"][0]["verificado_por"] = ["GATE-FANTASMA"]

        self._write_grammar(root, mutate)
        with self.assertRaisesRegex(ValueError, "divergen|no resoluble"):
            self.kom.load_contracts(root)

    def test_ambito_fuera_del_dominio_falla_cerrado(self) -> None:
        root = self._root_with_contracts()

        def mutate(data):
            data["constraints"][0]["aplica_a"] = ["EntidadInventada"]

        self._write_grammar(root, mutate)
        with self.assertRaisesRegex(ValueError, "divergen|fuera del dominio"):
            self.kom.load_contracts(root)

    def test_id_en_una_sola_fuente_falla_cerrado(self) -> None:
        root = self._root_with_contracts()

        def drop(data):
            data["constraints"] = data["constraints"][1:]

        self._write_grammar(root, drop)
        with self.assertRaisesRegex(ValueError, "constraints y Ontología divergen"):
            self.kom.load_contracts(root)
        root2 = self._root_with_contracts()

        def add(data):
            data["constraints"] = data["constraints"] + [
                {"id": "INV-099", "aplica_a": ["Core"], "verificado_por": ["KOM"]}
            ]

        self._write_grammar(root2, add)
        with self.assertRaisesRegex(ValueError, "constraints y Ontología divergen"):
            self.kom.load_contracts(root2)

    def test_gates_json_ausente_falla_cerrado(self) -> None:
        root = self._root_with_contracts()
        (root / ".specify/gates.json").unlink()
        with self.assertRaisesRegex(ValueError, "falta .specify/gates.json"):
            self.kom.load_contracts(root)

    def test_tipo_constraint_es_valido(self) -> None:
        self.assertIn("Constraint", self.entities)
        with tempfile.TemporaryDirectory() as temporary:
            scope = Path(temporary)
            (scope / ".git").mkdir()
            (scope / "constraint.md").write_text(
                "---\nid: KO-FIXTURE-CONSTRAINT\ntipo: Constraint\n"
                "titulo: Fixture\nversion: 1.0.0\nestado: Borrador\n"
                "autoridad: Consumer\nidioma: es\nowner: Fixture\n"
                "deriva_de: Foundation\n---\n\n# Fixture\n",
                encoding="utf-8",
            )
            mounted = self.kom.scan_scope(scope, "fixture.scope", core_scope=False)
            rules = self.kom.evaluate(ROOT, mounted, self.grammar, self.entities)
            vr02 = next(rule for rule in rules if rule.id == "KOM-VR-02")
            self.assertEqual(vr02.errors, [])

    def test_corpus_declara_ambitos_y_enforcement_reales(self) -> None:
        constraints = {row["id"]: row for row in self.grammar["constraints"]}
        self.assertGreaterEqual(len(constraints), 11)
        for row in constraints.values():
            self.assertTrue(set(row["aplica_a"]) <= self.entities, row)
            self.assertTrue(row["verificado_por"], row)


class AdversarialReviewTests(unittest.TestCase):
    """Regresiones de specs/015: contrato de findings, v3 y calidad de tests."""

    GATE = "tools/validation/spec_kit_gate.py"

    @classmethod
    def setUpClass(cls) -> None:
        cls.quality = load_module(
            "test_quality_check_015", "tools/validation/test_quality_check.py"
        )

    def _feature_root(self, findings: str | None, schema: str = "edaios.sdd.feature/v3") -> Path:
        import shutil
        tmp = Path(tempfile.mkdtemp(prefix="edaios-adversarial-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        (tmp / ".specify/memory").mkdir(parents=True)
        shutil.copy(ROOT / ".specify/memory/constitution.md", tmp / ".specify/memory/constitution.md")
        feature = tmp / "specs/900-fixture"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text(
            "---\nid: EDAIOS-FIXTURE-ADVERSARIAL\nestado: Cerrado\nfase: implemented\n"
            "dominio: core\ntramo_sensibilidad: T0\nowner: Fixture\n"
            "tipo_cambio: governance\ntrazas:\n  - ADR-0001\n"
            "spec_tipada: specs/900-fixture/feature.spec.yaml\nfuentes:\n  - spec.md\n"
            "value_ledger: \"N/A: fixture de regresion\"\n"
            "hipotesis_valor: fixture de regresion adversarial\n---\n\n# Fixture\n\n"
            "- **FR-001:** fixture.\n\n- **SC-001:** fixture.\n",
            encoding="utf-8",
        )
        (feature / "feature.spec.yaml").write_text(
            f"schema: {schema}\nid: EDAIOS-FIXTURE-ADVERSARIAL\n"
            "artifact: specs/900-fixture/spec.md\n",
            encoding="utf-8",
        )
        if findings is not None:
            (feature / "review").mkdir()
            (feature / "review/findings.md").write_text(findings, encoding="utf-8")
        return tmp

    def _gate_output(self, root: Path) -> str:
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, str(ROOT / self.GATE), str(root),
             "--feature", "specs/900-fixture", "--profile", "consumer-release"],
            capture_output=True, text=True, check=False,
        )
        return result.stdout + result.stderr

    def test_v3_estructural_sin_findings_falla(self) -> None:
        output = self._gate_output(self._feature_root(findings=None))
        self.assertIn("revision adversarial materializada", output)
        self.assertRegex(output, r"\[FAIL\].*revision adversarial materializada")

    def test_v2_sin_findings_no_exige_revision(self) -> None:
        output = self._gate_output(
            self._feature_root(findings=None, schema="edaios.sdd.feature/v2")
        )
        self.assertNotIn("revision adversarial materializada", output)

    def test_fila_no_conforme_y_critical_abierto_fallan(self) -> None:
        malformed = (
            "# Revision\n\n"
            "| Id | Lente | Severidad | Estado | Hallazgo | Refs |\n"
            "|---|---|---|---|---|---|\n"
            "| RA-001 | refutador | GRAVISIMA | abierto | x | spec.md |\n"
        )
        output = self._gate_output(self._feature_root(findings=malformed))
        self.assertRegex(output, r"\[FAIL\].*filas de hallazgo conformes.*RA-001")
        blocking = (
            "# Revision\n\n"
            "| Id | Lente | Severidad | Estado | Hallazgo | Refs |\n"
            "|---|---|---|---|---|---|\n"
            "| RA-001 | lente-riesgo | CRITICAL | abierto | x | spec.md |\n"
        )
        output = self._gate_output(self._feature_root(findings=blocking))
        self.assertRegex(output, r"\[FAIL\].*sin CRITICAL/HIGH abiertos.*RA-001")

    def test_sin_hallazgos_justificado_pasa_el_contrato(self) -> None:
        clean = "# Revision\n\nSin hallazgos: se reviso spec, plan y diff sin defectos defendibles.\n"
        output = self._gate_output(self._feature_root(findings=clean))
        self.assertNotRegex(output, r"\[FAIL\].*findings")
        self.assertNotRegex(output, r"\[FAIL\].*hallazgo")

    def test_checker_de_calidad_falla_cerrado(self) -> None:
        tmp = Path(tempfile.mkdtemp(prefix="edaios-quality-"))
        self.addCleanup(__import__("shutil").rmtree, tmp, ignore_errors=True)
        bad = tmp / "test_malos.py"
        bad.write_text(
            "import unittest\n\n\nclass Malos(unittest.TestCase):\n"
            "    def test_sin_asserts(self):\n        valor = 1 + 1\n\n"
            "    def test_tautologico(self):\n        valor = 3\n        self.assertEqual(valor, valor)\n\n"
            "    def test_constante(self):\n        self.assertTrue(True)\n",
            encoding="utf-8",
        )
        errors: list[str] = []
        checked = self.quality.check_file(bad, errors)
        self.assertEqual(checked, 3)
        self.assertEqual(len(errors), 3, errors)

    def test_namespace_de_agentes_sin_fuentes_falla_cerrado(self) -> None:
        import os as _os
        import shutil
        import subprocess
        import sys
        tmp = Path(tempfile.mkdtemp(prefix="edaios-sync-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        shutil.copytree(ROOT / ".specify/commands", tmp / ".specify/commands")
        (tmp / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        env = dict(_os.environ, EDAIOS_REPO_ROOT=str(tmp))
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/publishing/sync_spec_kit_integrations.py"), "--check"],
            capture_output=True, text=True, check=False, env=env,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("no hay fuentes de agentes revisores", result.stdout + result.stderr)
