#!/usr/bin/env python3
"""Seleccion de feature Spec Kit por worktree sin mutar el handoff canonico."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile


ROOT = Path(os.environ.get("EDAIOS_REPO_ROOT") or Path(__file__).resolve().parents[2])
CANONICAL = Path(".specify/feature.json")
LOCAL = Path(".specify/feature.local.json")
HANDOFF_SCHEMAS = {"edaios.feature-handoff/v2", "edaios.feature-handoff/v3"}
HANDOFF_SCHEMA = "edaios.feature-handoff/v2"
HANDOFF_ROLES = ("baseline_feature", "last_closed_feature", "active_feature")


class FeatureContextError(ValueError):
    pass


def _within(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _frontmatter_id(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise FeatureContextError(f"{path}: frontmatter ausente")
    if "\n---\n" not in text[4:]:
        raise FeatureContextError(f"{path}: frontmatter sin cierre")
    frontmatter = text[4:].split("\n---\n", 1)[0]
    match = re.search(r"^id:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    if not match:
        raise FeatureContextError(f"{path}: id ausente")
    return match.group(1).strip().strip("\"'")


def _feature_is_closed(root: Path, pointer: dict[str, str]) -> bool:
    spec = root / pointer["feature_directory"] / "spec.md"
    text = spec.read_text(encoding="utf-8")
    frontmatter = text[4:].split("\n---\n", 1)[0]
    state = re.search(r"^estado:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    phase = re.search(r"^fase:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    return bool(
        state
        and phase
        and state.group(1).strip().strip("\"'") == "Cerrado"
        and phase.group(1).strip().strip("\"'") == "implemented"
    )


def _typed_id(path: Path) -> str:
    match = re.search(r"^id:\s*(.+?)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise FeatureContextError(f"{path}: id ausente")
    return match.group(1).strip().strip("\"'")


def feature_pointer(root: Path, feature_value: str) -> dict[str, str]:
    root = root.resolve()
    candidate = (root / feature_value).resolve()
    specs = (root / "specs").resolve()
    if not _within(specs, candidate) or candidate == specs:
        candidate = (specs / feature_value).resolve()
    if not _within(specs, candidate) or candidate == specs:
        raise FeatureContextError("la feature debe vivir bajo specs/")

    spec = candidate / "spec.md"
    typed = candidate / "feature.spec.yaml"
    if not spec.is_file() or not typed.is_file():
        raise FeatureContextError(f"{candidate}: faltan spec.md o feature.spec.yaml")
    spec_id = _frontmatter_id(spec)
    typed_id = _typed_id(typed)
    if spec_id != typed_id:
        raise FeatureContextError(f"identidad inconsistente: spec={spec_id} typed={typed_id}")
    return {
        "id": spec_id,
        "feature_directory": candidate.relative_to(root).as_posix(),
    }


def _pointer_from_data(root: Path, data: object, path: Path, role: str) -> dict[str, str]:
    if not isinstance(data, dict):
        raise FeatureContextError(f"{path}: {role} debe ser un objeto")
    try:
        pointer = feature_pointer(root, str(data["feature_directory"]))
        declared_id = str(data["id"]).strip()
    except (KeyError, TypeError, ValueError) as exc:
        raise FeatureContextError(f"{path}: {role} ilegible: {exc}") from exc
    if not declared_id:
        raise FeatureContextError(f"{path}: {role}.id vacio")
    if declared_id != pointer["id"]:
        raise FeatureContextError(
            f"{path}: {role}.id {declared_id} no coincide con {pointer['id']}"
        )
    return pointer


def _load_pointer(root: Path, relative: Path) -> dict[str, str]:
    """Carga el selector local v1; el formato se conserva por compatibilidad."""
    root = root.resolve()
    path = root / relative
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") is not None:
            raise FeatureContextError(f"{path}: selector local v1 invalido")
        return _pointer_from_data(root, data, path, "selector local")
    except (OSError, ValueError, TypeError) as exc:
        if isinstance(exc, FeatureContextError):
            raise
        raise FeatureContextError(f"{path}: pointer ilegible: {exc}") from exc


def _load_handoff(root: Path) -> dict[str, dict[str, str]]:
    """Carga el handoff canónico v2 y valida sus tres referencias."""
    root = root.resolve()
    path = root / CANONICAL
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise FeatureContextError(f"{path}: handoff debe ser un objeto")
        if data.get("schema") not in HANDOFF_SCHEMAS:
            raise FeatureContextError(f"{path}: schema de handoff no soportado")
        pointers = {role: _pointer_from_data(root, data.get(role), path, role)
                    for role in HANDOFF_ROLES if data.get(role) is not None}
        if data.get("schema") == "edaios.feature-handoff/v3" and data.get("active_feature") is None:
            pointers["active_feature"] = None
        if set(pointers) != set(HANDOFF_ROLES):
            raise FeatureContextError(f"{path}: faltan referencias obligatorias del handoff")
        directories = [pointer["feature_directory"] for pointer in pointers.values()]
        if len(directories) != len(set(directories)):
            raise FeatureContextError(f"{path}: las tres referencias deben ser distintas")
        return pointers
    except (OSError, ValueError, TypeError) as exc:
        if isinstance(exc, FeatureContextError):
            raise
        raise FeatureContextError(f"{path}: handoff ilegible: {exc}") from exc


def resolve(root: Path, explicit: str | None = None) -> tuple[dict[str, str], str]:
    root = root.resolve()
    if explicit:
        return feature_pointer(root, explicit), "explicit"
    if (root / LOCAL).exists():
        return _load_pointer(root, LOCAL), "local"
    if (root / CANONICAL).exists():
        return _load_handoff(root)["active_feature"], "canonical"
    raise FeatureContextError("no existe selector local ni pointer canonico")


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(ROOT))
    commands = parser.add_subparsers(dest="command", required=True)

    select = commands.add_parser("select", help="selecciona una feature para este worktree")
    select.add_argument("feature")
    select.add_argument("--canonical", action="store_true",
                        help="actualiza el handoff versionado; reservado al cambio de foco del programa")

    resolve_cmd = commands.add_parser("resolve", help="resuelve explicit > local > canonico")
    resolve_cmd.add_argument("--feature", help="selector explicito con maxima precedencia")
    resolve_cmd.add_argument("--path-only", action="store_true")

    commands.add_parser("clear", help="elimina solo el selector local del worktree")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()

    try:
        if args.command == "select":
            pointer = feature_pointer(root, args.feature)
            destination = CANONICAL if args.canonical else LOCAL
            if args.canonical:
                handoff = _load_handoff(root)
                last_closed = handoff["last_closed_feature"]
                if _feature_is_closed(root, handoff["active_feature"]):
                    last_closed = handoff["active_feature"]
                historical = {
                    handoff["baseline_feature"]["feature_directory"],
                    last_closed["feature_directory"],
                }
                if pointer["feature_directory"] in historical:
                    raise FeatureContextError(
                        "active_feature no puede reutilizar baseline_feature ni last_closed_feature"
                    )
                payload: dict[str, object] = {
                    "schema": HANDOFF_SCHEMA,
                    "baseline_feature": handoff["baseline_feature"],
                    "last_closed_feature": last_closed,
                    "active_feature": pointer,
                }
            else:
                payload = pointer
            _atomic_json(root / destination, payload)
            print(f"{destination.as_posix()} -> {pointer['feature_directory']} ({pointer['id']})")
            return 0
        if args.command == "clear":
            (root / LOCAL).unlink(missing_ok=True)
            print(f"{LOCAL.as_posix()} eliminado")
            return 0

        pointer, source = resolve(root, args.feature)
        if args.path_only:
            print(pointer["feature_directory"])
        else:
            print(json.dumps({**pointer, "source": source}, ensure_ascii=True, indent=2))
        return 0
    except FeatureContextError as exc:
        print(f"[feature-context] ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
