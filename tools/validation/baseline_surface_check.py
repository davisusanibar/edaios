#!/usr/bin/env python3
"""Prueba por estructura que Core sigue agnóstico y sin consumers instalados.

Las palabras que describen un runtime o una iniciativa no constituyen una
instalación. Esta puerta inspecciona superficies ejecutables y catálogos; la
trazabilidad de ADR/RFC vive en ``traceability_check.py``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


FORBIDDEN_ROOTS = {
    "archive", "node_modules", "packages", "portfolio", "releases",
    "reference-consumers", "foundation", "edaios-framework", ".bitbucket",
    ".husky", ".edaios", "domains", "engines", "consumers", "products",
    "platform",
}
RUNTIME_MANIFESTS = {
    "pom.xml", "build.gradle", "build.gradle.kts", "package.json",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
}
RUNTIME_SUFFIXES = {".java", ".kt", ".tf"}


def tracked_files(root: Path) -> list[Path] | None:
    """Superficie versionada según git; None si git no puede responder.

    El gate juzga lo versionado: el estado local no rastreado (.edaios, locks,
    receipts) es reconstruible por contrato de memory-port y queda fuera del
    claim. Sin git disponible se conserva el barrido de filesystem, que en un
    árbol exportado equivale a la superficie completa (fail-closed).
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    entries = [item for item in out.stdout.decode("utf-8").split("\0") if item]
    if not entries:
        return None
    return [root / item for item in entries]


def validate_profile_registry(root: Path, selected: str) -> None:
    data = json.loads(
        (root / "core/framework/core/profiles/validation-profiles.json").read_text(
            encoding="utf-8"
        )
    )
    if data.get("schema") != "edaios.validation-profile-registry/v1":
        raise ValueError("schema de profiles no soportado")
    registry_rows = data.get("profiles")
    if not isinstance(registry_rows, list) or not all(isinstance(row, dict) for row in registry_rows):
        raise ValueError("profiles inválidos")
    profile_root = (root / "core/framework/core/profiles").resolve()
    by_id: dict[str, dict[str, object]] = {}
    for registry_row in registry_rows:
        profile_id = str(registry_row.get("id", ""))
        profile_path = (root / str(registry_row.get("path", ""))).resolve()
        try:
            profile_path.relative_to(profile_root)
        except ValueError as exc:
            raise ValueError(f"{profile_id}: path fuera de profiles") from exc
        row = json.loads(profile_path.read_text(encoding="utf-8"))
        if row.get("schema") != "edaios.conformance-profile/v1" or row.get("id") != profile_id:
            raise ValueError(f"{profile_id}: contrato inválido")
        if row.get("remove_controls"):
            raise ValueError(f"{profile_id}: remove_controls prohibido")
        controls = row.get("controls")
        if not isinstance(controls, list) or not controls or len(controls) != len(set(controls)):
            raise ValueError(f"{profile_id}: controls inválidos")
        by_id[profile_id] = row
    if set(by_id) != {"core-release", "initiative-adoption", "federation"}:
        raise ValueError("profiles canónicos incompletos")
    if len(by_id) != len(registry_rows):
        raise ValueError("ids de profile duplicados")
    if (
        by_id["core-release"].get("parent") is not None
        or by_id["initiative-adoption"].get("parent") != "core-release"
        or by_id["federation"].get("parent") != "initiative-adoption"
    ):
        raise ValueError("cadena de profiles no es acumulativa")
    if selected not in by_id:
        raise ValueError(f"profile no resoluble: {selected}")
    active: set[str] = set()
    memo: dict[str, set[str]] = {}

    def resolve(profile_id: str) -> set[str]:
        if profile_id in memo:
            return memo[profile_id]
        if profile_id in active:
            raise ValueError(f"ciclo de herencia: {profile_id}")
        active.add(profile_id)
        row = by_id[profile_id]
        own = {str(item) for item in row.get("controls", [])}
        parent = row.get("parent")
        if parent is not None:
            if not isinstance(parent, str) or parent not in by_id:
                raise ValueError(f"parent no resoluble: {parent}")
            inherited = resolve(parent)
            own.update(inherited)
        active.remove(profile_id)
        memo[profile_id] = own
        return own

    resolve(selected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--profile", default="core-release",
        choices=("core-release", "initiative-adoption", "federation"),
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    try:
        validate_profile_registry(root, args.profile)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"registry de perfiles inválido: {exc}")

    tracked = tracked_files(root)
    if tracked is not None:
        relatives = [path.relative_to(root) for path in tracked]
        top_level = {rel.parts[0] for rel in relatives}
        surface = tracked
        core_present = "core" in top_level
        core_layers = {
            rel.parts[1] for rel in relatives
            if rel.parts[0] == "core" and len(rel.parts) > 2
        }
    else:
        top_level = {path.name for path in root.iterdir() if path.name != ".git"}
        surface = [
            path for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ]
        core = root / "core"
        core_present = core.is_dir()
        core_layers = (
            {path.name for path in core.iterdir() if path.is_dir()}
            if core_present else set()
        )

    for name in sorted(FORBIDDEN_ROOTS & top_level):
        errors.append(f"raíz no instalada permitida apareció: {name}")

    if core_present:
        unexpected = sorted(core_layers - {"foundation", "framework"})
        if unexpected:
            errors.append("capas no autorizadas dentro de core/: " + ", ".join(unexpected))
    else:
        errors.append("core/ ausente")

    for path in surface:
        if path.name in RUNTIME_MANIFESTS or path.suffix.lower() in RUNTIME_SUFFIXES:
            errors.append(f"runtime/infra instalado: {path.relative_to(root)}")

    try:
        catalog = json.loads((root / "repositories.json").read_text(encoding="utf-8"))
        modules = catalog.get("modules", [])
        if len(modules) != 1 or modules[0].get("id") != "edaios-core" or modules[0].get("path") != "core":
            errors.append("catálogo instala algo distinto de edaios-core")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"catálogo modular ilegible: {exc}")

    for error in errors:
        print(f"[FAIL] {error}")
    if errors:
        return 1
    print(
        f"[surface] OK: profile={args.profile} · Core agnóstico · "
        "sin runtime, dominio, consumer ni producto instalado"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
