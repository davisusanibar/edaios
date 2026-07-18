from pathlib import Path
import tempfile
import unittest

from edaios_core.io import write_text
from edaios_core_harness import CoreHarness
from edaios_ekg.graph import build_graph
from edaios_query import QueryEngine


class BaselineCoreTests(unittest.TestCase):
    def test_atomic_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "state.txt"
            write_text(target, "governed\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "governed\n")

    def test_harness_contracts(self):
        result = CoreHarness().validate()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["execution_policy"], "coordinate-and-validate-only")

    def test_empty_graph_is_latent(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph = build_graph(Path(tmp))
            self.assertEqual(graph["nodes"], [])
            self.assertEqual(QueryEngine.from_graph(graph).find(), [])


if __name__ == "__main__":
    unittest.main()
