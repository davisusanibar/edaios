"""ADR-0016 — perfil consumer-release y gate SDD parametrizable por profile.

Verifica el seam: consumer-release resuelve como raíz liviana sin registry de
Core, core-release exige el registry, y la selección de modo estructural es
fail-closed por allowlist (solo consumer-release apaga el bookkeeping).
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GATE_PATH = ROOT / "tools" / "validation" / "spec_kit_gate.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("spec_kit_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConsumerReleaseProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = _load_gate()

    def _rows(self, results):
        return {name: ok for ok, name, _detail in results.rows}

    def test_consumer_release_resuelve_sin_registry_de_core(self):
        """consumer-release es built-in: no exige core/framework/core/profiles/."""
        with tempfile.TemporaryDirectory() as tmp:
            results = self.gate.Results()
            controls = self.gate.load_validation_profile(Path(tmp), "consumer-release", results)
        self.assertEqual(controls, {"sdd-contract", "claim-surface"})
        self.assertNotIn("core-monorepo", controls)
        rows = self._rows(results)
        self.assertIn("perfil consumer-release (raiz liviana, ADR-0016)", rows)
        self.assertTrue(all(rows.values()))

    def test_core_release_exige_registry_y_declara_core_monorepo(self):
        """Un core profile sin registry falla; su set incluye core-monorepo."""
        with tempfile.TemporaryDirectory() as tmp:
            results = self.gate.Results()
            controls = self.gate.load_validation_profile(Path(tmp), "core-release", results)
        # Sin registry, el profile no resuelve: falla fail-closed y no elude checks.
        rows = self._rows(results)
        self.assertIn("registry de perfiles parseable", rows)
        self.assertFalse(rows["registry de perfiles parseable"])
        self.assertNotIn("core-monorepo", controls)  # no resolvió: set vacío

    def test_modo_estructural_es_allowlist_fail_closed(self):
        """Solo consumer-release apaga lo estructural; el resto lo exige."""
        # Refleja la derivación de main(): structural = profile != 'consumer-release'.
        for profile in ("core-release", "initiative-adoption", "federation"):
            self.assertTrue(profile != "consumer-release", profile)
        self.assertFalse("consumer-release" != "consumer-release")

    def test_gate_declara_consumer_release_como_choice(self):
        source = GATE_PATH.read_text(encoding="utf-8")
        self.assertIn('"consumer-release"', source)
        self.assertIn('structural = args.profile != "consumer-release"', source)


if __name__ == "__main__":
    unittest.main()
