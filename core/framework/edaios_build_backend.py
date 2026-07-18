"""Backend PEP 517 hermético y determinista de EDAIOS Core.

Vive junto al proyecto para no resolver herramientas de build desde la red.
Solo usa la biblioteca estándar.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import re
import tomllib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXED_TIMESTAMP = (2026, 7, 16, 0, 0, 0)
SKIP_PARTS = {"__pycache__", ".pytest_cache", "build", "dist"}


def _config() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _safe_files(root: Path):
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"source root ausente o symlink: {root}")
    for entry in sorted(root.iterdir()):
        if entry.name in SKIP_PARTS or entry.name.endswith(".egg-info"):
            continue
        if entry.is_symlink():
            raise RuntimeError(f"symlink no permitido en wheel: {entry}")
        if entry.is_dir():
            yield from _safe_files(entry)
        elif entry.is_file() and entry.suffix != ".pyc":
            yield entry


def _distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name)


def _metadata(config: dict) -> tuple[str, str, str, bytes]:
    project = config["project"]
    name = str(project["name"])
    version = str(project["version"])
    dist_info = f"{_distribution_name(name)}-{version}.dist-info"
    lines = [
        "Metadata-Version: 2.1",
        f"Name: {name}",
        f"Version: {version}",
        f"Summary: {project.get('description', '')}",
        f"Requires-Python: {project.get('requires-python', '')}",
        "License: MIT",
    ]
    for author in project.get("authors", []):
        if author.get("name"):
            lines.append(f"Author: {author['name']}")
    if project.get("keywords"):
        lines.append("Keywords: " + ",".join(project["keywords"]))
    return name, version, dist_info, ("\n".join(lines) + "\n").encode()


def _selected_source_files(config: dict) -> dict[str, Path]:
    """Resolve exactamente los archivos fuente que ingresan al wheel."""
    selected: dict[str, Path] = {}
    build = config["tool"]["edaios-build"]
    package_data = build.get("package-data", {})
    for root_text in build["source-roots"]:
        source_root = ROOT / root_text
        for source in _safe_files(source_root):
            relative = source.relative_to(source_root)
            package_parts = relative.parts[:-1]
            if not package_parts:
                continue
            cursor = source_root
            belongs_to_package = False
            for part in package_parts:
                cursor /= part
                if (cursor / "__init__.py").is_file():
                    belongs_to_package = True
            if belongs_to_package:
                package = relative.parts[0]
                inside_package = Path(*relative.parts[1:]).as_posix()
                include = source.suffix == ".py" or any(
                    Path(inside_package).match(pattern)
                    for pattern in package_data.get(package, [])
                )
                if not include:
                    continue
                target = relative.as_posix()
                previous = selected.get(target)
                if previous is not None and previous.read_bytes() != source.read_bytes():
                    raise RuntimeError(f"colisión entre source roots: {target}")
                selected.setdefault(target, source)
    return selected


def selected_source_files() -> dict[str, Path]:
    """Superficie auxiliar para provenance y verificación de distribución."""
    return _selected_source_files(_config())


def _wheel_entries(config: dict) -> tuple[dict[str, bytes], str, str]:
    _, version, dist_info, metadata = _metadata(config)
    entries = {
        target: source.read_bytes()
        for target, source in _selected_source_files(config).items()
    }
    entries[f"{dist_info}/METADATA"] = metadata
    entries[f"{dist_info}/WHEEL"] = (
        "Wheel-Version: 1.0\nGenerator: edaios-build-backend 1\n"
        "Root-Is-Purelib: true\nTag: py3-none-any\n"
    ).encode()
    scripts = config["project"].get("scripts", {})
    if scripts:
        body = "[console_scripts]\n" + "".join(
            f"{key} = {value}\n" for key, value in sorted(scripts.items())
        )
        entries[f"{dist_info}/entry_points.txt"] = body.encode()
    license_path = ROOT / "LICENSE"
    if license_path.is_file() and not license_path.is_symlink():
        entries[f"{dist_info}/LICENSE"] = license_path.read_bytes()
    return entries, dist_info, version


def _digest(content: bytes) -> str:
    value = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
    return "sha256=" + value.decode("ascii")


def _record(entries: dict[str, bytes], dist_info: str) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    for path, content in sorted(entries.items()):
        writer.writerow((path, _digest(content), len(content)))
    writer.writerow((f"{dist_info}/RECORD", "", ""))
    return buffer.getvalue().encode()


def _write_wheel(wheel_directory: str) -> str:
    config = _config()
    entries, dist_info, version = _wheel_entries(config)
    entries[f"{dist_info}/RECORD"] = _record(entries, dist_info)
    project_name = _distribution_name(str(config["project"]["name"]))
    filename = f"{project_name}-{version}-py3-none-any.whl"
    destination = Path(wheel_directory) / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in sorted(entries.items()):
            info = zipfile.ZipInfo(path, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content)
    return filename


def get_requires_for_build_wheel(config_settings=None) -> list[str]:
    return []


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None) -> str:
    config = _config()
    _, _, dist_info, metadata = _metadata(config)
    target = Path(metadata_directory) / dist_info
    target.mkdir(parents=True, exist_ok=True)
    (target / "METADATA").write_bytes(metadata)
    (target / "WHEEL").write_text(
        "Wheel-Version: 1.0\nGenerator: edaios-build-backend 1\n"
        "Root-Is-Purelib: true\nTag: py3-none-any\n",
        encoding="utf-8",
    )
    return dist_info


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None) -> str:
    return _write_wheel(wheel_directory)
