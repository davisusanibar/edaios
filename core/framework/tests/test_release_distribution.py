"""Contratos de regresion para wheel hermetico y export reproducible."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


exporter = load_module(
    "edaios_core_export_test",
    "tools/publishing/build_core_export.py",
)
build_backend = load_module(
    "edaios_build_backend_test",
    "core/framework/edaios_build_backend.py",
)
distribution = load_module(
    "edaios_core_distribution_test",
    "tools/validation/core_distribution_check.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseDistributionTests(unittest.TestCase):
    def test_core_export_is_reproducible_and_contains_minimum_surface(self):
        manifest = json.loads(
            (ROOT / "core/framework/core/export-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            first = directory / "first.zip"
            second = directory / "second.zip"

            first_report = exporter.build_export(ROOT, first)
            second_report = exporter.build_export(ROOT, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first_report["sha256"], second_report["sha256"])
            self.assertEqual(first_report["sha256"], sha256(first))
            self.assertEqual(
                first.with_suffix(".zip.sha256").read_text(encoding="utf-8"),
                f"{first_report['sha256']}  first.zip\n",
            )

            root = manifest["root_directory"].rstrip("/") + "/"
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
            for relative in (
                "README.md",
                "AGENTS.md",
                "VERSION",
                ".specify/release.json",
                "core-export-manifest.json",
                "edaios.lock.json",
                "repositories.json",
                "core/foundation/FOUNDATION_INDEX.md",
                "core/framework/README.md",
                "core/framework/AGENTS.md",
                "core/framework/LICENSE",
                "core/framework/CHANGELOG.md",
                "core/framework/pyproject.toml",
                "core/framework/edaios_build_backend.py",
                "core/framework/core/export-manifest.json",
                "core/framework/core/templates/initiative/federation-mounts.json",
                "governance/archive/adr/ADR-0010-reproducible-release-and-canonical-cutover.md",
                "governance/ADR-0011-local-working-memory-and-derived-indexes.md",
                "governance/archive/adr/ADR-0012-day-zero-baseline-and-new-genealogy.md",
                "core/framework/core/docs/AGENT_WORKING_MEMORY.md",
                "core/framework/modules/harness-core/src/edaios_core_harness/cli.py",
                "core/framework/modules/conformance-core/src/edaios_conformance/schemas.py",
                "core/framework/extensions/memory-adapter/engram/adapter.json",
            ):
                self.assertIn(root + relative, names)
            self.assertFalse(any("/.git/" in name for name in names))
            self.assertNotIn(root + "bitbucket-pipelines.yml", names)
            self.assertNotIn(
                root + "core/framework/core/docs/MIGRATION_2_TO_3.md", names
            )
            self.assertFalse(
                any("__pycache__" in name or name.endswith(".pyc") for name in names)
            )
            extracted = directory / "extracted"
            with zipfile.ZipFile(first) as archive:
                archive.extractall(extracted)
            export_root = extracted / manifest["root_directory"]
            self.assertEqual(
                (export_root / "README.md").read_bytes(),
                (ROOT / "core/framework/README.md").read_bytes(),
            )
            self.assertEqual(
                (export_root / "AGENTS.md").read_bytes(),
                (ROOT / "core/framework/AGENTS.md").read_bytes(),
            )
            distribution.verify_export_topology(
                export_root, manifest["version"]
            )

    def test_core_export_rejects_unsafe_root_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            manifest_path = workspace / "core/framework/core/export-manifest.json"
            manifest_path.parent.mkdir(parents=True)
            source = workspace / "source.txt"
            source.write_text("safe\n", encoding="utf-8")
            manifest_path.write_text(json.dumps({
                "schema": "edaios.core-export/v1",
                "root_directory": "../../escape",
                "files": [{"source": "source.txt", "target": "source.txt"}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(exporter.ExportError, "root_directory"):
                exporter.build_export(workspace, Path(tmp) / "unsafe.zip")

    def test_core_export_rejects_source_outside_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            manifest_path = workspace / "core/framework/core/export-manifest.json"
            manifest_path.parent.mkdir(parents=True)
            outside = Path(tmp) / "outside.txt"
            outside.write_text("not governed\n", encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "edaios.core-export/v1",
                        "root_directory": "bundle",
                        "files": [
                            {"source": "../outside.txt", "target": "outside.txt"}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(exporter.ExportError):
                exporter.build_export(workspace, Path(tmp) / "unsafe.zip")

    def test_core_export_rejects_cross_platform_unsafe_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            manifest_path = workspace / "core/framework/core/export-manifest.json"
            manifest_path.parent.mkdir(parents=True)
            (workspace / "source.txt").write_text("safe\n", encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "edaios.core-export/v1",
                        "root_directory": "bundle",
                        "files": [
                            {"source": "source.txt", "target": "..\\escape.txt"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(exporter.ExportError, "target"):
                exporter.build_export(workspace, Path(tmp) / "unsafe.zip")

    def test_core_export_rejects_symlink_in_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            manifest_path = workspace / "core/framework/core/export-manifest.json"
            manifest_path.parent.mkdir(parents=True)
            source = workspace / "governed"
            source.mkdir()
            (source / "real.txt").write_text("governed\n", encoding="utf-8")
            link = source / "alias.txt"
            try:
                link.symlink_to(source / "real.txt")
            except OSError as exc:
                self.skipTest(f"symlinks no disponibles: {exc}")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "edaios.core-export/v1",
                        "root_directory": "bundle",
                        "trees": [
                            {
                                "source": "governed",
                                "target": "governed",
                                "include": ["**/*"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(exporter.ExportError):
                exporter.build_export(workspace, Path(tmp) / "unsafe.zip")

    def test_pep517_backend_is_hermetic_and_reproducible(self):
        config = tomllib.loads(
            (ROOT / "core/framework/pyproject.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(config["build-system"]["requires"], [])
        self.assertEqual(
            config["build-system"]["build-backend"], "edaios_build_backend"
        )
        self.assertEqual(config["build-system"]["backend-path"], ["."])
        self.assertEqual(build_backend.get_requires_for_build_wheel(), [])
        self.assertEqual(config["project"]["requires-python"], ">=3.11,<3.14")

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            first_dir = directory / "first"
            second_dir = directory / "second"
            first_name = build_backend.build_wheel(str(first_dir))
            second_name = build_backend.build_wheel(str(second_dir))
            first = first_dir / first_name
            second = second_dir / second_name

            self.assertEqual(first_name, second_name)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
                metadata_name = next(
                    name for name in names if name.endswith(".dist-info/METADATA")
                )
                metadata = archive.read(metadata_name).decode("utf-8")
            version = config["project"]["version"]
            self.assertIn(f"Version: {version}\n", metadata)
            self.assertIn("edaios_core/__init__.py", names)
            self.assertIn("edaios_core_harness/cli.py", names)
            self.assertIn("edaios_memory_adapter/engram.py", names)
            self.assertTrue(
                any(name.endswith(".dist-info/entry_points.txt") for name in names)
            )
            self.assertTrue(any(name.endswith(".dist-info/RECORD") for name in names))
            self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))

    def test_pep517_backend_excludes_undeclared_package_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "framework"
            shutil.copytree(ROOT / "core/framework", project)
            package = project / "modules/ess-core/src/edaios_core"
            (package / ".env").write_text("SECRET=not-for-wheel\n", encoding="utf-8")
            cache = package / "__pycache__"
            cache.mkdir(exist_ok=True)
            (cache / "secret.pyc").write_bytes(b"not reproducible")
            # Load the copied backend so its ROOT points at the adversarial tree.
            spec = importlib.util.spec_from_file_location(
                "edaios_build_backend_temp", project / "edaios_build_backend.py"
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            isolated_backend = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(isolated_backend)
            output = Path(tmp) / "wheel"
            wheel = output / isolated_backend.build_wheel(str(output))
            with zipfile.ZipFile(wheel) as archive:
                names = set(archive.namelist())
            self.assertFalse(any(name.endswith(".env") for name in names))
            self.assertFalse(
                any("__pycache__" in name or name.endswith(".pyc") for name in names)
            )
            materials = distribution.source_materials(ROOT, project)
            expected = {
                path.relative_to(project.resolve()).as_posix()
                for path in isolated_backend.selected_source_files().values()
            } | {"pyproject.toml", "edaios_build_backend.py", "LICENSE"}
            self.assertEqual(set(materials), expected)
            self.assertFalse(any(path.endswith(".env") for path in materials))


if __name__ == "__main__":
    unittest.main()
