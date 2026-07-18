"""Contrato del candidato reproducible y del sello final fail-closed."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
GIT = shutil.which("git")


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prepare = load_module(
    "prepare_core_release_test", "tools/publishing/prepare_core_release.py"
)
seal = load_module(
    "core_release_seal_check_test", "tools/validation/core_release_seal_check.py"
)

from edaios_core_harness import (  # noqa: E402
    create_approval_receipt,
    create_evidence_receipt,
)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        [GIT, "-C", str(root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def initialize(root: Path) -> None:
    root.mkdir()
    subprocess.run([GIT, "init", "-q", str(root)], check=True)
    git(root, "config", "user.email", "core-release-test@edaios.local")
    git(root, "config", "user.name", "EDAIOS Core Release Test")
    git(root, "remote", "add", "origin", "https://example.test/edaios.git")
    (root / "VERSION").write_text("3.0.0\n", encoding="utf-8")
    (root / "source.txt").write_text("baseline\n", encoding="utf-8")
    gates = root / ".specify/gates.json"
    gates.parent.mkdir(parents=True)
    gates.write_text(
        json.dumps(
            {
                "schema": "edaios.gates/v1",
                "gates": [
                    {"id": "EDAIOS-CI", "scope": "ci", "command": "true"}
                ],
            }
        ),
        encoding="utf-8",
    )
    release = root / prepare.RELEASE_POLICY_RELATIVE.parent
    release.mkdir(parents=True)
    policy = {
        "schema": "edaios.policy-profile/v1",
        "id": "core-release-policy",
        "version": "3.0.0",
        "parent": "core-release",
        "controls": [{"id": "release-seal", "level": "required"}],
        "approval_required": True,
        "max_receipt_age_seconds": 86400,
        "allowed_sensitivity": ["T0"],
        "exceptions_allowed": False,
    }
    authority = {
        "schema": "edaios.authority-registry/v1",
        "initiative": "core-release",
        "version": "3.0.0",
        "actors": [
            {
                "actor_id": "HUMAN-TEST",
                "type": "human",
                "roles": ["principal-architect"],
                "capabilities": ["approve"],
                "active": True,
            },
            {
                "actor_id": "RELEASE-BOT",
                "type": "service",
                "roles": ["release-observer"],
                "capabilities": ["release:observe"],
                "active": True,
            },
        ],
    }
    target = {
        "schema": "edaios.git-cutover-target/v1",
        "status": "proposed",
        "component": "edaios-core",
        "version": "3.0.0",
        "repository": "example.test/edaios",
        "canonical_branch": "main",
        "required_checks": ["EDAIOS-CI"],
        "provider_evidence_kinds": [
            "branch-protection",
            "default-branch",
            "git-refs",
            "required-checks",
        ],
        "attestation_publication": {
            "required": True,
            "allowed_kinds": ["release-asset"],
        },
    }
    for relative, payload in (
        (prepare.RELEASE_POLICY_RELATIVE, policy),
        (prepare.RELEASE_AUTHORITY_RELATIVE, authority),
        (prepare.CUTOVER_TARGET_RELATIVE, target),
    ):
        (root / relative).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "baseline")


def write_release_state(
    root: Path,
    *,
    version: str | None = None,
    active_candidate: dict | None = None,
) -> tuple[Path, dict]:
    adr = root / "governance/ADR-0013-portable-single-root-genealogy.md"
    adr.parent.mkdir(parents=True, exist_ok=True)
    adr.write_text("# ADR-0013\n\n**Estado:** Aceptado\n", encoding="utf-8")
    payload = {
        "schema": "edaios.core-release-state/v2",
        "component": "edaios-core",
        "version": version or (root / "VERSION").read_text(encoding="utf-8").strip(),
        "status": "candidate" if active_candidate is not None else "baseline",
        "genealogy": {
            "kind": "single-root",
            "root_derivation": "unique-reachable-root",
            "canonical_branch": "main",
        },
        "active_candidate": active_candidate,
        "publication": "not-claimed",
        "governing_adr": "ADR-0013",
        "claim_boundary": (
            "Fixture de raíz derivada; no afirma ancla externa, tag ni producción."
        ),
    }
    path = root / seal.RELEASE_STATE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path, payload


def canonical_digest(value: object) -> str:
    content = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def fake_artifacts(_root: Path, version: str) -> dict:
    rows = [
        {
            "kind": kind,
            "name": f"{kind}-{version}",
            "sha256": hashlib.sha256(kind.encode()).hexdigest(),
            "size": len(kind),
        }
        for kind in (
            "core-export",
            "core-export-checksum",
            "provenance",
            "sbom",
            "wheel",
            "wheel-checksum",
        )
    ]
    return {
        "schema": "edaios.release-artifacts/v1",
        "digest": canonical_digest(rows),
        "items": rows,
    }


def add_integrity(payload: dict, prefix: str) -> dict:
    identity = dict(payload)
    payload["receipt_id"] = f"{prefix}-{canonical_digest(identity)[:12]}"
    payload["integrity"] = {
        "algorithm": "SHA-256",
        "payload_sha256": canonical_digest(payload),
        "claim": "local-integrity-only; not identity or non-repudiation",
    }
    return payload


def write_verified_receipts(
    root: Path,
    directory: Path,
    *,
    version: str,
    base: str,
    head: str,
    evidence_paths: list[str] | None = None,
    recorded_at: datetime | None = None,
    approved_at: datetime | None = None,
) -> tuple[Path, Path, Path, Path, Path]:
    directory.mkdir()
    policy_path = root / prepare.RELEASE_POLICY_RELATIVE
    authority_path = root / prepare.RELEASE_AUTHORITY_RELATIVE
    target_path = root / prepare.CUTOVER_TARGET_RELATIVE
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    observed = recorded_at or datetime.now(timezone.utc)
    generated_evidence = create_evidence_receipt(
        root,
        initiative="core-release",
        feature_run="feature/006/run-final",
        actor_id="CI-TEST",
        actor_type="service",
        core_version=version,
        policy=policy,
        base_commit=base,
        head_commit=head,
        evidence=evidence_paths
        or [
            "source.txt",
            prepare.RELEASE_POLICY_RELATIVE.as_posix(),
            prepare.RELEASE_AUTHORITY_RELATIVE.as_posix(),
            prepare.CUTOVER_TARGET_RELATIVE.as_posix(),
        ],
        sensitivity="T0",
        exit_code=0,
        verdict="passed",
        claim_boundary="fixture efimera; no afirma cutover remoto",
        rollback={
            "target_ref": base,
            "steps": ["restore"],
            "verification": "rerun",
        },
        approval_required=True,
        approval_roles=["principal-architect"],
        recorded_at=observed,
    )
    evidence_payload = json.loads(generated_evidence.read_text(encoding="utf-8"))
    generated_approval = create_approval_receipt(
        root,
        initiative="core-release",
        feature_run="feature/006/run-final",
        actor_id="HUMAN-TEST",
        authority_role="principal-architect",
        evidence_receipt_digest=evidence_payload["integrity"]["payload_sha256"],
        verdict="accepted",
        statement="fixture efimera de aprobacion local",
        approved_at=approved_at or observed,
    )
    evidence_path = directory / "evidence.json"
    approval_path = directory / "approval.json"
    shutil.copyfile(generated_evidence, evidence_path)
    shutil.copyfile(generated_approval, approval_path)
    shutil.rmtree(root / ".edaios")
    return evidence_path, approval_path, policy_path, authority_path, target_path


def write_cutover_receipt(
    path: Path,
    *,
    version: str,
    head: str,
    tree: str,
    evidence_receipt: Path,
    approval_receipt: Path,
    remote_head: str | None = None,
    observed_at: datetime | None = None,
    checks: list[str] | None = None,
    provider_kinds: list[str] | None = None,
) -> Path:
    evidence_payload = json.loads(evidence_receipt.read_text(encoding="utf-8"))
    approval_payload = json.loads(approval_receipt.read_text(encoding="utf-8"))
    kinds = provider_kinds or [
        "branch-protection",
        "default-branch",
        "git-refs",
        "required-checks",
    ]
    payload = add_integrity(
        {
            "schema": seal.CUTOVER_SCHEMA,
            "repository": "example.test/edaios",
            "canonical_branch": "main",
            "version": version,
            "commit": head,
            "tree": tree,
            "tag": f"v{version}",
            "remote_head": remote_head or head,
            "remote_tag_target": head,
            "default_branch": "main",
            "default_branch_head": head,
            "required_checks": [
                {"id": check, "status": "passed"}
                for check in (checks or ["EDAIOS-CI"])
            ],
            "branch_protection": {
                "observed": True,
                "force_push_allowed": False,
            },
            "legacy_history_merged": False,
            "provider_evidence": [
                {
                    "kind": kind,
                    "uri": f"https://example.test/evidence/{kind}.json",
                    "sha256": hashlib.sha256(kind.encode()).hexdigest(),
                    "size": len(kind),
                }
                for kind in kinds
            ],
            "attestation_publication": {
                "kind": "release-asset",
                "uri": "https://example.test/releases/v3.0.0/attestations.json",
                "sha256": hashlib.sha256(b"attestation").hexdigest(),
                "size": len("attestation"),
                "subjects": [
                    {
                        "kind": "approval-receipt",
                        "receipt_id": approval_payload["receipt_id"],
                        "sha256": approval_payload["integrity"]["payload_sha256"],
                    },
                    {
                        "kind": "evidence-receipt",
                        "receipt_id": evidence_payload["receipt_id"],
                        "sha256": evidence_payload["integrity"]["payload_sha256"],
                    },
                ],
            },
            "observed_at": (observed_at or datetime.now(timezone.utc)).isoformat().replace(
                "+00:00", "Z"
            ),
            "observer": {"id": "RELEASE-BOT", "type": "service"},
            "claim_boundary": seal.CUTOVER_CLAIM,
        },
        "CUT",
    )
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


@unittest.skipUnless(GIT, "git no disponible")
class CoreReleaseCandidateTests(unittest.TestCase):
    def test_release_state_can_live_in_the_only_root_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()
            subprocess.run([GIT, "init", "-q", str(root)], check=True)
            git(root, "config", "user.email", "core-release-test@edaios.local")
            git(root, "config", "user.name", "EDAIOS Core Release Test")
            (root / "VERSION").write_text("3.1.0\n", encoding="utf-8")
            write_release_state(root)
            git(root, "add", ".")
            git(root, "commit", "-q", "-m", "feat(core): establish portable root")

            head = git(root, "rev-parse", "HEAD")
            report = seal.validate_release_state(root)

            self.assertEqual(report["baseline_root"], head)
            self.assertEqual(
                report["baseline_tree"], git(root, "rev-parse", "HEAD^{tree}")
            )
            self.assertEqual(report["root_derivation"], "unique-reachable-root")
            self.assertEqual(report["publication"], "not-claimed")
            self.assertFalse(report["promotion_allowed"])

    def test_baseline_without_candidate_is_explicit_and_non_promotable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            initialize(root)
            baseline = git(root, "rev-parse", "HEAD")
            baseline_tree = git(root, "rev-parse", "HEAD^{tree}")
            write_release_state(root)
            stale = root / prepare.MANIFEST_RELATIVE
            stale.parent.mkdir(parents=True, exist_ok=True)
            stale.write_text(
                json.dumps({"version": "2.0.0", "status": "prepared"}),
                encoding="utf-8",
            )
            git(root, "add", ".")
            git(root, "commit", "-q", "-m", "record baseline release state")

            report = seal.validate_release_state(root)
            self.assertEqual(report["status"], "baseline-no-candidate")
            self.assertEqual(report["version"], "3.0.0")
            self.assertEqual(report["baseline_root"], baseline)
            self.assertEqual(report["baseline_tree"], baseline_tree)
            self.assertEqual(report["canonical_branch"], "main")
            self.assertIsNone(report["active_candidate"])
            self.assertFalse(report["promotion_allowed"])
            self.assertNotEqual(git(root, "rev-parse", "HEAD"), baseline)
            self.assertEqual(
                subprocess.run(
                    [GIT, "-C", str(root), "merge-base", "--is-ancestor", baseline, "HEAD"]
                ).returncode,
                0,
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(seal.main([str(root), "--json"]), 0)
            cli_report = json.loads(stdout.getvalue())
            self.assertEqual(cli_report["status"], "baseline-no-candidate")
            self.assertIsNone(cli_report["active_candidate"])

    def test_baseline_state_rejects_legacy_pins_and_version_drift(self):
        with self.subTest("legacy-pins"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "workspace"
                initialize(root)
                path, payload = write_release_state(root)
                payload["genealogy"]["root_commit"] = "0" * 40
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(seal.ReleaseSealError, "no verificable"):
                    seal.validate_release_state(root)

        with self.subTest("version"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "workspace"
                initialize(root)
                write_release_state(root, version="9.9.9")
                with self.assertRaisesRegex(seal.ReleaseSealError, "VERSION"):
                    seal.validate_release_state(root)

    def test_baseline_state_rejects_incomplete_or_rewritten_genealogy(self):
        with self.subTest("shallow"):
            with tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "source"
                initialize(source)
                write_release_state(source)
                git(source, "add", ".")
                git(source, "commit", "-q", "-m", "release state")
                shallow = Path(tmp) / "shallow"
                subprocess.run(
                    [
                        GIT,
                        "clone",
                        "-q",
                        "--depth",
                        "1",
                        source.as_uri(),
                        str(shallow),
                    ],
                    check=True,
                )
                with self.assertRaisesRegex(seal.ReleaseSealError, "no shallow"):
                    seal.validate_release_state(shallow)

        with self.subTest("replace-ref"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "workspace"
                initialize(root)
                write_release_state(root)
                baseline = git(root, "rev-parse", "HEAD")
                replacement = git(
                    root, "commit-tree", "HEAD^{tree}", "-m", "replacement root"
                )
                git(root, "replace", baseline, replacement)
                with self.assertRaisesRegex(seal.ReleaseSealError, "refs/replace"):
                    seal.validate_release_state(root)

        with self.subTest("custom-replace-ref-base"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "workspace"
                initialize(root)
                write_release_state(root)
                baseline = git(root, "rev-parse", "HEAD")
                replacement = git(
                    root, "commit-tree", "HEAD^{tree}", "-m", "custom replacement"
                )
                git(root, "update-ref", f"refs/custom/{baseline}", replacement)
                with patch.dict(
                    os.environ,
                    {"GIT_REPLACE_REF_BASE": "refs/custom"},
                    clear=False,
                ):
                    with self.assertRaisesRegex(
                        seal.ReleaseSealError, "GIT_REPLACE_REF_BASE"
                    ):
                        seal.validate_release_state(root)

        with self.subTest("grafts"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "workspace"
                initialize(root)
                write_release_state(root)
                grafts = root / ".git/info/grafts"
                grafts.parent.mkdir(parents=True, exist_ok=True)
                grafts.write_text(
                    f"{git(root, 'rev-parse', 'HEAD')}\n", encoding="ascii"
                )
                with self.assertRaisesRegex(seal.ReleaseSealError, "grafts"):
                    seal.validate_release_state(root)

        with self.subTest("multiple-roots"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "workspace"
                initialize(root)
                write_release_state(root)
                git(root, "add", ".")
                git(root, "commit", "-q", "-m", "release state")
                head = git(root, "rev-parse", "HEAD")
                tree = git(root, "rev-parse", "HEAD^{tree}")
                unrelated = git(root, "commit-tree", tree, "-m", "unrelated root")
                merged = git(
                    root,
                    "commit-tree",
                    tree,
                    "-p",
                    head,
                    "-p",
                    unrelated,
                    "-m",
                    "merge unrelated histories",
                )
                git(root, "checkout", "-q", "--detach", merged)
                with self.assertRaisesRegex(
                    seal.ReleaseSealError, "exactamente una raiz"
                ):
                    seal.validate_release_state(root)

    def test_prepare_cli_requires_explicit_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            initialize(root)
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    prepare.main([str(root)])
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("--manifest", stderr.getvalue())
            self.assertFalse((root / prepare.MANIFEST_RELATIVE).exists())

            with self.assertRaisesRegex(
                prepare.ReleasePreparationError, "path de manifest inseguro"
            ):
                prepare.write_manifest(
                    root, "../outside.json", artifact_builder=fake_artifacts
                )
            with self.assertRaisesRegex(
                prepare.ReleasePreparationError, "path de manifest inseguro"
            ):
                prepare.write_manifest(
                    root,
                    Path(tmp) / "absolute.json",
                    artifact_builder=fake_artifacts,
                )

            outside = Path(tmp) / "outside"
            outside.mkdir()
            linked_parent = root / "linked-release"
            try:
                linked_parent.symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks no disponibles: {exc}")
            with self.assertRaisesRegex(
                prepare.ReleasePreparationError, "parent symlink no permitido"
            ):
                prepare._safe_target(root, "linked-release/candidate.json")
            self.assertFalse((outside / "candidate.json").exists())

    def test_repository_normalization_strips_git_transport_and_rejects_secrets(self):
        self.assertEqual(
            seal._normalize_repository("git@Example.Test:team/edaios.git"),
            "example.test/team/edaios",
        )
        self.assertEqual(
            seal._normalize_repository("ssh://git@Example.Test/team/edaios.git"),
            "example.test/team/edaios",
        )
        with self.assertRaisesRegex(seal.ReleaseSealError, "userinfo"):
            seal._normalize_repository("https://token@example.test/team/edaios.git")
        with self.assertRaisesRegex(seal.ReleaseSealError, "secreto"):
            seal._normalize_repository(
                "https://user:secret@example.test/team/edaios.git"
            )

    def test_dirty_candidate_is_prepared_deterministic_and_tamper_evident(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            initialize(root)
            (root / "source.txt").write_text("candidate\n", encoding="utf-8")

            path, manifest = prepare.write_manifest(
                root, artifact_builder=fake_artifacts
            )
            first = path.read_bytes()
            second_path, second = prepare.write_manifest(
                root, artifact_builder=fake_artifacts
            )

            self.assertEqual(path, second_path)
            self.assertEqual(first, second_path.read_bytes())
            self.assertEqual(manifest, second)
            self.assertEqual(manifest["status"], "prepared")
            self.assertNotIn("governed_worktree_clean", manifest)
            self.assertEqual(len(manifest["artifacts"]["items"]), 6)
            self.assertEqual(manifest["base_tree"], git(root, "rev-parse", "HEAD^{tree}"))
            report = seal.validate_release_candidate(
                root, artifact_builder=fake_artifacts
            )
            self.assertEqual(report["candidate_status"], "prepared")
            self.assertEqual(report["readiness"], "prepared")
            self.assertEqual(
                report["schema"], "edaios.core-release-verification-report/v1"
            )
            self.assertEqual(report["verification_mode"], "local-validation")
            self.assertFalse(report["provider_live_verified"])
            self.assertEqual(report["base_head"], git(root, "rev-parse", "HEAD"))

            (root / "source.txt").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(seal.ReleaseSealError, "diverge"):
                seal.validate_release_candidate(root, artifact_builder=fake_artifacts)

    def test_local_approval_and_remote_seal_are_separate_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp)
            root = outer / "repo"
            initialize(root)
            path, manifest = prepare.write_manifest(
                root, artifact_builder=fake_artifacts
            )

            self.assertEqual(manifest["status"], "prepared")
            self.assertEqual(
                seal.validate_release_candidate(
                    root, artifact_builder=fake_artifacts
                )["candidate_status"],
                "prepared",
            )
            with self.assertRaisesRegex(seal.ReleaseSealError, "worktree limpio"):
                seal.validate_release_candidate(
                    root, require_local_approval=True, artifact_builder=fake_artifacts
                )

            git(root, "add", prepare.MANIFEST_RELATIVE.as_posix())
            git(root, "commit", "-q", "-m", "release candidate")
            with self.assertRaisesRegex(seal.ReleaseSealError, "EvidenceReceipt"):
                seal.validate_release_candidate(
                    root, require_local_approval=True, artifact_builder=fake_artifacts
                )

            head = git(root, "rev-parse", "HEAD")
            evidence, approval, policy, authority, target = write_verified_receipts(
                root,
                outer / "receipts",
                version=manifest["version"],
                base=manifest["base_head"],
                head=head,
            )
            local = seal.validate_release_candidate(
                root,
                require_local_approval=True,
                evidence_receipt=evidence,
                approval_receipt=approval,
                policy=policy,
                authority_registry=authority,
                cutover_target=target,
                artifact_builder=fake_artifacts,
            )
            self.assertEqual(local["status"], "locally-approved")
            self.assertEqual(local["readiness"], "ready-for-approval")
            with self.assertRaisesRegex(seal.ReleaseSealError, "GitCutoverReceipt"):
                seal.validate_release_candidate(
                    root,
                    require_final_seal=True,
                    evidence_receipt=evidence,
                    approval_receipt=approval,
                    policy=policy,
                    authority_registry=authority,
                    cutover_target=target,
                    artifact_builder=fake_artifacts,
                )
            cutover = write_cutover_receipt(
                outer / "cutover.json",
                version=manifest["version"],
                head=head,
                tree=git(root, "rev-parse", "HEAD^{tree}"),
                evidence_receipt=evidence,
                approval_receipt=approval,
            )
            report = seal.validate_release_candidate(
                root,
                require_final_seal=True,
                evidence_receipt=evidence,
                approval_receipt=approval,
                policy=policy,
                authority_registry=authority,
                cutover_target=target,
                cutover_receipt=cutover,
                artifact_builder=fake_artifacts,
            )
            self.assertEqual(report["status"], "sealed-by-authorized-observation")
            self.assertEqual(report["verification_mode"], "authorized-observation")
            self.assertFalse(report["provider_live_verified"])
            self.assertTrue(report["full_worktree_clean"])
            self.assertEqual(report["cutover"]["canonical_branch"], "main")

    def test_receipts_reject_external_policy_and_remote_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp)
            root = outer / "repo"
            initialize(root)
            _, manifest = prepare.write_manifest(root, artifact_builder=fake_artifacts)
            git(root, "add", prepare.MANIFEST_RELATIVE.as_posix())
            git(root, "commit", "-q", "-m", "release candidate")
            head = git(root, "rev-parse", "HEAD")
            evidence, approval, policy, authority, target = write_verified_receipts(
                root,
                outer / "receipts",
                version=manifest["version"],
                base=manifest["base_head"],
                head=head,
            )
            copied_policy = outer / "copied-policy.json"
            shutil.copyfile(policy, copied_policy)
            with self.assertRaisesRegex(seal.ReleaseSealError, "ruta canonica"):
                seal.validate_release_candidate(
                    root,
                    require_local_approval=True,
                    evidence_receipt=evidence,
                    approval_receipt=approval,
                    policy=copied_policy,
                    authority_registry=authority,
                    cutover_target=target,
                    artifact_builder=fake_artifacts,
                )
            cutover = write_cutover_receipt(
                outer / "cutover.json",
                version=manifest["version"],
                head=head,
                tree=git(root, "rev-parse", "HEAD^{tree}"),
                evidence_receipt=evidence,
                approval_receipt=approval,
                remote_head="f" * 40,
            )
            with self.assertRaisesRegex(seal.ReleaseSealError, "remote_head"):
                seal.validate_release_candidate(
                    root,
                    require_final_seal=True,
                    evidence_receipt=evidence,
                    approval_receipt=approval,
                    policy=policy,
                    authority_registry=authority,
                    cutover_target=target,
                    cutover_receipt=cutover,
                    artifact_builder=fake_artifacts,
                )

    def test_seal_rejects_missing_contract_evidence_checks_and_bad_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp)
            root = outer / "repo"
            initialize(root)
            _, manifest = prepare.write_manifest(root, artifact_builder=fake_artifacts)
            git(root, "add", prepare.MANIFEST_RELATIVE.as_posix())
            git(root, "commit", "-q", "-m", "release candidate")
            head = git(root, "rev-parse", "HEAD")
            missing = write_verified_receipts(
                root,
                outer / "missing-receipts",
                version=manifest["version"],
                base=manifest["base_head"],
                head=head,
                evidence_paths=["source.txt"],
            )
            with self.assertRaisesRegex(seal.ReleaseSealError, "no cubre contratos"):
                seal.validate_release_candidate(
                    root,
                    require_local_approval=True,
                    evidence_receipt=missing[0],
                    approval_receipt=missing[1],
                    policy=missing[2],
                    authority_registry=missing[3],
                    cutover_target=missing[4],
                    artifact_builder=fake_artifacts,
                )

            approved_at = datetime.now(timezone.utc)
            evidence, approval, policy, authority, target = write_verified_receipts(
                root,
                outer / "valid-receipts",
                version=manifest["version"],
                base=manifest["base_head"],
                head=head,
                recorded_at=approved_at,
                approved_at=approved_at,
            )
            wrong_checks = write_cutover_receipt(
                outer / "wrong-checks.json",
                version=manifest["version"],
                head=head,
                tree=git(root, "rev-parse", "HEAD^{tree}"),
                evidence_receipt=evidence,
                approval_receipt=approval,
                checks=["OTHER-CHECK"],
            )
            with self.assertRaisesRegex(seal.ReleaseSealError, "required_checks"):
                seal.validate_release_candidate(
                    root,
                    require_final_seal=True,
                    evidence_receipt=evidence,
                    approval_receipt=approval,
                    policy=policy,
                    authority_registry=authority,
                    cutover_target=target,
                    cutover_receipt=wrong_checks,
                    artifact_builder=fake_artifacts,
                )
            stale_order = write_cutover_receipt(
                outer / "bad-order.json",
                version=manifest["version"],
                head=head,
                tree=git(root, "rev-parse", "HEAD^{tree}"),
                evidence_receipt=evidence,
                approval_receipt=approval,
                observed_at=approved_at - timedelta(seconds=1),
            )
            with self.assertRaisesRegex(seal.ReleaseSealError, "precede"):
                seal.validate_release_candidate(
                    root,
                    require_final_seal=True,
                    evidence_receipt=evidence,
                    approval_receipt=approval,
                    policy=policy,
                    authority_registry=authority,
                    cutover_target=target,
                    cutover_receipt=stale_order,
                    artifact_builder=fake_artifacts,
                )

    def test_candidate_rejects_symlinked_governed_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            initialize(root)
            link = root / "alias.txt"
            try:
                link.symlink_to(root / "source.txt")
            except OSError as exc:
                self.skipTest(f"symlinks no disponibles: {exc}")
            with self.assertRaisesRegex(
                prepare.ReleasePreparationError, "symlink no permitido"
            ):
                prepare.build_manifest(root, artifact_builder=fake_artifacts)


if __name__ == "__main__":
    unittest.main()
