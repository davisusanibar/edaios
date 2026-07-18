#!/usr/bin/env python3
"""Valida Core cerrado y attachments externos según un perfil acumulativo."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


ALLOWED = {
    ".agents", ".claude", ".github", ".gitignore", ".specify", "AGENTS.md",
    "README.md", "VERSION", "bitbucket-pipelines.yml", "core", "docs",
    "edaios.lock.json",
    "governance", "program-office", "repositories.json", "scripts", "specs",
    "tools",
}
REPOSITORY_INTEGRATIONS = {"bitbucket-pipelines.yml"}
NAMESPACE = re.compile(r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9-]*)+")


def versioned_roots(root: Path) -> set[str] | None:
    """Raíces de la superficie versionada según git; None si git no responde.

    La topología juzga lo versionado: el estado local no rastreado (.edaios,
    locks, receipts) es reconstruible por contrato de memory-port y no
    constituye una raíz instalada. Sin git se conserva el barrido de
    filesystem (fail-closed para árboles exportados).
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    names = {
        item.split("/", 1)[0]
        for item in out.stdout.decode("utf-8").split("\0")
        if item
    }
    return names or None


def profiles(root: Path) -> dict[str, dict[str, object]]:
    path = root / "core/framework/core/profiles/validation-profiles.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "edaios.validation-profile-registry/v1":
        raise ValueError("schema de perfiles no soportado")
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
        raise ValueError("faltan perfiles canónicos")
    if len(by_id) != len(registry_rows):
        raise ValueError("ids de profile duplicados")
    if (
        by_id["core-release"].get("parent") is not None
        or by_id["initiative-adoption"].get("parent") != "core-release"
        or by_id["federation"].get("parent") != "initiative-adoption"
    ):
        raise ValueError("cadena de profiles no es acumulativa")
    active: set[str] = set()
    memo: dict[str, set[str]] = {}

    def resolve(profile_id: str) -> set[str]:
        if profile_id in memo:
            return memo[profile_id]
        if profile_id in active or profile_id not in by_id:
            raise ValueError(f"herencia inválida: {profile_id}")
        active.add(profile_id)
        row = by_id[profile_id]
        own = {str(item) for item in row.get("controls", [])}
        parent = row.get("parent")
        if parent is not None:
            if not isinstance(parent, str):
                raise ValueError(f"{profile_id}: parent inválido")
            inherited = resolve(parent)
            own.update(inherited)
        active.remove(profile_id)
        memo[profile_id] = own
        return own

    for profile_id in by_id:
        resolve(profile_id)
    return by_id


def attachment(raw: str, root: Path) -> tuple[str, Path]:
    namespace, sep, path_text = raw.partition("=")
    if not sep or not NAMESPACE.fullmatch(namespace):
        raise ValueError(f"attachment inválido {raw!r}; use namespace=path")
    path = Path(path_text)
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"attachment no resoluble: {raw}")
    try:
        path.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError(f"attachment debe vivir fuera del Core: {raw}")
    return namespace, path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--require-git", action="store_true")
    parser.add_argument(
        "--profile", default="core-release",
        choices=("core-release", "initiative-adoption", "federation"),
    )
    parser.add_argument(
        "--attachment", action="append", default=[], metavar="NAMESPACE=PATH",
        help="scope consumidor explícito y externo; repetible solo para federation",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    try:
        profiles(root)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"registry de perfiles inválido: {exc}")

    tracked_roots = versioned_roots(root)
    visible = (
        tracked_roots if tracked_roots is not None
        else {path.name for path in root.iterdir() if path.name != ".git"}
    )
    extra = sorted(visible - ALLOWED)
    required = ALLOWED if args.require_git else ALLOWED - REPOSITORY_INTEGRATIONS
    missing = sorted(required - visible)
    if extra:
        errors.append(f"raíces no autorizadas: {', '.join(extra)}")
    if missing:
        errors.append(f"raíces requeridas ausentes: {', '.join(missing)}")
    nested = [path for path in root.rglob(".git") if path != root / ".git"]
    if nested:
        errors.append("repositorios Git anidados: " + ", ".join(map(str, nested)))
    if args.require_git and not (root / ".git").is_dir():
        errors.append(".git raíz requerido")

    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        catalog = json.loads((root / "repositories.json").read_text(encoding="utf-8"))
        modules = catalog["modules"]
        if catalog.get("version") != version:
            errors.append("repositories.json diverge de VERSION")
        if len(modules) != 1:
            errors.append("el release Core declara exactamente un módulo")
        else:
            module = modules[0]
            expected = {
                "id": "edaios-core", "path": "core", "role": "core",
                "required": True, "version": version,
            }
            if any(module.get(key) != value for key, value in expected.items()):
                errors.append(f"catálogo modular inválido: {module}")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"repositories.json inválido: {exc}")

    mounted: list[tuple[str, Path]] = []
    for raw in args.attachment:
        try:
            mounted.append(attachment(raw, root))
        except ValueError as exc:
            errors.append(str(exc))
    namespaces = [namespace for namespace, _path in mounted]
    paths = [path for _namespace, path in mounted]
    if len(namespaces) != len(set(namespaces)):
        errors.append("namespaces de attachment duplicados")
    if len(paths) != len(set(paths)):
        errors.append("paths de attachment duplicados")
    expected_count = {
        "core-release": lambda count: count == 0,
        "initiative-adoption": lambda count: count == 1,
        "federation": lambda count: count >= 2,
    }
    if not expected_count[args.profile](len(mounted)):
        expectation = {
            "core-release": "cero",
            "initiative-adoption": "exactamente uno",
            "federation": "al menos dos",
        }[args.profile]
        errors.append(f"profile {args.profile} exige {expectation} attachment(s)")

    for error in errors:
        print(f"[FAIL] {error}")
    if errors:
        return 1
    print(
        f"[structure] OK: profile={args.profile} · una raíz · un módulo Core · "
        f"{len(mounted)} attachment(s) externo(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
