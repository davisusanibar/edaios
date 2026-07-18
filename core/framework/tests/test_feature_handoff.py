"""Contract tests for the canonical Spec Kit handoff and local selector."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class FeatureHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_module(
            "test_feature_context_v2", "tools/operations/feature_context.py"
        )
        cls.gate = load_module(
            "test_spec_kit_handoff_v2", "tools/validation/spec_kit_gate.py"
        )

    def _feature(
        self,
        root: Path,
        directory: str,
        feature_id: str,
        *,
        state: str = "Cerrado",
        phase: str = "implemented",
    ) -> dict[str, str]:
        feature = root / "specs" / directory
        feature.mkdir(parents=True)
        typed = feature / "feature.spec.yaml"
        typed.write_text(f"id: {feature_id}\n", encoding="utf-8")
        feature.joinpath("spec.md").write_text(
            "\n".join(
                (
                    "---",
                    f"id: {feature_id}",
                    f"estado: {state}",
                    f"fase: {phase}",
                    f"spec_tipada: specs/{directory}/feature.spec.yaml",
                    "---",
                    "",
                    f"# {feature_id}",
                    "",
                )
            ),
            encoding="utf-8",
        )
        return {
            "id": feature_id,
            "feature_directory": f"specs/{directory}",
        }

    def _repository(self, root: Path) -> dict[str, dict[str, str]]:
        (root / ".specify").mkdir()
        pointers = {
            "baseline_feature": self._feature(root, "004-baseline", "FEATURE-004"),
            "last_closed_feature": self._feature(root, "005-closed", "FEATURE-005"),
            "active_feature": self._feature(
                root,
                "006-active",
                "FEATURE-006",
                state="Propuesto",
                phase="tasked",
            ),
        }
        root.joinpath(".specify/feature.json").write_text(
            json.dumps(
                {"schema": self.context.HANDOFF_SCHEMA, **pointers}, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        return pointers

    def test_resolve_uses_active_feature_and_preserves_local_v1_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pointers = self._repository(root)

            resolved, source = self.context.resolve(root)
            self.assertEqual(source, "canonical")
            self.assertEqual(resolved, pointers["active_feature"])

            root.joinpath(".specify/feature.local.json").write_text(
                json.dumps(pointers["last_closed_feature"]) + "\n", encoding="utf-8"
            )
            resolved, source = self.context.resolve(root)
            self.assertEqual(source, "local")
            self.assertEqual(resolved, pointers["last_closed_feature"])

            resolved, source = self.context.resolve(root, "004-baseline")
            self.assertEqual(source, "explicit")
            self.assertEqual(resolved, pointers["baseline_feature"])

    def test_canonical_selection_changes_only_active_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pointers = self._repository(root)
            next_active = self._feature(
                root,
                "007-next",
                "FEATURE-007",
                state="Propuesto",
                phase="specified",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                status = self.context.main(
                    ["--repo-root", str(root), "select", "007-next", "--canonical"]
                )
            self.assertEqual(status, 0)
            handoff = json.loads(root.joinpath(".specify/feature.json").read_text())
            self.assertEqual(handoff["schema"], self.context.HANDOFF_SCHEMA)
            self.assertEqual(handoff["baseline_feature"], pointers["baseline_feature"])
            self.assertEqual(
                handoff["last_closed_feature"], pointers["last_closed_feature"]
            )
            self.assertEqual(handoff["active_feature"], next_active)

    def test_canonical_selection_promotes_a_closed_active_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pointers = self._repository(root)
            active_spec = root / "specs/006-active/spec.md"
            active_spec.write_text(
                active_spec.read_text(encoding="utf-8")
                .replace("estado: Propuesto", "estado: Cerrado")
                .replace("fase: tasked", "fase: implemented"),
                encoding="utf-8",
            )
            next_active = self._feature(
                root,
                "007-next",
                "FEATURE-007",
                state="Propuesto",
                phase="specified",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                status = self.context.main(
                    ["--repo-root", str(root), "select", "007-next", "--canonical"]
                )
            self.assertEqual(status, 0)
            handoff = json.loads(root.joinpath(".specify/feature.json").read_text())
            self.assertEqual(handoff["baseline_feature"], pointers["baseline_feature"])
            self.assertEqual(handoff["last_closed_feature"], pointers["active_feature"])
            self.assertEqual(handoff["active_feature"], next_active)

    def test_gate_validates_closed_history_and_returns_active_feature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pointers = self._repository(root)
            results = self.gate.Results()
            active = self.gate.registered_feature(root, results)
            self.assertTrue(results.ok)
            self.assertEqual(
                active,
                (root / pointers["active_feature"]["feature_directory"]).resolve(),
            )

            closed_spec = root / "specs/005-closed/spec.md"
            closed_spec.write_text(
                closed_spec.read_text(encoding="utf-8").replace(
                    "estado: Cerrado", "estado: Propuesto"
                ),
                encoding="utf-8",
            )
            rejected = self.gate.Results()
            self.gate.registered_feature(root, rejected)
            self.assertFalse(rejected.ok)
            self.assertTrue(
                any(
                    not ok and "last_closed_feature referencia una feature cerrada" in name
                    for ok, name, _detail in rejected.rows
                )
            )

    def test_legacy_shape_is_allowed_only_for_local_selector(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pointers = self._repository(root)
            legacy = pointers["active_feature"]
            root.joinpath(".specify/feature.json").write_text(
                json.dumps(legacy) + "\n", encoding="utf-8"
            )
            with self.assertRaises(self.context.FeatureContextError):
                self.context.resolve(root)

            root.joinpath(".specify/feature.local.json").write_text(
                json.dumps(legacy) + "\n", encoding="utf-8"
            )
            resolved, source = self.context.resolve(root)
            self.assertEqual(source, "local")
            self.assertEqual(resolved, legacy)


if __name__ == "__main__":
    unittest.main()
