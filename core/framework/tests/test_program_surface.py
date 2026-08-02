"""Regression: la superficie diaria no contradice el handoff canónico (specs/011, FR-004)."""

from __future__ import annotations

import importlib.util
import json
import shutil
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


class ProgramSurfaceFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = load_module(
            "test_traceability_check_surface", "tools/validation/traceability_check.py"
        )

    def _fixture_root(
        self, surface: str, next_iteration: str = "# NEXT_ITERATION\n\nSin pendientes.\n"
    ) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="edaios-surface-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        (tmp / "program-office/context").mkdir(parents=True)
        (tmp / ".specify").mkdir()
        (tmp / "specs/009-alpha").mkdir(parents=True)
        (tmp / "specs/010-beta").mkdir(parents=True)
        (tmp / ".specify/feature.json").write_text(
            json.dumps(
                {
                    "schema": "edaios.feature-handoff/v3",
                    "baseline_feature": {"id": "A", "feature_directory": "specs/009-alpha"},
                    "last_closed_feature": {"id": "A", "feature_directory": "specs/009-alpha"},
                    "active_feature": None,
                }
            ),
            encoding="utf-8",
        )
        (tmp / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        (tmp / "specs/009-alpha/spec.md").write_text(
            "---\nid: A\nestado: Cerrado\n---\n", encoding="utf-8"
        )
        (tmp / "specs/010-beta/spec.md").write_text(
            "---\nid: B\nestado: Propuesto\n---\n", encoding="utf-8"
        )
        (tmp / "program-office/context/CURRENT_STATE.md").write_text(
            surface, encoding="utf-8"
        )
        (tmp / "program-office/context/NEXT_ITERATION.md").write_text(
            next_iteration, encoding="utf-8"
        )
        return tmp

    def test_stale_surface_fails_closed(self) -> None:
        root = self._fixture_root("# CURRENT_STATE\n\nLa feature 008 cerrada.\n")
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertTrue(
            any("no cita la última feature cerrada" in error for error in errors),
            errors,
        )
        self.assertTrue(any("VERSION vigente" in error for error in errors), errors)

    def test_closure_claim_of_open_feature_fails_closed(self) -> None:
        surface = (
            "# CURRENT_STATE\n\nVersión 9.9.9. Última cerrada: specs/009-alpha.\n"
            "La feature 010 quedó cerrada.\n"
        )
        root = self._fixture_root(surface)
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertTrue(
            any("no cerrada: 010" in error for error in errors),
            errors,
        )

    def test_unresolvable_feature_mention_fails_closed(self) -> None:
        surface = (
            "# CURRENT_STATE\n\nVersión 9.9.9. Última cerrada: specs/009-alpha.\n"
            "Ver specs/099-fantasma para el detalle.\n"
        )
        root = self._fixture_root(surface)
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertTrue(
            any("feature no resoluble: specs/099-fantasma" in error for error in errors),
            errors,
        )

    def test_fresh_surface_passes(self) -> None:
        surface = (
            "# CURRENT_STATE\n\nVersión 9.9.9.\n"
            "Última feature cerrada: specs/009-alpha (feature 009 cerrada).\n"
            "La feature 010 está propuesta en cola: specs/010-beta.\n"
        )
        root = self._fixture_root(surface)
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertEqual(errors, [])

    def test_next_iteration_con_ruta_fantasma_falla(self) -> None:
        fresh = (
            "# CURRENT_STATE\n\nVersión 9.9.9.\n"
            "Última feature cerrada: specs/009-alpha (feature 009 cerrada).\n"
        )
        root = self._fixture_root(
            fresh, "# NEXT_ITERATION\n\nVer specs/099-fantasma.\n"
        )
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertTrue(
            any("NEXT_ITERATION menciona feature no resoluble" in e for e in errors),
            errors,
        )

    def test_next_iteration_cerrada_en_cola_falla(self) -> None:
        # Escape real de specs/017: la 009 (Cerrado) declarada en ejecución,
        # con la oración envuelta en dos líneas como en el archivo real.
        fresh = (
            "# CURRENT_STATE\n\nVersión 9.9.9.\n"
            "Última feature cerrada: specs/009-alpha (feature 009 cerrada).\n"
        )
        stale = (
            "# NEXT_ITERATION\n\nLa feature 009 (reorganización de\n"
            "archivo) está en ejecución como último cierre.\n"
        )
        root = self._fixture_root(fresh, stale)
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertTrue(
            any("en cola o en ejecución una feature cerrada: 009" in e for e in errors),
            errors,
        )

    def test_cierre_falso_envuelto_en_next_iteration_falla(self) -> None:
        # RA-001/RA-002 (review 017): el reclamo de cierre también se normaliza;
        # un cierre falso envuelto en dos líneas no escapa.
        fresh = (
            "# CURRENT_STATE\n\nVersión 9.9.9.\n"
            "Última feature cerrada: specs/009-alpha (feature 009 cerrada).\n"
        )
        stale = (
            "# NEXT_ITERATION\n\nLa feature 010 quedó finalmente\n"
            "cerrada la semana pasada.\n"
        )
        root = self._fixture_root(fresh, stale)
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertTrue(
            any(
                "NEXT_ITERATION reclama como cerrada una feature no cerrada: 010" in e
                for e in errors
            ),
            errors,
        )

    def test_punto_interno_no_corta_la_asociacion(self) -> None:
        # RA-002 (review 017): `.md` y semver no son límite de oración.
        fresh = (
            "# CURRENT_STATE\n\nVersión 9.9.9.\n"
            "Última feature cerrada: specs/009-alpha (feature 009 cerrada).\n"
        )
        stale = (
            "# NEXT_ITERATION\n\nLa feature 009 (ver NOTAS.md y Core 3.1.0)\n"
            "sigue en ejecución.\n"
        )
        root = self._fixture_root(fresh, stale)
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertTrue(
            any("en cola o en ejecución una feature cerrada: 009" in e for e in errors),
            errors,
        )

    def test_prefijo_ambiguo_falla_cerrado(self) -> None:
        # RA-003 (review 017): dos directorios con el mismo número no escapan.
        fresh = (
            "# CURRENT_STATE\n\nVersión 9.9.9.\n"
            "Última feature cerrada: specs/009-alpha (feature 009 cerrada).\n"
        )
        stale = "# NEXT_ITERATION\n\nEn cola: la 013 pendiente.\n"
        root = self._fixture_root(fresh, stale)
        for name, estado in (("013-uno", "Cerrado"), ("013-dos", "Propuesto")):
            directory = root / "specs" / name
            directory.mkdir(parents=True)
            (directory / "spec.md").write_text(
                f"---\nid: X-{name.upper()}\nestado: {estado}\n---\n", encoding="utf-8"
            )
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertTrue(
            any("prefijo numérico de feature ambiguo" in e for e in errors), errors
        )

    def test_vl_en_oracion_de_cola_no_da_falso_positivo(self) -> None:
        fresh = (
            "# CURRENT_STATE\n\nVersión 9.9.9.\n"
            "Última feature cerrada: specs/009-alpha (feature 009 cerrada).\n"
        )
        benign = (
            "# NEXT_ITERATION\n\nEn cola: la review de VL-001 y la feature\n"
            "010 propuesta.\n"
        )
        root = self._fixture_root(fresh, benign)
        errors: list[str] = []
        self.tool.validate_program_surface(root, errors)
        self.assertEqual(errors, [])

    def test_real_corpus_passes(self) -> None:
        errors: list[str] = []
        self.tool.validate_program_surface(ROOT, errors)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
