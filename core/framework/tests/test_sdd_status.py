"""Regression: estado SDD estructurado edaios.sdd.status/v1 (specs/013)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PHASE_DAG = "core/framework/modules/harness-core/src/edaios_core_harness/resources/phase-dag.json"


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class SddStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = load_module("test_feature_context_status", "tools/operations/feature_context.py")

    def _root(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="edaios-status-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        dag = tmp / PHASE_DAG
        dag.parent.mkdir(parents=True)
        shutil.copy(ROOT / PHASE_DAG, dag)
        return tmp

    def _feature(self, root: Path, name: str, estado: str, fase: str,
                 with_checklist: bool = False) -> str:
        directory = root / "specs" / name
        directory.mkdir(parents=True)
        feature_id = f"EDAIOS-{name.upper().replace('/', '-').replace('_', '-')}"
        (directory / "spec.md").write_text(
            f"---\nid: {feature_id}\nestado: {estado}\nfase: {fase}\n---\n\n# Fixture\n",
            encoding="utf-8",
        )
        (directory / "feature.spec.yaml").write_text(
            f"id: {feature_id}\n", encoding="utf-8"
        )
        if with_checklist:
            (directory / "checklists").mkdir()
            (directory / "checklists/requirements.md").write_text("# ok\n", encoding="utf-8")
        return f"specs/{name}"

    def test_idle_handoff_v3_no_es_error(self) -> None:
        root = self._root()
        base = self._feature(root, "001-base", "Cerrado", "implemented")
        closed = self._feature(root, "002-cerrada", "Cerrado", "implemented")
        (root / ".specify").mkdir()
        (root / ".specify/feature.json").write_text(
            json.dumps({
                "schema": "edaios.feature-handoff/v3",
                "baseline_feature": {"id": "EDAIOS-001-BASE", "feature_directory": base},
                "last_closed_feature": {"id": "EDAIOS-002-CERRADA", "feature_directory": closed},
                "active_feature": None,
            }),
            encoding="utf-8",
        )
        payload = self.tool.sdd_status(root)
        self.assertEqual(payload["nextRecommended"], "idle")
        self.assertIsNone(payload["feature"])
        self.assertEqual(payload["blockedReasons"], [])

    def test_sin_selector_alguno_es_idle(self) -> None:
        root = self._root()
        payload = self.tool.sdd_status(root)
        self.assertEqual(payload["nextRecommended"], "idle")
        self.assertEqual(payload["source"], "idle")

    def test_planned_recomienda_tasks(self) -> None:
        root = self._root()
        feature = self._feature(root, "010-media", "Propuesto", "planned")
        payload = self.tool.sdd_status(root, feature, with_gate=False)
        self.assertEqual(payload["nextRecommended"], "tasks")
        self.assertEqual(payload["fase"], "planned")

    def test_clarified_depende_del_checklist(self) -> None:
        root = self._root()
        sin = self._feature(root, "011-sin-checklist", "Propuesto", "clarified")
        con = self._feature(root, "012-con-checklist", "Propuesto", "clarified",
                            with_checklist=True)
        self.assertEqual(
            self.tool.sdd_status(root, sin, with_gate=False)["nextRecommended"],
            "checklist",
        )
        self.assertEqual(
            self.tool.sdd_status(root, con, with_gate=False)["nextRecommended"],
            "plan",
        )

    def test_cerrada_es_idle(self) -> None:
        root = self._root()
        feature = self._feature(root, "013-cerrada", "Cerrado", "implemented")
        payload = self.tool.sdd_status(root, feature, with_gate=False)
        self.assertEqual(payload["nextRecommended"], "idle")

    def test_fase_desconocida_falla_cerrado(self) -> None:
        root = self._root()
        feature = self._feature(root, "014-rara", "Propuesto", "inventada")
        with self.assertRaisesRegex(self.tool.FeatureContextError, "fuera del dominio"):
            self.tool.sdd_status(root, feature, with_gate=False)

    def test_gate_rojo_bloquea_y_retiene_la_fase(self) -> None:
        # Sin gate sembrado en el root la verificacion es imposible: fail-closed
        # (mismo contrato que un consumer sin seed_gate, RFC-0002/ADR-0020).
        root = self._root()
        feature = self._feature(root, "015-bloqueada", "Propuesto", "planned")
        payload = self.tool.sdd_status(root, feature, with_gate=True)
        self.assertTrue(payload["blockedReasons"], payload)
        self.assertEqual(payload["nextRecommended"], "plan")

    def test_corpus_real_en_verde(self) -> None:
        # La feature 013 queda Cerrada en el corpus: su respuesta estable es idle
        # con gate en verde (lista de bloqueos vacía).
        payload = self.tool.sdd_status(ROOT, "specs/archive/013-sdd-status-maquina")
        self.assertEqual(payload["blockedReasons"], [], payload)
        self.assertEqual(payload["nextRecommended"], "idle")
        self.assertEqual(payload["estado"], "Cerrado")
        self.assertEqual(payload["schema"], "edaios.sdd.status/v1")


if __name__ == "__main__":
    unittest.main()
