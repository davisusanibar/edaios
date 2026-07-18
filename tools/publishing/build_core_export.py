#!/usr/bin/env python3
"""Materializa el bundle Foundation + Core desde export-manifest.json."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


FIXED_TIMESTAMP = (2026, 7, 16, 0, 0, 0)
SKIP_NAMES = {"__pycache__", ".pytest_cache", "build", "dist"}


class ExportError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _safe_walk(root: Path):
    if root.is_symlink() or not root.is_dir():
        raise ExportError(f"tree ausente o symlink: {root}")
    for entry in sorted(root.iterdir()):
        if entry.name in SKIP_NAMES or entry.name.endswith(".egg-info"):
            continue
        if entry.is_symlink():
            raise ExportError(f"symlink no permitido en export: {entry}")
        if entry.is_dir():
            yield from _safe_walk(entry)
        elif entry.is_file() and entry.suffix != ".pyc":
            yield entry


def _ignored_files(root: Path) -> set[str]:
    if not (root / ".git").exists():
        return set()
    result = subprocess.run(
        [
            "git", "-C", str(root), "ls-files", "--others", "--ignored",
            "--exclude-standard", "-z",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise ExportError(
            "no se pudo resolver archivos ignorados: "
            + result.stderr.decode("utf-8", errors="replace").strip()
        )
    return {
        value.decode("utf-8", errors="strict")
        for value in result.stdout.split(b"\0")
        if value
    }


def _safe_root_directory(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ExportError("root_directory inválido")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1 or path.parts[0] in {".", ".."}:
        raise ExportError(f"root_directory inseguro: {value!r}")
    return path.as_posix()


def _safe_target(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ExportError(f"target inválido: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.name in {"", ".", ".."}:
        raise ExportError(f"target inseguro: {value!r}")
    return path.as_posix()


def _atomic_write(path: Path, content: bytes) -> None:
    if path.is_symlink():
        raise ExportError(f"output symlink no permitido: {path}")
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def collect_entries(root: Path, manifest: dict) -> dict[str, bytes]:
    root = root.resolve()
    entries: dict[str, bytes] = {}
    ignored = _ignored_files(root)

    def add(source: Path, target: str) -> None:
        if source.is_symlink() or not source.is_file() or not _inside(root, source):
            raise ExportError(f"source no resoluble o fuera del root: {source}")
        source_relative = source.relative_to(root).as_posix()
        if source_relative in ignored:
            raise ExportError(f"source ignorado por Git no permitido: {source_relative}")
        normalized = _safe_target(target)
        content = source.read_bytes()
        if normalized in entries and entries[normalized] != content:
            raise ExportError(f"colisión de target: {normalized}")
        entries[normalized] = content

    manifest_path = root / "core/framework/core/export-manifest.json"
    add(manifest_path, "core-export-manifest.json")
    for row in manifest.get("files", []):
        add(root / row["source"], row["target"])
    for row in manifest.get("trees", []):
        source_root = root / row["source"]
        if source_root.is_symlink() or not _inside(root, source_root):
            raise ExportError(f"tree fuera del root o symlink: {source_root}")
        patterns = row.get("include", ["**/*"])
        for source in _safe_walk(source_root):
            relative = source.relative_to(source_root).as_posix()
            if any(
                pattern == "**/*"
                or fnmatch.fnmatch(relative, pattern)
                or Path(relative).match(pattern)
                or (
                    pattern.startswith("**/")
                    and fnmatch.fnmatch(relative, pattern.removeprefix("**/"))
                )
                for pattern in patterns
            ):
                add(source, (Path(row["target"]) / relative).as_posix())
    framework = root / "core/framework"
    for source_text in manifest.get("python_source_roots", []):
        source_root = root / source_text
        if source_root.is_symlink() or not _inside(root, source_root):
            raise ExportError(f"python source root fuera del repo: {source_text}")
        try:
            target_root = source_root.relative_to(framework)
        except ValueError as exc:
            raise ExportError(f"python source root fuera de framework: {source_text}") from exc
        for source in _safe_walk(source_root):
            add(
                source,
                (
                    Path("core/framework")
                    / target_root
                    / source.relative_to(source_root)
                ).as_posix(),
            )
    if not entries:
        raise ExportError("export manifest no produjo archivos")
    return entries


def build_export(root: Path, output: Path) -> dict[str, str]:
    root = root.resolve()
    manifest = json.loads(
        (root / "core/framework/core/export-manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("schema") != "edaios.core-export/v1":
        raise ExportError("schema de export no soportado")
    root_directory = _safe_root_directory(manifest.get("root_directory"))
    entries = collect_entries(root, manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise ExportError(f"output symlink no permitido: {output}")
    fd, name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for relative, content in sorted(entries.items()):
                info = zipfile.ZipInfo(
                    f"{root_directory}/{relative}",
                    FIXED_TIMESTAMP,
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, content)
        os.replace(temporary, output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    digest = sha256_file(output)
    checksum = output.with_suffix(output.suffix + ".sha256")
    _atomic_write(checksum, f"{digest}  {output.name}\n".encode("utf-8"))
    return {
        "archive": str(output),
        "sha256": digest,
        "checksum": str(checksum),
        "root_directory": root_directory,
        "files": str(len(entries)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = build_export(Path(args.root), Path(args.output))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ExportError) as exc:
        print(f"[core-export] FAIL: {exc}")
        return 1
    print(
        f"[core-export] OK: {result['files']} archivos · "
        f"sha256:{result['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
