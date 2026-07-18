#!/usr/bin/env python3
"""Construye un wheel reproducible con stdlib, lo instala y prueba la API."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SOURCE_ROOTS = (
    "modules/ess-core/src",
    "modules/harness-core/src",
    "modules/ekg-core/src",
    "modules/query-engine/src",
    "modules/sdk-consumption/src",
    "modules/conformance-core/src",
    "modules/supply-chain-core/src",
    "extensions/sdd-adapter/src",
    "extensions/memory-adapter/src",
)


SKIP_PARTS = {"__pycache__", ".pytest_cache", "build", "dist"}


def safe_files(root: Path):
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"source root ausente o symlink: {root}")
    for entry in sorted(root.iterdir()):
        if entry.name in SKIP_PARTS or entry.name.endswith(".egg-info"):
            continue
        if entry.is_symlink():
            raise RuntimeError(f"symlink no permitido en distribución: {entry}")
        if entry.is_dir():
            yield from safe_files(entry)
        elif entry.is_file() and entry.suffix != ".pyc":
            yield entry


def copy_project(source: Path, target: Path) -> None:
    target.mkdir(parents=True)
    for path in safe_files(source):
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def build_pep517_wheel(project: Path, output: Path) -> Path:
    output.mkdir(parents=True)
    env = dict(
        os.environ,
        SOURCE_DATE_EPOCH="1784160000",
        PYTHONHASHSEED="0",
        PIP_NO_INDEX="1",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(output),
            str(project),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    if result.returncode:
        raise RuntimeError("PEP 517 wheel falló:\n" + result.stdout)
    wheels = sorted(output.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"PEP 517 produjo {len(wheels)} wheels")
    return wheels[0]


def load_build_backend(project: Path):
    path = project / "edaios_build_backend.py"
    spec = importlib.util.spec_from_file_location(
        f"edaios_build_backend_{hashlib.sha256(str(project).encode()).hexdigest()[:12]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se pudo cargar backend PEP 517: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_materials(_root: Path, project: Path) -> dict[str, Path]:
    """Materiales exactos que influyen en los bytes del wheel."""
    project = project.resolve()
    backend = load_build_backend(project)
    materials: dict[str, Path] = {}
    for source in backend.selected_source_files().values():
        relative = source.relative_to(project).as_posix()
        materials[relative] = source
    for relative in ("pyproject.toml", "edaios_build_backend.py", "LICENSE"):
        path = project / relative
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"material del wheel ausente o symlink: {relative}")
        materials[relative] = path
    return materials


def load_exporter(root: Path):
    path = root / "tools/publishing/build_core_export.py"
    spec = importlib.util.spec_from_file_location("edaios_core_export", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("no se pudo cargar build_core_export.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_export_topology(export_root: Path, version: str) -> None:
    """Comprueba que locks y paths del bundle resuelvan dentro del export."""
    lock = json.loads((export_root / "edaios.lock.json").read_text(encoding="utf-8"))
    repositories = json.loads(
        (export_root / "repositories.json").read_text(encoding="utf-8")
    )
    if lock.get("version") != version or repositories.get("version") != version:
        raise RuntimeError("lock/repositories exportados divergen de VERSION")
    if (
        lock.get("component_authority") != "ADR-0006"
        or lock.get("release_authority") != "ADR-0013"
    ):
        raise RuntimeError("lock exportado mezcla autoridad de componente y release")
    declared = [
        ("repositories.modules.path", row.get("path"))
        for row in repositories.get("modules", [])
    ] + [
        ("lock.components.source_path", row.get("source_path"))
        for row in lock.get("components", [])
    ]
    if not declared:
        raise RuntimeError("export sin componentes declarados")
    for label, value in declared:
        if not isinstance(value, str) or not value or "\\" in value:
            raise RuntimeError(f"{label} inválido: {value!r}")
        relative = PurePosixPath(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"{label} inseguro: {value!r}")
        target = export_root.joinpath(*relative.parts)
        if target.is_symlink() or not target.is_dir():
            raise RuntimeError(f"{label} no resuelve a directorio: {value}")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    project = root / "core/framework"
    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        if not SEMVER.fullmatch(version):
            raise RuntimeError(f"VERSION no es semver: {version or '<vacio>'}")
        pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject, re.MULTILINE)
        if not match or match.group(1) != version:
            raise RuntimeError("pyproject.toml no coincide con VERSION")
        export = json.loads(
            (project / "core/export-manifest.json").read_text(encoding="utf-8")
        )
        if export.get("version") != version:
            raise RuntimeError("export-manifest.json no coincide con VERSION")
        if (
            export.get("component_authority") != "ADR-0006"
            or export.get("release_authority") != "ADR-0013"
        ):
            raise RuntimeError("export no separa autoridad de componente y release")
        lock = json.loads((root / "edaios.lock.json").read_text(encoding="utf-8"))
        repositories = json.loads((root / "repositories.json").read_text(encoding="utf-8"))
        if lock.get("version") != version or repositories.get("version") != version:
            raise RuntimeError("lock/repositories no coinciden con VERSION")
        project_config = tomllib.loads(pyproject)
        if project_config["project"].get("requires-python") != ">=3.11,<3.14":
            raise RuntimeError("Core 3 debe declarar requires-python >=3.11,<3.14")
        configured_roots = set(project_config["tool"]["edaios-build"]["source-roots"])
        if configured_roots != set(SOURCE_ROOTS):
            raise RuntimeError("pyproject source roots difieren del builder")
        exported_roots = set(export.get("python_source_roots", []))
        expected_exports = {
            "core/framework/" + relative.removesuffix("/src")
            for relative in SOURCE_ROOTS
        }
        if exported_roots != expected_exports:
            raise RuntimeError("export manifest source roots difieren del builder")
        supply_source = project / "modules/supply-chain-core/src"
        sys.path.insert(0, str(supply_source))
        from edaios_supply_chain import (  # type: ignore
            build_supply_chain_artifacts,
            sha256_file,
            verify_supply_chain_artifacts,
        )
        with tempfile.TemporaryDirectory(prefix="edaios-core-wheel-") as tmp:
            tmp_path = Path(tmp)
            first_project = tmp_path / "project-first"
            second_project = tmp_path / "project-second"
            copy_project(project, first_project)
            copy_project(project, second_project)
            wheel = build_pep517_wheel(first_project, tmp_path / "wheel-first")
            comparison = build_pep517_wheel(second_project, tmp_path / "wheel-second")
            if sha256_file(wheel) != sha256_file(comparison):
                raise RuntimeError("wheel PEP 517 no es reproducible entre dos builds limpios")
            materials = source_materials(root, project)
            artifacts = build_supply_chain_artifacts(
                wheel,
                tmp_path / "supply-chain",
                version=version,
                materials=materials,
            )
            verification = verify_supply_chain_artifacts(
                artifacts["subject"],
                artifacts["checksum"],
                artifacts["sbom"],
                artifacts["provenance"],
                materials=materials,
            )
            if verification.get("status") != "ok":
                raise RuntimeError("supply chain local no verificable")
            target = tmp_path / "installed"
            result = subprocess.run(
                [
                    sys.executable, "-m", "pip", "install", str(wheel),
                    "--no-deps", "--target", str(target),
                ],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                env=dict(
                    os.environ,
                    PIP_NO_INDEX="1",
                    PIP_DISABLE_PIP_VERSION_CHECK="1",
                ),
            )
            if result.returncode:
                raise RuntimeError(result.stdout)
            env = dict(os.environ, PYTHONPATH=str(target))
            entrypoint = target / "bin/edaios-core"
            if not entrypoint.is_file() or not os.access(entrypoint, os.X_OK):
                raise RuntimeError("console script instalado no es ejecutable")
            success = subprocess.run(
                [str(entrypoint), "kos", "list", "--root", str(root)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, cwd=tmp_path,
            )
            if success.returncode != 0:
                raise RuntimeError("console script instalado falló:\n" + success.stderr)
            success_payload = json.loads(success.stdout)
            if success_payload.get("schema") != "edaios.cli-output/v1":
                raise RuntimeError("console script instalado no emitió envelope v1")
            blocked = subprocess.run(
                [
                    str(entrypoint), "query", "impact", "--root", str(root),
                    "--node", "NO-EXISTE",
                ],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, cwd=tmp_path,
            )
            if blocked.returncode != 2:
                raise RuntimeError("console script instalado no preservó exit 2")
            blocked_payload = json.loads(blocked.stderr)
            if blocked_payload.get("status") != "blocked":
                raise RuntimeError("console script instalado no emitió bloqueo contractual")
            root_literal = json.dumps(str(root))
            code = f"""
import contextlib
import io
import json
from importlib.metadata import distribution, version
from importlib.resources import files
import edaios_core, edaios_core_harness, edaios_ekg, edaios_query
import edaios_sdk_consumption, edaios_conformance
import edaios_supply_chain, edaios_sdd_adapter, edaios_memory_adapter
from edaios_core_harness import CoreHarness
from edaios_core_harness.cli import main
from edaios_query import QueryEngine

assert version("edaios-core") == {version!r}
assert all(p.__version__ == {version!r} for p in (
    edaios_core, edaios_core_harness, edaios_ekg, edaios_query,
    edaios_sdk_consumption, edaios_conformance,
    edaios_supply_chain, edaios_sdd_adapter, edaios_memory_adapter,
))
scripts = {{item.name: item.value for item in distribution("edaios-core").entry_points}}
assert scripts["edaios-core"] == "edaios_core_harness.cli:main"
assert files("edaios_conformance").joinpath(
    "resources/schemas/cli-output.json"
).is_file()
assert files("edaios_conformance").joinpath(
    "resources/schemas/federation-mounts.json"
).is_file()
assert files("edaios_conformance").joinpath(
    "resources/schemas/memory-record.json"
).is_file()
assert CoreHarness().validate()["status"] == "ok"
assert QueryEngine.from_graph({{
    "nodes": [], "edges": [], "entity_types": {{}}, "relationship_types": {{}}
}}).find() == []
stdout = io.StringIO()
with contextlib.redirect_stdout(stdout):
    assert main(["kos", "list", "--root", {root_literal}]) == 0
payload = json.loads(stdout.getvalue())
assert payload["schema"] == "edaios.cli-output/v1"
assert payload["status"] == "ok"
stderr = io.StringIO()
with contextlib.redirect_stderr(stderr):
    assert main(["query", "impact", "--root", {root_literal}, "--node", "NO-EXISTE"]) == 2
blocked = json.loads(stderr.getvalue())
assert blocked["schema"] == "edaios.cli-output/v1"
assert blocked["status"] == "blocked"
"""
            subprocess.run(
                [sys.executable, "-s", "-c", code],
                check=True, env=env, cwd=tmp_path,
            )
            exporter = load_exporter(root)
            first_export = tmp_path / f"edaios-core-{version}-first.zip"
            second_export = tmp_path / f"edaios-core-{version}-second.zip"
            first_report = exporter.build_export(root, first_export)
            second_report = exporter.build_export(root, second_export)
            if first_report["sha256"] != second_report["sha256"]:
                raise RuntimeError("export Foundation + Core no es reproducible")
            extracted = tmp_path / "exported"
            with zipfile.ZipFile(first_export) as archive:
                for info in archive.infolist():
                    name = PurePosixPath(info.filename)
                    mode = (info.external_attr >> 16) & 0o170000
                    if (
                        name.is_absolute()
                        or ".." in name.parts
                        or "\\" in info.filename
                        or mode == 0o120000
                    ):
                        raise RuntimeError(f"entrada insegura en export: {info.filename}")
                    target_path = (extracted / Path(*name.parts)).resolve(strict=False)
                    try:
                        target_path.relative_to(extracted.resolve())
                    except ValueError as exc:
                        raise RuntimeError(
                            f"entrada fuera del destino: {info.filename}"
                        ) from exc
                archive.extractall(extracted)
            export_root = extracted / export["root_directory"]
            if any(path.name == ".git" for path in export_root.rglob("*")):
                raise RuntimeError("export contiene metadata .git")
            for required in (
                "README.md",
                "AGENTS.md",
                "VERSION",
                "edaios.lock.json",
                "repositories.json",
                "core/foundation/FOUNDATION_INDEX.md",
                "core/framework/README.md",
                "core/framework/AGENTS.md",
                "core/framework/LICENSE",
                "core/framework/CHANGELOG.md",
                "core/framework/pyproject.toml",
                "core/framework/edaios_build_backend.py",
                "governance/ADR_CATALOG.md",
                "core-export-manifest.json",
                "core/framework/core/export-manifest.json",
                "core/framework/core/templates/initiative/federation-mounts.json",
            ):
                if not (export_root / required).is_file():
                    raise RuntimeError(f"export incompleto: {required}")
            verify_export_topology(export_root, version)
            export_project = export_root / "core/framework"
            exported_wheel = build_pep517_wheel(
                export_project, tmp_path / "wheel-from-export"
            )
            if sha256_file(exported_wheel) != sha256_file(wheel):
                raise RuntimeError(
                    "wheel reconstruido desde export difiere del wheel canónico"
                )
            export_sources = [
                export_project / relative
                for relative in (
                    "modules/ess-core/src",
                    "modules/harness-core/src",
                    "modules/ekg-core/src",
                    "modules/query-engine/src",
                    "modules/sdk-consumption/src",
                    "modules/conformance-core/src",
                    "modules/supply-chain-core/src",
                    "extensions/sdd-adapter/src",
                    "extensions/memory-adapter/src",
                )
            ]
            export_env = dict(os.environ, PYTHONPATH=os.pathsep.join(map(str, export_sources)))
            subprocess.run(
                [
                    sys.executable,
                    "-s",
                    "-c",
                    (
                        "from edaios_conformance import SchemaRegistry;"
                        "from edaios_core_harness import CoreHarness;"
                        "assert 'cli-output' in SchemaRegistry().names();"
                        "assert CoreHarness().validate()['status']=='ok'"
                    ),
                ],
                check=True,
                env=export_env,
                cwd=export_project,
            )
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"[core-distribution] FAIL: {exc}")
        return 1
    print(
        f"[core-distribution] OK: wheel PEP 517 y export reproducibles {version}, "
        "checksum, SBOM y provenance local verificables"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
