import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from edaios_conformance import SchemaRegistry
from edaios_core.io import WorkspaceLockError, workspace_lock
from edaios_core.memory import (
    LocalWorkingMemory,
    MemoryContractError,
    MemoryProvider,
    PendingConflictError,
)
from edaios_core_harness.cli import main as cli_main
from edaios_sdd_adapter import (
    DraftGuardError,
    assert_draft_promotable,
    draft_conflict_candidates,
    ingest_artifact,
)


class WorkingMemoryTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_records_are_local_typed_idempotent_and_never_promote(self):
        memory = LocalWorkingMemory(self.root)
        self.assertIsInstance(memory, MemoryProvider)
        self.assertFalse(hasattr(memory, "promote"))
        record = memory.save_observation(
            project="alpha",
            subject="orders",
            claim="state-backend",
            value="RocksDB",
            source_ref="test",
            created_at="2026-07-16T10:00:00Z",
        )
        duplicate = memory.save_observation(
            project="alpha",
            subject="orders",
            claim="state-backend",
            value="RocksDB",
            source_ref="test",
            created_at="2026-07-16T11:00:00Z",
        )
        self.assertEqual(record.record_id, duplicate.record_id)
        self.assertFalse(record.authoritative)
        self.assertTrue(record.rebuildable)
        self.assertEqual(record.channel, "local-working")
        SchemaRegistry().validate("memory-record", record.to_dict())
        self.assertEqual(memory.conflict_candidates(project="alpha"), [])
        self.assertTrue((self.root / ".edaios/memory/working.sqlite3").is_file())
        self.assertFalse(any(self.root.glob("*.sqlite3")))

    def test_conflicts_are_candidates_and_suggestions_remain_advisory(self):
        memory = LocalWorkingMemory(self.root)
        for value in ("RocksDB", "HashMapStateBackend"):
            memory.save_observation(
                project="alpha",
                subject="orders",
                claim="state-backend",
                value=value,
                source_ref="test",
            )
        candidates = memory.conflict_candidates(project="alpha")
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.status, "review-required")
        SchemaRegistry().validate("memory-conflict-candidate", candidate.to_dict())
        suggestion = memory.suggest_conflict(
            candidate.candidate_id,
            relation="supersedes",
            source="test-agent",
            reasoning="La segunda observación declara reemplazo.",
        )
        self.assertFalse(suggestion["authoritative"])
        with self.assertRaises(MemoryContractError):
            memory.suggest_conflict(
                candidate.candidate_id,
                relation="accepted",
                source="test-agent",
                reasoning="Un agente no puede aceptar.",
            )
        self.assertEqual(
            memory.conflict_candidates(project="alpha")[0].status,
            "review-required",
        )
        with self.assertRaises(PendingConflictError):
            memory.assert_promotable(project="alpha")

    def test_sessions_are_hash_chained_and_summaries_are_not_evidence(self):
        memory = LocalWorkingMemory(self.root)
        started = memory.start_session(
            session_id="session-1",
            project="alpha",
            feature="007",
            actor_id="OWNER-1",
            agent="codex",
            worktree=str(self.root),
            branch="feature/memory",
            head_start="abc123",
            created_at="2026-07-16T10:00:00Z",
        )
        self.assertEqual(started["evidence_status"], "observation-only")
        memory.append_session_event(
            "session-1",
            kind="gate",
            payload={"command": "test", "exit_code": 0},
            created_at="2026-07-16T10:01:00Z",
        )
        closed = memory.end_session(
            "session-1",
            summary="Tests locales ejecutados.",
            head_end="def456",
            receipt_refs=[{"receipt_id": "EVR-1", "digest": "0" * 64}],
            created_at="2026-07-16T10:02:00Z",
        )
        self.assertEqual(closed["summary_event"]["payload"]["verification"], "unverified")
        timeline = memory.timeline("session-1")
        self.assertEqual([event.kind for event in timeline], ["start", "gate", "summary", "end"])
        for event in timeline:
            SchemaRegistry().validate("memory-session-event", event.to_dict())
        self.assertEqual(memory.verify_session("session-1")["status"], "valid")
        connection = sqlite3.connect(memory.database)
        try:
            connection.execute(
                "UPDATE session_events SET payload_json='{}' WHERE session_id=? AND sequence=2",
                ("session-1",),
            )
            connection.commit()
        finally:
            connection.close()
        self.assertEqual(memory.verify_session("session-1")["status"], "invalid")

        memory_two = LocalWorkingMemory(self.root, database=".edaios/memory/second.sqlite3")
        memory_two.start_session(
            session_id="session-2", project="alpha", feature="007",
            actor_id="OWNER-1", agent="codex", worktree=str(self.root),
            branch="feature/memory", head_start="abc123",
            created_at="2026-07-16T11:00:00Z",
        )
        memory_two.end_session(
            "session-2", summary="Cierre.", head_end="def456",
            created_at="2026-07-16T11:01:00Z",
        )
        with sqlite3.connect(memory_two.database) as connection:
            connection.execute(
                "DELETE FROM session_events WHERE session_id=? AND sequence=3",
                ("session-2",),
            )
            connection.commit()
        verification = memory_two.verify_session("session-2")
        self.assertEqual(verification["status"], "invalid")
        self.assertTrue(any("event_count" in issue for issue in verification["issues"]))

    def test_paths_utf8_and_concurrent_writes_fail_closed(self):
        with self.assertRaises(MemoryContractError):
            LocalWorkingMemory(self.root, database="../escape.sqlite3")
        memory = LocalWorkingMemory(self.root)
        with self.assertRaises(MemoryContractError):
            memory.save_observation(
                project="alpha", subject="bad\ud800", claim="x", value="y"
            )
        with workspace_lock(self.root, "local-working-memory"):
            with self.assertRaises(WorkspaceLockError):
                memory.save_observation(
                    project="alpha", subject="x", claim="y", value="z"
                )

    def test_fallback_search_and_cli_boundary_are_explicit(self):
        memory = LocalWorkingMemory(self.root, force_fallback=True)
        memory.save_observation(
            project="alpha", subject="checkpoint", claim="mode", value="local fallback"
        )
        self.assertEqual(memory.health()["search_mode"], "fallback-like")
        self.assertEqual(len(memory.search("fallback")), 1)
        output = StringIO()
        with redirect_stdout(output):
            code = cli_main(["memory", "doctor", "--root", str(self.root), "--force-fallback"])
        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["schema"], "edaios.memory-cli-output/v1")
        self.assertIn("no confiere autoridad", payload["claim_boundary"])

    def test_sdd_draft_ingest_preserves_revisions_and_blocks_conflicts(self):
        with self.assertRaises(TypeError):
            ingest_artifact(
                self.root,
                name="unclassified",
                kind="architecture",
                content="No sensitivity must not be inferred.",
                tipo="Article",
                source_tool="spec-kit",
                tool_version="0.12.11",
            )
        first = ingest_artifact(
            self.root,
            name="state backend",
            kind="architecture",
            content="Use RocksDB.",
            tipo="Article",
            source_tool="spec-kit",
            tool_version="0.12.11",
            sensitivity="T0",
        )
        duplicate = ingest_artifact(
            self.root,
            name="state backend",
            kind="architecture",
            content="Use RocksDB.",
            tipo="Article",
            source_tool="spec-kit",
            tool_version="0.12.11",
            sensitivity="T0",
        )
        second = ingest_artifact(
            self.root,
            name="state backend",
            kind="architecture",
            content="Use HashMapStateBackend.",
            tipo="Article",
            source_tool="external-sdd",
            tool_version="1.0.0",
            sensitivity="T0",
        )
        self.assertEqual(first, duplicate)
        self.assertNotEqual(first, second)
        self.assertTrue(first.is_file() and second.is_file())
        self.assertFalse((self.root / ".edaios/memory").exists())
        self.assertEqual(len(draft_conflict_candidates(self.root, name="state backend")), 1)
        with self.assertRaises(PendingConflictError):
            assert_draft_promotable(self.root, name="state backend")
        with self.assertRaises(DraftGuardError):
            ingest_artifact(
                self.root,
                name="bad\nname",
                kind="architecture",
                content="x",
                tipo="Article",
                source_tool="tool",
                tool_version="1.0.0",
                sensitivity="T0",
            )
        original = first.read_text(encoding="utf-8")
        first.write_text(original.replace("Use RocksDB.", "Use TamperedState."), encoding="utf-8")
        with self.assertRaises(DraftGuardError):
            assert_draft_promotable(self.root, name="state backend")


if __name__ == "__main__":
    unittest.main()
