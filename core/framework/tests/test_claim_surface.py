from pathlib import Path
import importlib.util
import json
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools/validation/claim_surface_check.py"
SPEC = importlib.util.spec_from_file_location("claim_surface_check", MODULE_PATH)
CLAIM_SURFACE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(CLAIM_SURFACE)


class ClaimSurfaceTests(unittest.TestCase):
    def test_repository_claim_surface_is_resolvable(self):
        self.assertEqual(CLAIM_SURFACE.validate(ROOT), [])

    def test_enforced_claim_without_test_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            source.write_text("claim.json\n", encoding="utf-8")
            target = root / "claim.json"
            target.write_text("{}\n", encoding="utf-8")
            (root / "VERSION").write_text("2.0.0\n", encoding="utf-8")
            manifest = root / "core/framework/core/profiles/claim-surface.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "edaios.claim-surface/v1",
                        "version": "2.0.0",
                        "claims": [
                            {
                                "id": "unsafe-claim",
                                "claim": "claim",
                                "maturity": "enforced",
                                "artifacts": ["claim.json"],
                                "tests": [],
                                "boundary": "local",
                            }
                        ],
                        "documentation_references": [
                            {"source": "source.txt", "target": "claim.json"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.assertIn(
                "unsafe-claim: enforced exige pruebas",
                CLAIM_SURFACE.validate(root),
            )


if __name__ == "__main__":
    unittest.main()
