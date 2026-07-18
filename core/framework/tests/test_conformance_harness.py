from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from importlib.resources import files
from pathlib import Path

from edaios_conformance import (
    AttachmentError,
    PolicyWeakeningError,
    ProfileRegistry,
    SchemaRegistry,
    ValidationError,
    diff_policy,
    initialize_attachment,
    prepare_upgrade,
    require_monotonic_policy,
    rollback_attachment,
    validate_attachment,
)
from edaios_core.knowledge import KnowledgeMount, corpus_digest
from edaios_core_harness import (
    ContractError,
    CoreHarness,
    ReceiptError,
    create_approval_receipt,
    create_evidence_receipt,
    verify_evidence_receipt,
)
from edaios_core_harness.cli import main as cli_main


NOW = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)


class SchemaAndProfileTests(unittest.TestCase):
    def test_every_schema_has_valid_and_invalid_contract_example(self):
        example_root = files("edaios_conformance").joinpath("resources/examples")
        valid = json.loads(example_root.joinpath("t0.valid.json").read_text())
        invalid = json.loads(example_root.joinpath("t0.invalid.json").read_text())
        registry = SchemaRegistry()
        self.assertEqual(set(registry.names()), set(valid))
        self.assertEqual(set(valid), set(invalid))
        for name in registry.names():
            with self.subTest(schema=name, case="valid"):
                self.assertEqual(registry.validate(name, valid[name]), valid[name])
            with self.subTest(schema=name, case="invalid"):
                with self.assertRaises(ValidationError):
                    registry.validate(name, invalid[name])

    def test_public_boundary_patterns_are_explicitly_anchored(self):
        schema_root = files("edaios_conformance").joinpath("resources/schemas")

        def patterns(value):
            if isinstance(value, dict):
                if "pattern" in value:
                    yield value["pattern"]
                for child in value.values():
                    yield from patterns(child)
            elif isinstance(value, list):
                for child in value:
                    yield from patterns(child)

        for resource in schema_root.iterdir():
            filename = resource.name
            if not filename.endswith(".json"):
                continue
            with self.subTest(schema=filename):
                schema = json.loads(resource.read_text())
                for pattern in patterns(schema):
                    self.assertTrue(pattern.startswith("^"), pattern)
                    self.assertTrue(pattern.endswith("$"), pattern)

    def test_profile_inheritance_is_cumulative_and_cycle_fails(self):
        registry = ProfileRegistry()
        report = registry.validate_registry()
        self.assertEqual(
            report["resolved"]["federation"]["chain"],
            ["core-release", "initiative-adoption", "federation"],
        )
        core_controls = set(report["resolved"]["core-release"]["controls"])
        self.assertTrue(core_controls <= set(report["resolved"]["federation"]["controls"]))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.profile.json").write_text(json.dumps({
                "schema": "edaios.conformance-profile/v1", "id": "a",
                "version": "1.0.0", "parent": "b", "controls": ["x"],
            }))
            (root / "b.profile.json").write_text(json.dumps({
                "schema": "edaios.conformance-profile/v1", "id": "b",
                "version": "1.0.0", "parent": "a", "controls": ["y"],
            }))
            with self.assertRaises(ValueError):
                ProfileRegistry(root).resolve("a")

    def test_policy_diff_rejects_weakening(self):
        current = {"id": "current", "controls": [{"id": "traceability", "level": "required"}]}
        stronger = {"id": "stronger", "controls": [
            {"id": "traceability", "level": "required"},
            {"id": "approval", "level": "required"},
        ]}
        weaker = {"id": "weaker", "controls": [{"id": "traceability", "level": "advisory"}]}
        self.assertTrue(require_monotonic_policy(current, stronger)["applicable"])
        self.assertFalse(diff_policy(current, weaker)["applicable"])
        with self.assertRaises(PolicyWeakeningError):
            require_monotonic_policy(current, weaker)


class AttachmentTests(unittest.TestCase):
    def test_init_validate_and_safe_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("initiative\n", encoding="utf-8")
            created = initialize_attachment(
                root,
                initiative_id="demo-t0",
                namespace="demo.t0",
                owner="OWNER-DEMO",
                value_owner="VALUE-DEMO",
            )
            self.assertEqual(created["status"], "initialized")
            report = validate_attachment(root)
            self.assertEqual(report["status"], "valid")
            self.assertFalse(report["adopted"])
            self.assertFalse(rollback_attachment(root)["applied"])
            self.assertTrue(rollback_attachment(root, apply=True)["applied"])
            self.assertFalse((root / "edaios.initiative.json").exists())

    def test_init_does_not_overwrite_and_rollback_detects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_attachment(
                root,
                initiative_id="demo-t0",
                namespace="demo.t0",
                owner="OWNER-DEMO",
                value_owner="VALUE-DEMO",
            )
            with self.assertRaises(AttachmentError):
                initialize_attachment(
                    root,
                    initiative_id="demo-t0",
                    namespace="demo.t0",
                    owner="OWNER-DEMO",
                    value_owner="VALUE-DEMO",
                )
            manifest = root / "edaios.initiative.json"
            manifest.write_text(manifest.read_text() + " ", encoding="utf-8")
            with self.assertRaises(AttachmentError):
                rollback_attachment(root, apply=True)

    def test_validate_rejects_symlinked_authority_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_attachment(
                root,
                initiative_id="demo-t0",
                namespace="demo.t0",
                owner="OWNER-DEMO",
                value_owner="VALUE-DEMO",
            )
            authority = root / ".edaios/authority-registry.json"
            outside = root / "outside-authority.json"
            authority.replace(outside)
            try:
                authority.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks no disponibles: {exc}")
            with self.assertRaises(AttachmentError):
                validate_attachment(root)


class HarnessContractTests(unittest.TestCase):
    def setUp(self):
        self.harness = CoreHarness()

    def test_registry_has_twelve_honestly_enforced_harnesses(self):
        report = self.harness.validate()
        self.assertEqual(report["harnesses"], 12)
        self.assertEqual(report["enforced"], 12)

    def test_sdd_orchestrator_positive_and_negative(self):
        self.assertEqual(self.harness.next_phase(["constitution"])["next_phase"], "specify")
        with self.assertRaises(ContractError):
            self.harness.next_phase(["specify"])

    def test_request_router_positive_and_negative(self):
        self.assertEqual(
            self.harness.route_request(intent="decidir frontera", declared_kind="adr")["route"],
            "governance-adr",
        )
        with self.assertRaises(ContractError):
            self.harness.route_request(intent="", declared_kind="guess")

    def test_phase_dag_positive_and_negative(self):
        self.assertEqual(len(self.harness.validate_phase_dag()["order"]), 8)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("harness-registry.json", "execution-modes.json", "phase-dag.json"):
                source = self.harness.resource_root / name
                (root / name).write_bytes(source.read_bytes())
            dag = json.loads((root / "phase-dag.json").read_text())
            dag["phases"][0]["dependencies"] = ["implement"]
            (root / "phase-dag.json").write_text(json.dumps(dag))
            with self.assertRaises(ValueError):
                CoreHarness(root).validate_phase_dag()

    def test_strict_tdd_positive_and_negative(self):
        stages = ["red", "green", "triangulate", "refactor"]
        self.assertTrue(self.harness.strict_tdd(stages)["tests_first"])
        with self.assertRaises(ContractError):
            self.harness.strict_tdd(["green", "refactor"])

    def test_artifact_store_positive_and_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "artifact.txt").write_text("bytes", encoding="utf-8")
            receipt = self.harness.store_artifact(root, artifact="artifact.txt", source="SPEC-0001")
            self.assertTrue(receipt.is_file())
            with self.assertRaises(ContractError):
                self.harness.store_artifact(root, artifact="../outside", source="SPEC-0001")

    def test_result_contract_positive_and_negative(self):
        self.assertEqual(self.harness.normalize_result(
            status="passed", summary="ok", exit_code=0, evidence=["test"], claim_boundary="local",
        )["status"], "passed")
        with self.assertRaises(ContractError):
            self.harness.normalize_result(
                status="passed", summary="ok", exit_code=1, evidence=["test"], claim_boundary="local",
            )

    def test_memory_port_positive_and_negative(self):
        self.assertTrue(self.harness.memory_port(
            tier="durable", record={"git_path": "evidence/result.json"},
        )["authoritative"])
        local = self.harness.memory_port(
            tier="local", record={"subject": "working context"},
        )
        self.assertFalse(local["authoritative"])
        self.assertEqual(local["channel"], "local-working")
        self.assertIn("promote", local["forbidden_operations"])
        with self.assertRaises(ContractError):
            self.harness.memory_port(tier="durable", record={"value": "RAM"})
        with self.assertRaises(ContractError):
            self.harness.memory_port(
                tier="local", record={"value": "RAM", "authoritative": True}
            )

    def test_permission_guard_positive_and_negative(self):
        authority = {
            "schema": "edaios.authority-registry/v1", "initiative": "demo-t0", "version": "1.0.0",
            "actors": [
                {
                    "actor_id": "OWNER", "type": "human", "roles": ["initiative-owner"],
                    "capabilities": ["approve", "delegate", "validate"], "active": True,
                },
                {
                    "actor_id": "AGENT", "type": "agent", "roles": ["executor"],
                    "capabilities": ["read"], "active": True,
                },
            ],
        }
        self.assertEqual(self.harness.permission_guard(
            request={"actor_id": "OWNER", "capability": "approve", "scope": "specs/demo"},
            authority_registry=authority,
        )["basis"], "direct-authority")
        grant = {
            "schema": "edaios.delegation-grant/v1", "id": "DLG-0001", "initiative": "demo-t0",
            "grantor_actor_id": "OWNER", "grantee_actor_id": "AGENT", "capabilities": ["validate"],
            "scope": ["specs/demo"], "valid_from": "2026-07-15T00:00:00Z",
            "valid_until": "2026-07-16T00:00:00Z", "revoked": False,
        }
        self.assertEqual(self.harness.permission_guard(
            request={"actor_id": "AGENT", "capability": "validate", "scope": "specs/demo"},
            authority_registry=authority, grants=[grant], now="2026-07-15T12:00:00Z",
        )["basis"], "DLG-0001")
        with self.assertRaises(ContractError):
            self.harness.permission_guard(
                request={"actor_id": "AGENT", "capability": "approve", "scope": "specs/demo"},
                authority_registry=authority, grants=[grant], now="2026-07-17T12:00:00Z",
            )

    def test_backup_rollback_positive_and_negative(self):
        plan = {"target_ref": "aaaaaaa", "steps": ["restore"], "verification": "tests", "owner": "OWNER"}
        self.assertEqual(self.harness.backup_rollback(plan)["status"], "ready")
        with self.assertRaises(ContractError):
            self.harness.backup_rollback({"target_ref": "aaaaaaa"})

    def test_telemetry_positive_and_negative(self):
        event = {
            "event_name": "gate.completed", "observed_at": "2026-07-15T12:00:00Z",
            "source": "local-test", "attributes": {"status": "passed"},
        }
        self.assertIn("not an outcome", self.harness.telemetry(event)["claim_boundary"])
        with self.assertRaises(ContractError):
            self.harness.telemetry({**event, "outcome": "invented"})

    def test_command_wrapper_positive_and_negative(self):
        result = self.harness.command_wrapper(command=["python", "-V"], exit_code=7, stderr=b"error")
        self.assertEqual(result["exit_code"], 7)
        self.assertFalse(result["executed_by_core"])
        with self.assertRaises(ContractError):
            self.harness.command_wrapper(command=[], exit_code=0)


class ReceiptAndHumanAcceptanceTests(unittest.TestCase):
    def _create_evidence(self, root: Path, *, approval_required: bool = False, when: datetime = NOW) -> Path:
        (root / "evidence").mkdir(exist_ok=True)
        (root / "evidence/result.txt").write_text("green\n", encoding="utf-8")
        policy = {
            "schema": "edaios.policy-profile/v1", "id": "demo-policy", "version": "1.0.0",
            "parent": "demo", "controls": [{"id": "human-authority", "level": "required"}],
            "approval_required": approval_required, "max_receipt_age_seconds": 86400,
            "allowed_sensitivity": ["T0"], "exceptions_allowed": False,
        }
        return create_evidence_receipt(
            root,
            initiative="demo-t0",
            feature_run="feature/demo/run-1",
            actor_id="AGENT",
            actor_type="agent",
            core_version="2.0.0",
            policy=policy,
            base_commit="aaaaaaa",
            head_commit="bbbbbbb",
            evidence=["evidence/result.txt"],
            sensitivity="T0",
            exit_code=0,
            verdict="passed",
            claim_boundary="local tests only",
            rollback={"target_ref": "aaaaaaa", "steps": ["restore"], "verification": "rerun tests"},
            approval_required=approval_required,
            approval_roles=["initiative-owner"] if approval_required else [],
            recorded_at=when,
        )

    def test_evidence_receipt_detects_tampering_head_and_staleness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = self._create_evidence(root)
            expected_policy = {
                "schema": "edaios.policy-profile/v1", "id": "demo-policy", "version": "1.0.0",
                "parent": "demo", "controls": [{"id": "human-authority", "level": "required"}],
                "approval_required": False, "max_receipt_age_seconds": 86400,
                "allowed_sensitivity": ["T0"], "exceptions_allowed": False,
            }
            self.assertEqual(verify_evidence_receipt(
                root, receipt, expected_head="bbbbbbb", expected_base="aaaaaaa",
                expected_policy=expected_policy, max_age_seconds=60, now=NOW,
            )["status"], "valid")
            with self.assertRaises(ReceiptError):
                verify_evidence_receipt(root, receipt, expected_head="ccccccc")
            with self.assertRaises(ReceiptError):
                verify_evidence_receipt(root, receipt, expected_policy={
                    **expected_policy, "id": "other",
                })
            with self.assertRaises(ReceiptError):
                verify_evidence_receipt(root, receipt, max_age_seconds=60, now=NOW + timedelta(seconds=61))
            (root / "evidence/result.txt").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(ReceiptError):
                verify_evidence_receipt(root, receipt)

    def test_human_acceptance_is_separate_and_human_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = self._create_evidence(root, approval_required=True)
            receipt_data = json.loads(receipt.read_text())
            evidence_digest = receipt_data["integrity"]["payload_sha256"]
            with self.assertRaises(ReceiptError):
                verify_evidence_receipt(root, receipt)
            approval = create_approval_receipt(
                root,
                initiative="demo-t0",
                feature_run="feature/demo/run-1",
                actor_id="OWNER",
                authority_role="initiative-owner",
                evidence_receipt_digest=evidence_digest,
                verdict="accepted",
                statement="Aceptacion humana local del alcance observado.",
                approved_at=NOW,
            )
            authority = {
                "schema": "edaios.authority-registry/v1", "initiative": "demo-t0", "version": "1.0.0",
                "actors": [{
                    "actor_id": "OWNER", "type": "human", "roles": ["initiative-owner"],
                    "capabilities": ["approve"], "active": True,
                }],
            }
            report = verify_evidence_receipt(
                root, receipt, approval=approval, approval_authority=authority,
            )
            self.assertEqual(report["approval"]["actor_id"], "OWNER")
            self.assertEqual(
                CoreHarness().human_acceptance(
                    approval,
                    evidence_receipt_digest=evidence_digest,
                    allowed_roles=["initiative-owner"],
                    authority_registry=authority,
                )["status"],
                "valid",
            )
            tampered = json.loads(approval.read_text())
            tampered["actor"]["type"] = "agent"
            with self.assertRaises((ReceiptError, ValidationError)):
                CoreHarness().human_acceptance(
                    tampered,
                    evidence_receipt_digest=evidence_digest,
                    allowed_roles=["initiative-owner"],
                    authority_registry=authority,
                )


class CliTests(unittest.TestCase):
    def _call(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli_main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_init_adopt_validate_explain_upgrade_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, _, _ = self._call([
                "init", "--workspace", tmp, "--id", "demo-t0", "--namespace", "demo.t0",
                "--owner", "OWNER", "--value-owner", "VALUE",
            ])
            self.assertEqual(code, 0)
            self.assertEqual(self._call(["adopt", "--workspace", tmp])[0], 0)
            self.assertEqual(self._call([
                "validate", "--profile", "initiative-adoption", "--workspace", tmp,
            ])[0], 0)
            self.assertEqual(self._call(["explain", "--code", "EVIDENCE_TAMPERED"])[0], 0)

            current_path = root / ".edaios/policies/initiative-policy.json"
            proposed = json.loads(current_path.read_text())
            proposed["id"] = "demo-policy-next"
            proposed["controls"].append({"id": "rollback", "level": "required"})
            proposed_path = root / "proposed-policy.json"
            proposed_path.write_text(json.dumps(proposed))
            output = root / "upgrade-plan.json"
            self.assertEqual(self._call([
                "upgrade", "--manifest", str(root / "edaios.initiative.json"),
                "--current-policy", str(current_path), "--target-policy", str(proposed_path),
                "--target-core", "3.0.0", "--output", str(output),
            ])[0], 0)
            self.assertTrue(output.is_file())
            self.assertEqual(self._call(["rollback", "--workspace", tmp])[0], 0)
            self.assertEqual(self._call(["rollback", "--workspace", tmp, "--apply"])[0], 0)

    def test_cli_diff_policy_fails_closed_on_weakening(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "current.json"
            proposed = root / "proposed.json"
            current.write_text(json.dumps({"id": "a", "controls": [{"id": "x", "level": "required"}]}))
            proposed.write_text(json.dumps({"id": "b", "controls": []}))
            code, stdout, stderr = self._call([
                "diff-policy", "--current", str(current), "--proposed", str(proposed),
            ])
            self.assertEqual(code, 2)
            self.assertIn('"applicable": false', stdout)

    def test_cli_federation_requires_explicit_mounts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mounts = []
            attachments = []
            for suffix in ("one", "two"):
                attachment = root / suffix
                attachment.mkdir()
                (attachment / "README.md").write_text(f"{suffix}\n")
                owner = f"OWNER-{suffix.upper()}"
                initialize_attachment(
                    attachment,
                    initiative_id=f"demo-{suffix}",
                    namespace=f"demo.{suffix}",
                    owner=owner,
                    value_owner=f"VALUE-{suffix.upper()}",
                )
                manifest_path = attachment / "edaios.initiative.json"
                manifest = json.loads(manifest_path.read_text())
                manifest["conformance_profile"] = "federation"
                manifest_path.write_text(json.dumps(manifest))
                corpus = attachment / "corpus"
                corpus.mkdir()
                (corpus / "ko.md").write_text("\n".join([
                    "---", f"id: KO-{suffix.upper()}", "tipo: Principle",
                    f"titulo: {suffix}", "version: 1.0.0",
                    "estado: Ratificado", "autoridad: Consumer",
                    "idioma: es", f"owner: {owner}", "deriva_de: NONE",
                    "---", "", suffix,
                ]))
                if suffix == "one":
                    graph = corpus / "knowledge-graph"
                    graph.mkdir()
                    (graph / "type.json").write_text(json.dumps({
                        "kind": "entity_type", "name": "Service",
                    }))
                    (graph / "service.json").write_text(json.dumps({
                        "kind": "entity", "id": "service", "type": "Service",
                    }))
                authority = attachment / ".edaios/authority-registry.json"
                mounts.append({
                    "namespace": f"demo.{suffix}",
                    "path": str(corpus),
                    "authorized_root": str(attachment),
                    "authority_layer": "Consumer",
                    "owner_actor_id": owner,
                    "attachment": str(attachment),
                    "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
                    "authority_registry_sha256": sha256(authority.read_bytes()).hexdigest(),
                    "corpus_sha256": corpus_digest(
                        KnowledgeMount.from_value(
                            {
                                "namespace": f"demo.{suffix}",
                                "path": corpus,
                                "authorized_root": attachment,
                                "authority_layer": "Consumer",
                                "owner_actor_id": owner,
                                "allowed_owner_actor_ids": [owner],
                                "corpus_sha256": None,
                            }
                        )
                    ),
                })
                attachments.append(attachment)
            self.assertEqual(self._call([
                "validate", "--profile", "federation",
                "--workspace", str(attachments[0]),
            ])[0], 2)
            mounts_path = root / "mounts.json"
            mounts_path.write_text(json.dumps({
                "schema": "edaios.federation-mounts/v1",
                "mounts": mounts,
            }))
            one_mount = root / "one-mount.json"
            one_mount.write_text(json.dumps({
                "schema": "edaios.federation-mounts/v1",
                "mounts": mounts[:1],
            }))
            self.assertEqual(self._call([
                "validate", "--profile", "federation",
                "--workspace", str(attachments[0]),
                "--mounts", str(one_mount),
            ])[0], 2)
            tampered = json.loads(json.dumps(mounts))
            tampered[0]["manifest_sha256"] = "f" * 64
            tampered_path = root / "tampered-mounts.json"
            tampered_path.write_text(json.dumps({
                "schema": "edaios.federation-mounts/v1",
                "mounts": tampered,
            }))
            self.assertEqual(self._call([
                "validate", "--profile", "federation",
                "--workspace", str(attachments[0]),
                "--mounts", str(tampered_path),
            ])[0], 2)
            escaped_root = json.loads(json.dumps(mounts))
            escaped_root[0]["authorized_root"] = str(root)
            escaped_root_path = root / "escaped-root-mounts.json"
            escaped_root_path.write_text(json.dumps({
                "schema": "edaios.federation-mounts/v1",
                "mounts": escaped_root,
            }))
            self.assertEqual(self._call([
                "validate", "--profile", "federation",
                "--workspace", str(attachments[0]),
                "--mounts", str(escaped_root_path),
            ])[0], 2)
            code, stdout, stderr = self._call([
                "validate", "--profile", "federation",
                "--workspace", str(attachments[0]),
                "--mounts", str(mounts_path),
            ])
            self.assertEqual(code, 0, stderr)
            self.assertIn('"derived": true', stdout)
            self.assertIn('"mounts": 2', stdout)
            self.assertIn('"graph_nodes": 1', stdout)

    def test_cli_evidence_and_approval_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_attachment(
                root, initiative_id="demo-t0", namespace="demo.t0",
                owner="OWNER", value_owner="VALUE",
            )
            (root / "evidence").mkdir()
            (root / "evidence/result.txt").write_text("green\n")
            rollback = root / "rollback.json"
            rollback.write_text(json.dumps({
                "target_ref": "aaaaaaa", "steps": ["restore"],
                "verification": "rerun tests",
            }))
            code, stdout, _ = self._call([
                "evidence", "create", "--workspace", tmp,
                "--initiative", "demo-t0", "--feature-run", "feature/demo/run-1",
                "--actor-id", "AGENT", "--actor-type", "agent",
                "--policy", str(root / ".edaios/policies/initiative-policy.json"),
                "--base-commit", "aaaaaaa", "--head-commit", "bbbbbbb",
                "--file", "evidence/result.txt", "--sensitivity", "T0",
                "--exit-code", "0", "--verdict", "passed",
                "--claim-boundary", "local only", "--rollback-plan", str(rollback),
                "--approval-required", "--approval-role", "initiative-owner",
            ])
            self.assertEqual(code, 0)
            evidence_path = Path(json.loads(stdout)["receipt"])
            evidence_digest = json.loads(evidence_path.read_text())["integrity"]["payload_sha256"]
            code, stdout, _ = self._call([
                "approval", "create", "--workspace", tmp,
                "--initiative", "demo-t0", "--feature-run", "feature/demo/run-1",
                "--actor-id", "OWNER", "--authority-role", "initiative-owner",
                "--evidence-digest", evidence_digest, "--verdict", "accepted",
                "--statement", "Aceptacion humana local.",
            ])
            self.assertEqual(code, 0)
            approval_path = Path(json.loads(stdout)["receipt"])
            code, stdout, _ = self._call([
                "evidence", "verify", "--workspace", tmp,
                "--receipt", str(evidence_path), "--expected-base", "aaaaaaa",
                "--expected-head", "bbbbbbb",
                "--policy", str(root / ".edaios/policies/initiative-policy.json"),
                "--approval", str(approval_path),
                "--authority-registry", str(root / ".edaios/authority-registry.json"),
            ])
            self.assertEqual(code, 0)
            self.assertIn('"authority": "verified-against-local-registry"', stdout)


if __name__ == "__main__":
    unittest.main()
