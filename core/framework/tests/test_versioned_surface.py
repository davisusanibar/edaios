"""Los gates de superficie juzgan lo versionado; el estado local es reconstruible."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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


surface = load_module("surface_check", "tools/validation/baseline_surface_check.py")
structure = load_module("structure_check", "tools/validation/monorepo_structure_check.py")


@unittest.skipUnless(GIT, "git no disponible")
class VersionedSurfaceTests(unittest.TestCase):
    def test_untracked_state_is_not_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run([GIT, "init", "-q", str(root)], check=True)
            tracked = root / "core" / "foundation" / "ko.md"
            tracked.parent.mkdir(parents=True)
            tracked.write_text("x\n", encoding="utf-8")
            subprocess.run([GIT, "-C", str(root), "add", "."], check=True)
            (root / ".edaios" / "locks").mkdir(parents=True)
            (root / ".edaios" / "locks" / "r.lock").write_text("{}\n", encoding="utf-8")
            (root / "pom.xml").write_text("<project/>\n", encoding="utf-8")

            files = surface.tracked_files(root)
            self.assertIsNotNone(files)
            names = {path.name for path in files}
            self.assertIn("ko.md", names)
            self.assertNotIn("pom.xml", names)
            self.assertNotIn("r.lock", names)
            self.assertEqual(structure.versioned_roots(root), {"core"})

    def test_without_git_falls_back_to_filesystem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "anything.txt").write_text("x\n", encoding="utf-8")
            self.assertIsNone(surface.tracked_files(root))
            self.assertIsNone(structure.versioned_roots(root))

    def test_receipt_runtime_keeps_surface_gates_green(self):
        state = ROOT / ".edaios"
        created = not state.exists()
        try:
            from edaios_core_harness import create_evidence_receipt

            create_evidence_receipt(
                ROOT,
                initiative="core-t0",
                feature_run="feature/versioned-surface/run-1",
                actor_id="TEST",
                actor_type="agent",
                core_version=(ROOT / "VERSION").read_text(encoding="utf-8").strip(),
                policy={"id": "demo-policy", "version": "1.0.0",
                        "controls": [{"id": "human-authority"}]},
                base_commit="aaaaaaa",
                head_commit="bbbbbbb",
                evidence=["core/framework/tests/test_versioned_surface.py"],
                sensitivity="T0",
                exit_code=0,
                verdict="passed",
                claim_boundary="local tests only",
                rollback={"target_ref": "aaaaaaa", "steps": ["restore"],
                          "verification": "rerun tests"},
            )
            for script in (
                "tools/validation/baseline_surface_check.py",
                "tools/validation/monorepo_structure_check.py",
            ):
                result = subprocess.run(
                    [sys.executable, str(ROOT / script), str(ROOT)],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, f"{script}: {result.stdout}")
        finally:
            if created and state.exists():
                shutil.rmtree(state)


if __name__ == "__main__":
    unittest.main()
