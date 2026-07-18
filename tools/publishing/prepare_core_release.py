#!/usr/bin/env python3
"""Prepara el manifest determinista de un candidato de release de EDAIOS Core.

Este comando no crea commits, tags, releases ni receipts. La huella cubre todos
los archivos tracked y untracked no ignorados por Git, excepto el propio
manifest para evitar una referencia circular.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


# Defaults are fixture-friendly only. The CLI requires --manifest and release
# contracts are supplied explicitly to the checker; no live feature is selected
# by a path hardcoded in tooling.
MANIFEST_RELATIVE = Path("release/core-release-candidate.json")
RELEASE_POLICY_RELATIVE = Path("release/core-release-policy.json")
RELEASE_AUTHORITY_RELATIVE = Path("release/core-release-authority.json")
CUTOVER_TARGET_RELATIVE = Path("release/git-cutover-target.json")
MANIFEST_SCHEMA = "edaios.core-release-candidate/v2"
INPUT_SCHEMA = "edaios.governed-inputs/v1"
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
HEX_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")
CLAIM_BOUNDARY = (
    "Candidato local reproducible; no equivale a commit sellado, tag, "
    "publicacion, firma externa ni aprobacion humana."
)
FINAL_REQUIREMENTS = [
    "clean-commit",
    "evidence-receipt-v2",
    "human-approval-receipt",
    "remote-cutover-receipt",
]
VALIDATION_COMMANDS = [
    "./scripts/test.sh",
    "./scripts/validate.sh",
    "./scripts/ci.sh",
]


class ReleasePreparationError(RuntimeError):
    """El candidato no puede prepararse sin debilitar el contrato."""


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise ReleasePreparationError(f"git no disponible: {exc}") from exc
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ReleasePreparationError(
            f"git {' '.join(args)} fallo: {detail or 'sin detalle'}"
        )
    return result


def repository_root(root: str | Path) -> Path:
    candidate = Path(root).resolve()
    if not candidate.is_dir():
        raise ReleasePreparationError(f"root no existe: {candidate}")
    discovered = _git(candidate, "rev-parse", "--show-toplevel").stdout.decode(
        "utf-8", errors="strict"
    ).strip()
    resolved = Path(discovered).resolve()
    if resolved != candidate:
        raise ReleasePreparationError(
            f"root debe ser la raiz Git: recibido={candidate} real={resolved}"
        )
    return resolved


def current_head(root: Path) -> str:
    value = _git(root, "rev-parse", "HEAD").stdout.decode("ascii").strip()
    if not HEX_COMMIT.fullmatch(value):
        raise ReleasePreparationError(f"HEAD no resoluble o no canonico: {value}")
    return value


def tree_for_ref(root: Path, ref: str = "HEAD") -> str:
    value = _git(root, "rev-parse", f"{ref}^{{tree}}").stdout.decode("ascii").strip()
    if not HEX_COMMIT.fullmatch(value):
        raise ReleasePreparationError(f"tree de HEAD no resoluble: {value}")
    return value


def current_tree(root: Path) -> str:
    return tree_for_ref(root, "HEAD")


def current_branch(root: Path) -> str | None:
    value = _git(root, "branch", "--show-current").stdout.decode("utf-8").strip()
    return value or None


def core_version(root: Path) -> str:
    path = root / "VERSION"
    if path.is_symlink() or not path.is_file():
        raise ReleasePreparationError("VERSION ausente o symlink")
    value = path.read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(value):
        raise ReleasePreparationError(f"VERSION no es SemVer estable: {value or '<vacio>'}")
    return value


def _relative_manifest(manifest_relative: str | Path) -> str:
    path = Path(manifest_relative)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ReleasePreparationError(f"path de manifest inseguro: {path}")
    return path.as_posix()


def governed_paths(
    root: Path, manifest_relative: str | Path = MANIFEST_RELATIVE
) -> list[str]:
    excluded = _relative_manifest(manifest_relative)
    raw = _git(
        root,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ).stdout
    try:
        paths = sorted(
            {
                value.decode("utf-8", errors="strict")
                for value in raw.split(b"\0")
                if value
            }
        )
    except UnicodeDecodeError as exc:
        raise ReleasePreparationError("Git contiene un path no UTF-8") from exc
    return [path for path in paths if path != excluded]


def governed_input_digest(
    root: Path, manifest_relative: str | Path = MANIFEST_RELATIVE
) -> dict[str, Any]:
    """Calcula una huella estable de paths, modos, tamaños y contenidos."""
    digest = hashlib.sha256()
    digest.update((INPUT_SCHEMA + "\0").encode("ascii"))
    count = 0
    deleted = 0
    for relative in governed_paths(root, manifest_relative):
        path = root / relative
        row: dict[str, Any]
        if not path.exists() and not path.is_symlink():
            row = {"path": relative, "state": "deleted"}
            deleted += 1
        else:
            if path.is_symlink():
                raise ReleasePreparationError(
                    f"symlink no permitido entre inputs gobernados: {relative}"
                )
            if not path.is_file():
                raise ReleasePreparationError(
                    f"input gobernado no es archivo regular: {relative}"
                )
            content = path.read_bytes()
            mode = "100755" if os.access(path, os.X_OK) else "100644"
            row = {
                "path": relative,
                "state": "present",
                "mode": mode,
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        digest.update(
            json.dumps(
                row, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        )
        digest.update(b"\n")
        count += 1
    return {
        "schema": INPUT_SCHEMA,
        "algorithm": "SHA-256",
        "digest": digest.hexdigest(),
        "file_count": count,
        "deleted_count": deleted,
        "scope": "git tracked + untracked no ignorados; archivos regulares",
        "excluded": [_relative_manifest(manifest_relative)],
    }


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ReleasePreparationError(f"no se pudo cargar {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _artifact_row(kind: str, path: Path) -> dict[str, Any]:
    content = path.read_bytes()
    return {
        "kind": kind,
        "name": path.name,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size": len(content),
    }


def release_artifacts(root: Path, version: str) -> dict[str, Any]:
    """Construye artefactos efímeros y retorna solo su identidad durable."""
    distribution = _load_module(
        "edaios_release_distribution",
        root / "tools/validation/core_distribution_check.py",
    )
    project = root / "core/framework"
    supply_source = project / "modules/supply-chain-core/src"
    sys.path.insert(0, str(supply_source))
    try:
        from edaios_supply_chain import (  # type: ignore
            build_supply_chain_artifacts,
            verify_supply_chain_artifacts,
        )
    except ImportError as exc:
        raise ReleasePreparationError("supply-chain-core no importable") from exc
    with tempfile.TemporaryDirectory(prefix="edaios-release-candidate-") as tmp:
        temporary = Path(tmp)
        isolated = temporary / "project"
        distribution.copy_project(project, isolated)
        wheel = distribution.build_pep517_wheel(isolated, temporary / "wheel")
        materials = distribution.source_materials(root, project)
        sidecars = build_supply_chain_artifacts(
            wheel,
            temporary / "supply-chain",
            version=version,
            materials=materials,
        )
        verification = verify_supply_chain_artifacts(
            sidecars["subject"],
            sidecars["checksum"],
            sidecars["sbom"],
            sidecars["provenance"],
            materials=materials,
        )
        if verification.get("status") != "ok":
            raise ReleasePreparationError("sidecars del wheel no son verificables")
        exporter = distribution.load_exporter(root)
        export_path = temporary / f"edaios-core-{version}.zip"
        exporter.build_export(root, export_path)
        export_checksum = export_path.with_suffix(export_path.suffix + ".sha256")
        rows = [
            _artifact_row("wheel", wheel),
            _artifact_row("wheel-checksum", sidecars["checksum"]),
            _artifact_row("sbom", sidecars["sbom"]),
            _artifact_row("provenance", sidecars["provenance"]),
            _artifact_row("core-export", export_path),
            _artifact_row("core-export-checksum", export_checksum),
        ]
    rows.sort(key=lambda row: (row["kind"], row["name"]))
    canonical = json.dumps(
        rows, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "schema": "edaios.release-artifacts/v1",
        "digest": hashlib.sha256(canonical).hexdigest(),
        "items": rows,
    }


def governed_worktree_dirty(
    root: Path, manifest_relative: str | Path = MANIFEST_RELATIVE
) -> bool:
    excluded = _relative_manifest(manifest_relative)
    result = _git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        ".",
        f":(exclude){excluded}",
    )
    return bool(result.stdout)


def full_worktree_clean(root: Path) -> bool:
    return not bool(
        _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout
    )


def build_manifest(
    root: str | Path,
    manifest_relative: str | Path = MANIFEST_RELATIVE,
    *,
    artifact_builder: Callable[[Path, str], dict[str, Any]] = release_artifacts,
) -> dict[str, Any]:
    workspace = repository_root(root)
    version = core_version(workspace)
    return {
        "schema": MANIFEST_SCHEMA,
        "component": "edaios-core",
        "version": version,
        "status": "prepared",
        "base_head": current_head(workspace),
        "base_tree": current_tree(workspace),
        "branch": current_branch(workspace),
        "governed_inputs": governed_input_digest(workspace, manifest_relative),
        "artifacts": artifact_builder(workspace, version),
        "validation_commands": VALIDATION_COMMANDS,
        "final_seal": {
            "required": True,
            "requirements": FINAL_REQUIREMENTS,
            "present": False,
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }


def _safe_target(root: Path, manifest_relative: str | Path) -> Path:
    relative = Path(_relative_manifest(manifest_relative))
    target = root / relative
    parent = target.parent
    current = root
    for part in relative.parent.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ReleasePreparationError(f"parent symlink no permitido: {current}")
    parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        raise ReleasePreparationError(f"manifest no puede ser symlink: {target}")
    return target


def write_manifest(
    root: str | Path,
    manifest_relative: str | Path = MANIFEST_RELATIVE,
    *,
    artifact_builder: Callable[[Path, str], dict[str, Any]] = release_artifacts,
) -> tuple[Path, dict[str, Any]]:
    workspace = repository_root(root)
    manifest = build_manifest(
        workspace, manifest_relative, artifact_builder=artifact_builder
    )
    target = _safe_target(workspace, manifest_relative)
    content = (
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return target, manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--manifest",
        required=True,
        help="path relativo explícito del manifest dentro del repositorio",
    )
    args = parser.parse_args(argv)
    try:
        target, manifest = write_manifest(Path(args.root), args.manifest)
    except (OSError, ValueError, json.JSONDecodeError, ReleasePreparationError) as exc:
        print(f"[core-release-prepare] FAIL: {exc}")
        return 1
    print(
        f"[core-release-prepare] OK: {manifest['version']} · "
        f"{manifest['status']} · {target} · "
        f"sha256:{manifest['governed_inputs']['digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
