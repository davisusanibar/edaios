from contextlib import contextmanager, redirect_stderr, redirect_stdout
from hashlib import sha256
from io import StringIO
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from edaios_conformance import SchemaRegistry
from edaios_core_harness.cli import main as cli_main
from edaios_core_harness.agent_setup import (
    AgentSetupCollision,
    AgentSetupError,
    apply_setup,
    plan_setup,
    rollback_setup,
    verify_setup,
)
from edaios_memory_adapter import EngramAdapterError, EngramHTTPProvider


class _Response:
    def __init__(self, value, url="http://127.0.0.1:7437/mock"):
        self.raw = json.dumps(value).encode("utf-8")
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.raw

    def geturl(self):
        return self.url


def _engram_response(request, timeout):
    del timeout
    url = request.full_url
    if url.endswith("/health"):
        return _Response({"status": "ok", "service": "engram", "version": "0.1.0"})
    if "/search?" in url:
        return _Response({"results": [{"id": 1, "title": "memory"}]})
    if "/conflicts?" in url:
        return _Response({"relations": [{"sync_id": "rel-1", "judgment_status": "pending"}]})
    if url.rstrip("?").endswith("/context") or "/context?" in url:
        return _Response({"context": "sesiones y observaciones del proyecto"})
    if request.method == "POST":
        return _Response({"accepted": True, "body": json.loads(request.data or b"{}")})
    return _Response({"observations": [{"id": 1, "title": "event"}]})


def _canonical(value):
    return json.dumps(
        value, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"


def _digest(value):
    return "sha256:" + sha256(value).hexdigest()


def _receipt_id(value):
    identity = {
        key: value[key]
        for key in (
            "surface", "target", "before_digest", "after_digest",
            "integration_lock_digest",
        )
    }
    return "SETUP-" + sha256(_canonical(identity)).hexdigest()[:24].upper()


def _write_rehashed_receipt(path, value):
    unsigned = {key: item for key, item in value.items() if key != "integrity"}
    value["integrity"] = {
        **value["integrity"],
        "payload_sha256": _digest(_canonical(unsigned)),
    }
    path.write_bytes(_canonical(value))


class MemoryAdapterTest(unittest.TestCase):
    def test_adapter_is_loopback_pinned_and_non_authoritative(self):
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_engram_response):
            provider = EngramHTTPProvider()
            self.assertEqual(provider.health()["status"], "ok")
            self.assertFalse(provider.capabilities()["authoritative"])
            self.assertIn("promote", provider.capabilities()["forbidden_operations"])
            hits = provider.search("memory", project="alpha")
            self.assertEqual(len(hits), 1)
            self.assertFalse(hits[0]["authoritative"])
            saved = provider.save_observation(
                session_id="session/one",
                project="alpha",
                subject="orders",
                claim="backend",
                value="RocksDB",
            )
            self.assertEqual(saved["channel"], "local-working")
            self.assertEqual(len(provider.conflict_candidates(project="alpha")), 1)

    def test_adapter_context_is_read_only_and_bounded(self):
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_engram_response):
            provider = EngramHTTPProvider()
            self.assertIn("context", provider.capabilities()["operations"])
            envelope = provider.get_context(project="alpha", scope="project")
        self.assertEqual(envelope["operation"], "context")
        self.assertEqual(envelope["channel"], "local-working")
        self.assertFalse(envelope["authoritative"])
        self.assertEqual(
            envelope["result"]["context"], "sesiones y observaciones del proyecto"
        )
        with self.assertRaisesRegex(EngramAdapterError, "scope"):
            EngramHTTPProvider().get_context(scope="invalid")

    def test_adapter_degrades_and_rejects_remote_or_sensitive_routes(self):
        with self.assertRaises(EngramAdapterError):
            EngramHTTPProvider("https://engram.example.test")
        missing = EngramHTTPProvider(timeout_seconds=0.1)
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=URLError("offline")):
            self.assertEqual(missing.health()["status"], "degraded")
        provider = EngramHTTPProvider()
        with self.assertRaises(EngramAdapterError):
            provider.save_observation(
                session_id="s", project="p", subject="x", claim="y", value="z",
                sensitivity="T2",
            )
        incompatible = EngramHTTPProvider(required_version="0.2.0")
        with patch("edaios_memory_adapter.engram._open_loopback", side_effect=_engram_response):
            self.assertEqual(incompatible.health()["status"], "incompatible")
        with patch(
            "edaios_memory_adapter.engram._open_loopback",
            return_value=_Response(
                {"status": "ok", "service": "engram", "version": "0.1.0"},
                url="http://remote.example.test/health",
            ),
        ):
            with self.assertRaises(EngramAdapterError):
                provider.health()
        handler = __import__(
            "edaios_memory_adapter.engram", fromlist=["_RejectRedirects"]
        )._RejectRedirects()
        with self.assertRaisesRegex(EngramAdapterError, "redirect Engram rechazado"):
            handler.redirect_request()


def _run_cli(argv):
    out, err = StringIO(), StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli_main(argv)
    payload_text = out.getvalue().strip() or err.getvalue().strip()
    return code, json.loads(payload_text)


class MemoryCliProviderTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_defaults_to_local_provider(self):
        code, payload = _run_cli(["memory", "doctor", "--root", self.root])
        self.assertEqual(code, 0)
        self.assertEqual(payload["command"], "memory.doctor")
        self.assertIn("search_mode", payload["result"]["health"])

    def test_engram_provider_doctor_is_non_authoritative(self):
        with patch(
            "edaios_memory_adapter.engram._open_loopback", side_effect=_engram_response
        ):
            code, payload = _run_cli(
                ["memory", "doctor", "--root", self.root, "--provider", "engram"]
            )
        self.assertEqual(code, 0)
        self.assertEqual(payload["result"]["health"]["status"], "ok")
        self.assertFalse(payload["result"]["capabilities"]["authoritative"])

    def test_engram_context_returns_bounded_envelope(self):
        with patch(
            "edaios_memory_adapter.engram._open_loopback", side_effect=_engram_response
        ):
            code, payload = _run_cli(
                ["memory", "context", "--root", self.root,
                 "--provider", "engram", "--project", "alpha"]
            )
        self.assertEqual(code, 0)
        self.assertEqual(payload["command"], "memory.context")
        self.assertEqual(payload["result"]["operation"], "context")
        self.assertFalse(payload["result"]["authoritative"])

    def test_context_requires_engram_provider(self):
        code, payload = _run_cli(["memory", "context", "--root", self.root])
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("engram", payload["error"]["message"])

    def test_engram_degrades_without_runtime(self):
        with patch(
            "edaios_memory_adapter.engram._open_loopback",
            side_effect=URLError("offline"),
        ):
            code, payload = _run_cli(
                ["memory", "doctor", "--root", self.root, "--provider", "engram"]
            )
        self.assertEqual(code, 0)
        self.assertEqual(payload["result"]["health"]["status"], "degraded")

    def test_session_event_rejects_engram_with_domain_error(self):
        code, payload = _run_cli([
            "memory", "session-event", "--root", self.root, "--provider", "engram",
            "--session", "S-1", "--kind", "gate", "--payload", '{"a": 1}',
        ])
        self.assertEqual(code, 2)
        self.assertIn("no soporta session-event", payload["error"]["message"])

    def test_unknown_subcommand_fails_closed_without_traceback(self):
        for argv in (
            ["memory", "health", "--root", "."],
            ["agent-setup", "bogus", "--root", "."],
        ):
            with self.subTest(argv=argv):
                code, payload = _run_cli(argv)
                self.assertEqual(code, 2)
                self.assertEqual(payload["status"], "blocked")

    def test_engram_save_requires_session(self):
        with patch(
            "edaios_memory_adapter.engram._open_loopback", side_effect=_engram_response
        ):
            code, payload = _run_cli([
                "memory", "save", "--root", self.root, "--provider", "engram",
                "--project", "alpha", "--subject", "orders",
                "--claim", "backend", "--value", "RocksDB",
            ])
        self.assertEqual(code, 2)
        self.assertIn("session", payload["error"]["message"])


class AgentSetupTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / ".specify").mkdir()
        (self.root / ".specify/integrations.lock.json").write_text(
            json.dumps(
                {
                    "schema": "edaios.speckit.integrations/v1",
                    "source": "edaios-core@v3.1.0+spec-kit@v0.12.11",
                    "commands": {},
                }
            ) + "\n",
            encoding="utf-8",
        )
        (self.root / "AGENTS.md").write_text("# Existing instructions\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_plan_apply_verify_idempotency_and_rollback(self):
        original = (self.root / "AGENTS.md").read_bytes()
        plan = plan_setup(self.root, surface="codex")
        self.assertEqual(plan["change"], "write")
        self.assertFalse(plan["write_authorized"])
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), original)

        applied = apply_setup(self.root, surface="codex")
        self.assertEqual(applied["status"], "applied")
        self.assertIn("EDAIOS-CORE:BEGIN", (self.root / "AGENTS.md").read_text())
        self.assertEqual(verify_setup(self.root, surface="codex")["status"], "valid")
        self.assertEqual(apply_setup(self.root, surface="codex")["status"], "unchanged")

        receipt = self.root / applied["receipt"]
        SchemaRegistry().validate("agent-setup-receipt", json.loads(receipt.read_text()))
        rolled = rollback_setup(self.root, receipt=applied["receipt"])
        self.assertEqual(rolled["status"], "rolled-back")
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), original)

    def test_unbalanced_managed_markers_fail_closed(self):
        (self.root / "AGENTS.md").write_text(
            "# Existing\n<!-- EDAIOS-CORE:BEGIN agent-working-memory -->\n",
            encoding="utf-8",
        )
        with self.assertRaises(AgentSetupCollision):
            plan_setup(self.root, surface="codex")

    def test_rollback_revalidates_receipt_after_acquiring_lock(self):
        applied = apply_setup(self.root, surface="codex")
        receipt = self.root / applied["receipt"]

        @contextmanager
        def mutate_receipt_after_lock(*_args, **_kwargs):
            receipt.write_text("{}\n", encoding="utf-8")
            yield

        with patch(
            "edaios_core_harness.agent_setup.workspace_lock",
            mutate_receipt_after_lock,
        ):
            with self.assertRaises(AgentSetupError):
                rollback_setup(self.root, receipt=applied["receipt"])

    def test_rollback_rejects_rehashed_receipt_with_forged_target(self):
        applied = apply_setup(self.root, surface="codex")
        original_receipt = self.root / applied["receipt"]
        value = json.loads(original_receipt.read_text(encoding="utf-8"))
        original_backup = self.root / value["backup"]

        forged_target = self.root / "notes.md"
        forged_target.write_bytes((self.root / "AGENTS.md").read_bytes())
        value["target"] = "notes.md"
        value["receipt_id"] = _receipt_id(value)
        value["backup"] = (
            f".edaios/agent-setup/backups/{value['receipt_id']}/original.bin"
        )
        forged_backup = self.root / value["backup"]
        forged_backup.parent.mkdir(parents=True)
        forged_backup.write_bytes(original_backup.read_bytes())
        forged_receipt = (
            self.root / ".edaios/agent-setup/receipts"
            / f"{value['receipt_id']}.json"
        )
        _write_rehashed_receipt(forged_receipt, value)

        with self.assertRaisesRegex(AgentSetupCollision, "target no corresponde"):
            rollback_setup(
                self.root, receipt=forged_receipt.relative_to(self.root)
            )
        self.assertEqual(forged_target.read_bytes(), (self.root / "AGENTS.md").read_bytes())

    def test_rollback_rejects_rehashed_receipt_with_forged_backup(self):
        applied = apply_setup(self.root, surface="codex")
        receipt = self.root / applied["receipt"]
        value = json.loads(receipt.read_text(encoding="utf-8"))
        original_backup = self.root / value["backup"]
        value["backup"] = (
            f".edaios/agent-setup/backups/{value['receipt_id']}/forged/original.bin"
        )
        forged_backup = self.root / value["backup"]
        forged_backup.parent.mkdir(parents=True)
        forged_backup.write_bytes(original_backup.read_bytes())
        _write_rehashed_receipt(receipt, value)

        with self.assertRaisesRegex(AgentSetupCollision, "backup no corresponde"):
            rollback_setup(self.root, receipt=applied["receipt"])

    def test_rollback_rejects_symlinked_backup_component(self):
        applied = apply_setup(self.root, surface="codex")
        receipt = self.root / applied["receipt"]
        value = json.loads(receipt.read_text(encoding="utf-8"))
        backup = self.root / value["backup"]
        content = backup.read_bytes()
        outside = self.root / "outside.bin"
        outside.write_bytes(content)
        backup.unlink()
        backup.symlink_to(outside)

        with self.assertRaisesRegex(AgentSetupCollision, "backup symlink"):
            rollback_setup(self.root, receipt=applied["receipt"])

    def test_rollback_rejects_receipt_filename_not_bound_to_id(self):
        applied = apply_setup(self.root, surface="codex")
        receipt = self.root / applied["receipt"]
        alias = receipt.with_name("SETUP-000000000000000000000000.json")
        alias.write_bytes(receipt.read_bytes())
        with self.assertRaisesRegex(AgentSetupCollision, "receipt path"):
            rollback_setup(self.root, receipt=alias.relative_to(self.root))

    def test_rollback_rejects_invalid_receipt_id_format(self):
        applied = apply_setup(self.root, surface="codex")
        receipt = self.root / applied["receipt"]
        value = json.loads(receipt.read_text(encoding="utf-8"))
        value["receipt_id"] = "SETUP-invalid"
        _write_rehashed_receipt(receipt, value)
        with self.assertRaisesRegex(AgentSetupError, "contrato de receipt"):
            rollback_setup(self.root, receipt=applied["receipt"])


if __name__ == "__main__":
    unittest.main()
