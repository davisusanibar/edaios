"""Los catálogos ADR/RFC son proyecciones compiladas de sus documentos (ADR-0007)."""

from __future__ import annotations

import importlib.util
import contextlib
import io
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


catalogs = load_module("compile_catalogs", "tools/publishing/compile_catalogs.py")


def write_adr(governance: Path, name: str, *, heading: str, estado: str = "Aceptado") -> None:
    (governance / name).write_text(
        f"# {heading}\n\n**Estado:** {estado}\n**Fecha:** 2026-07-16\n"
        "**Owner:** Principal Architect\n\n## Decisión\n\nx\n",
        encoding="utf-8",
    )


class CatalogProjectionTests(unittest.TestCase):
    def test_catalogs_match_documents(self):
        governance = ROOT / "governance"
        adr_rows = catalogs.collect_adrs(governance)
        rfc_rows = catalogs.collect_rfcs(governance)
        self.assertGreaterEqual(len(adr_rows), 8)
        rendered = catalogs.render_adr_catalog(adr_rows)
        self.assertEqual(
            rendered, (governance / "ADR_CATALOG.md").read_text(encoding="utf-8")
        )
        self.assertEqual(
            catalogs.render_rfc_catalog(rfc_rows),
            (governance / "RFC_CATALOG.md").read_text(encoding="utf-8"),
        )
        counts = next(
            line for line in rendered.splitlines() if line.startswith("**Total:**")
        )
        self.assertIn(f"**Total:** {len(adr_rows)}", counts)

    def test_duplicate_or_divergent_decision_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            governance = Path(tmp)
            write_adr(governance, "ADR-0001-a.md", heading="ADR-0001 — Decisión A")
            write_adr(governance, "ADR-0001-b.md", heading="ADR-0001 — Decisión B")
            with self.assertRaisesRegex(catalogs.CatalogError, "duplicado"):
                catalogs.collect_adrs(governance)
        with tempfile.TemporaryDirectory() as tmp:
            governance = Path(tmp)
            write_adr(
                governance, "ADR-0001-a.md",
                heading="ADR-0001 — Decisión A", estado="Aprobadísimo",
            )
            with self.assertRaisesRegex(catalogs.CatalogError, "dominio"):
                catalogs.collect_adrs(governance)
        with tempfile.TemporaryDirectory() as tmp:
            governance = Path(tmp)
            write_adr(governance, "ADR-0002-x.md", heading="ADR-0001 — Heading ajeno")
            with self.assertRaisesRegex(catalogs.CatalogError, "canónico"):
                catalogs.collect_adrs(governance)

    def test_metadata_must_be_unique_and_live_in_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            governance = Path(tmp)
            (governance / "ADR-0001-a.md").write_text(
                "# ADR-0001 — A\n\n**Estado:** Aceptado\n"
                "**Fecha:** 2026-07-16\n\n## Contexto\n\n"
                "**Owner:** BODY-ONLY\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(catalogs.CatalogError, "fuera de cabecera"):
                catalogs.collect_adrs(governance)
        with tempfile.TemporaryDirectory() as tmp:
            governance = Path(tmp)
            (governance / "ADR-0001-a.md").write_text(
                "# ADR-0001 — A\n\n**Estado:** Aceptado\n"
                "**Fecha:** 2026-07-16\n**Owner:** ONE\n**Owner:** TWO\n"
                "\n## Contexto\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(catalogs.CatalogError, "duplicado"):
                catalogs.collect_adrs(governance)

    def test_filename_and_cli_modes_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            governance = Path(tmp)
            write_adr(
                governance, "ADR-" + "9-no-canonico.md",
                heading="ADR-0009 — No canónico",
            )
            with self.assertRaisesRegex(catalogs.CatalogError, "filename"):
                catalogs.collect_adrs(governance)
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                catalogs.main(["--chek"])
        adr = ROOT / "governance/ADR_CATALOG.md"
        rfc = ROOT / "governance/RFC_CATALOG.md"
        before = (adr.read_bytes(), rfc.read_bytes())
        self.assertEqual(catalogs.main([]), 0)
        self.assertEqual(before, (adr.read_bytes(), rfc.read_bytes()))

    def test_projection_write_is_atomic_per_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, second = root / "a.md", root / "b.md"
            first.write_text("old-a\n")
            second.write_text("old-b\n")
            catalogs._write_projections({first: "new-a\n", second: "new-b\n"})
            self.assertEqual(first.read_text(), "new-a\n")
            self.assertEqual(second.read_text(), "new-b\n")


if __name__ == "__main__":
    unittest.main()
