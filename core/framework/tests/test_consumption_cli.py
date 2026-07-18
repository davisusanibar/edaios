"""La CLI de consumo es read-only, con sobre JSON estable y frontera declarada (ADR-0008)."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from edaios_core_harness.cli import CLI_OUTPUT_SCHEMA, READ_ONLY_BOUNDARY, main


ROOT = Path(__file__).resolve().parents[3]


def run_cli(*argv: str) -> tuple[int, dict]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = main(list(argv))
    return code, json.loads(stdout.getvalue())


class ConsumptionCliTests(unittest.TestCase):
    def test_kos_list_and_get_are_read_only(self):
        state = ROOT / ".edaios"
        existed_before = state.exists()
        code, payload = run_cli("kos", "list", "--root", str(ROOT))
        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], CLI_OUTPUT_SCHEMA)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["claim_boundary"], READ_ONLY_BOUNDARY)
        ids = {row["id"] for row in payload["result"]}
        self.assertIn("ART-000", ids)
        self.assertTrue(all(row["estado"] == "Ratificado" for row in payload["result"]))

        code, payload = run_cli(
            "kos", "get", "--root", str(ROOT), "--id", "ART-000", "--kind", "aicontext",
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["result"]["ko_id"], "ART-000")
        self.assertTrue(payload["result"]["content"].strip())
        # read-only: la consulta no materializa estado local
        self.assertEqual(state.exists(), existed_before)

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["kos", "get", "--root", str(ROOT), "--id", "NO-EXISTE"])
        self.assertEqual(code, 2)
        blocked = json.loads(stderr.getvalue())
        self.assertEqual(blocked["schema"], CLI_OUTPUT_SCHEMA)
        self.assertEqual(blocked["command"], "kos.get")
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["claim_boundary"], READ_ONLY_BOUNDARY)
        self.assertEqual(blocked["error"]["code"], "NOT_FOUND")

    def test_query_commands_report_boundary(self):
        code, payload = run_cli("query", "find", "--root", str(ROOT))
        self.assertEqual(code, 0)
        self.assertEqual(payload["schema"], CLI_OUTPUT_SCHEMA)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["claim_boundary"], READ_ONLY_BOUNDARY)
        self.assertEqual(payload["result"], [])  # grafo latente sin instancia

        for action in ("impact", "neighborhood"):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main([
                    "query", action, "--root", str(ROOT), "--node", "zona-x",
                ])
            self.assertEqual(code, 2)
            blocked = json.loads(stderr.getvalue())
            self.assertEqual(blocked["schema"], CLI_OUTPUT_SCHEMA)
            self.assertEqual(blocked["command"], f"query.{action}")
            self.assertEqual(blocked["error"]["code"], "NOT_FOUND")

        with tempfile.TemporaryDirectory() as tmp:
            graph = Path(tmp) / "knowledge-graph"
            graph.mkdir()
            (graph / "type.json").write_text(json.dumps({
                "kind": "entity_type", "name": "component",
            }))
            (graph / "node.json").write_text(json.dumps({
                "kind": "entity", "id": "zona-x", "type": "component",
                "name": "Zona X",
            }))
            code, payload = run_cli(
                "query", "impact", "--root", tmp, "--node", "zona-x",
            )
            self.assertEqual(code, 0)
            self.assertEqual(payload["result"]["root"]["id"], "zona-x")
            code, payload = run_cli(
                "query", "neighborhood", "--root", tmp, "--node", "zona-x",
            )
            self.assertEqual(code, 0)
            self.assertEqual(
                [row["id"] for row in payload["result"]["nodes"]], ["zona-x"],
            )

    def test_empty_node_returns_contractual_not_found_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph = Path(tmp) / "knowledge-graph"
            graph.mkdir()
            (graph / "type.json").write_text(json.dumps({
                "kind": "entity_type", "name": "component",
            }))
            (graph / "node.json").write_text(json.dumps({
                "kind": "entity", "id": "zona-x", "type": "component",
                "name": "Zona X",
            }))
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main([
                    "query", "impact", "--root", tmp, "--node", "",
                ])
            self.assertEqual(code, 2)
            blocked = json.loads(stderr.getvalue())
            self.assertEqual(blocked["schema"], CLI_OUTPUT_SCHEMA)
            self.assertEqual(blocked["command"], "query.impact")
            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(blocked["error"]["code"], "NOT_FOUND")
            self.assertEqual(blocked["error"]["message"], "NodeNotFound")

    def test_all_consumption_subcommands_emit_contractual_parse_errors(self):
        cases = (
            ("kos", "list", "--desconocido"),
            ("kos", "get"),
            ("query", "find", "--desconocido"),
            ("query", "impact"),
            ("query", "neighborhood", "--depth", "no-entero"),
        )
        for argv in cases:
            with self.subTest(argv=argv):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    code = main(list(argv))
                self.assertEqual(code, 2)
                blocked = json.loads(stderr.getvalue())
                self.assertEqual(blocked["schema"], CLI_OUTPUT_SCHEMA)
                self.assertEqual(blocked["command"], f"{argv[0]}.{argv[1]}")
                self.assertEqual(blocked["status"], "blocked")
                self.assertEqual(blocked["error"]["code"], "INVALID_ARGUMENT")


if __name__ == "__main__":
    unittest.main()
