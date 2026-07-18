"""Cumulative conformance profiles and monotonic policy comparison."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping

from .schemas import ValidationError, read_json


class ProfileError(ValueError):
    pass


class PolicyWeakeningError(ProfileError):
    pass


class ProfileRegistry:
    """Resolve profiles by inheritance while prohibiting control removal."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = (
            Path(root).resolve()
            if root is not None
            else Path(str(files("edaios_conformance").joinpath("resources/profiles")))
        )

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(path.name.removesuffix(".profile.json") for path in self.root.glob("*.profile.json")))

    def _control_map(self) -> dict[str, dict[str, Any]]:
        path = self.root.parent / "control-registry.json"
        if not path.is_file():
            raise ProfileError("control-registry.json no registrado")
        value = read_json(path)
        if value.get("schema") != "edaios.control-registry/v1":
            raise ProfileError("schema de control registry no soportado")
        rows = value.get("controls")
        if not isinstance(rows, list) or not rows:
            raise ProfileError("control registry debe contener controls")
        mapped: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise ProfileError("control registry contiene fila invalida")
            control_id = row["id"]
            if control_id in mapped:
                raise ProfileError(f"control duplicado: {control_id}")
            required = {"implementation", "tests", "gates", "claim"}
            if required - set(row) or not all(isinstance(row[key], str) and row[key] for key in ("implementation", "tests", "claim")):
                raise ProfileError(f"{control_id}: enlace de control incompleto")
            if not isinstance(row["gates"], list) or not row["gates"]:
                raise ProfileError(f"{control_id}: gates invalidos")
            mapped[control_id] = row
        return mapped

    def load(self, profile_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", profile_id):
            raise ProfileError(f"id de perfil invalido: {profile_id!r}")
        path = self.root / f"{profile_id}.profile.json"
        if not path.is_file():
            raise ProfileError(f"perfil no registrado: {profile_id}")
        value = read_json(path)
        required = {"schema", "id", "version", "parent", "controls"}
        missing = required - set(value)
        if missing:
            raise ProfileError(f"{profile_id}: campos ausentes: {sorted(missing)}")
        if value["schema"] != "edaios.conformance-profile/v1":
            raise ProfileError(f"{profile_id}: schema no soportado")
        if value["id"] != profile_id:
            raise ProfileError(f"{profile_id}: id no coincide con nombre")
        if not isinstance(value["controls"], list) or not value["controls"]:
            raise ProfileError(f"{profile_id}: controls debe ser lista no vacia")
        if any(not isinstance(item, str) or not item for item in value["controls"]):
            raise ProfileError(f"{profile_id}: control invalido")
        if len(value["controls"]) != len(set(value["controls"])):
            raise ProfileError(f"{profile_id}: controls duplicados")
        if value.get("remove_controls"):
            raise PolicyWeakeningError(f"{profile_id}: remove_controls esta prohibido")
        unknown = set(value) - {
            "schema", "id", "version", "parent", "controls", "description",
            "claim_boundary", "remove_controls",
        }
        if unknown:
            raise ProfileError(f"{profile_id}: propiedades no admitidas: {sorted(unknown)}")
        return value

    def resolve(self, profile_id: str) -> dict[str, Any]:
        chain: list[dict[str, Any]] = []
        visited: set[str] = set()
        current: str | None = profile_id
        while current is not None:
            if current in visited:
                raise ProfileError(f"ciclo de perfiles detectado en {current}")
            visited.add(current)
            row = self.load(current)
            chain.append(row)
            parent = row["parent"]
            if parent is not None and not isinstance(parent, str):
                raise ProfileError(f"{current}: parent debe ser string o null")
            current = parent
        chain.reverse()
        effective: list[str] = []
        for row in chain:
            for control in row["controls"]:
                if control not in effective:
                    effective.append(control)
        return {
            "schema": "edaios.resolved-conformance-profile/v1",
            "id": profile_id,
            "version": chain[-1]["version"],
            "chain": [row["id"] for row in chain],
            "controls": effective,
            "monotonic": True,
        }

    def validate_registry(self) -> dict[str, Any]:
        names = self.names()
        if set(names) != {"core-release", "initiative-adoption", "federation"}:
            raise ProfileError("registry debe publicar core-release, initiative-adoption y federation")
        control_map = self._control_map()
        resolved = {name: self.resolve(name) for name in names}
        expected_chain = {
            "core-release": ["core-release"],
            "initiative-adoption": ["core-release", "initiative-adoption"],
            "federation": ["core-release", "initiative-adoption", "federation"],
        }
        for name, chain in expected_chain.items():
            if resolved[name]["chain"] != chain:
                raise ProfileError(f"{name}: herencia inesperada")
        declared = {control for row in resolved.values() for control in row["controls"]}
        if declared != set(control_map):
            missing = sorted(declared - set(control_map))
            extra = sorted(set(control_map) - declared)
            raise ProfileError(f"control registry/profile mismatch: missing={missing} extra={extra}")
        return {
            "status": "ok",
            "profiles": list(names),
            "resolved": resolved,
            "controls": sorted(control_map),
        }


def _control_map(policy: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    controls = policy.get("controls")
    if not isinstance(controls, list):
        raise ValidationError(["$.controls: debe ser lista"])
    mapped: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(controls):
        if not isinstance(row, Mapping) or not isinstance(row.get("id"), str):
            raise ValidationError([f"$.controls[{index}]: control invalido"])
        control_id = row["id"]
        if control_id in mapped:
            raise ValidationError([f"$.controls[{index}].id: duplicado {control_id}"])
        mapped[control_id] = dict(row)
    return mapped


def diff_policy(current: Mapping[str, Any], proposed: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic diff; no policy is applied by this operation."""
    old = _control_map(current)
    new = _control_map(proposed)
    removed = sorted(set(old) - set(new))
    added = sorted(set(new) - set(old))
    changed = sorted(key for key in set(old) & set(new) if old[key] != new[key])
    weakened = list(removed)
    for key in changed:
        old_level = old[key].get("level", "required")
        new_level = new[key].get("level", "required")
        if old_level == "required" and new_level != "required":
            weakened.append(key)
    dimensions: list[str] = []
    if current.get("parent") != proposed.get("parent"):
        dimensions.append("parent")
    if current.get("approval_required") is True and proposed.get("approval_required") is False:
        dimensions.append("approval_required")
    old_age = current.get("max_receipt_age_seconds")
    new_age = proposed.get("max_receipt_age_seconds")
    if isinstance(old_age, int) and isinstance(new_age, int) and new_age > old_age:
        dimensions.append("max_receipt_age_seconds")
    if current.get("exceptions_allowed") is False and proposed.get("exceptions_allowed") is True:
        dimensions.append("exceptions_allowed")
    old_sensitivity = current.get("allowed_sensitivity")
    new_sensitivity = proposed.get("allowed_sensitivity")
    if isinstance(old_sensitivity, list) and isinstance(new_sensitivity, list):
        if not set(new_sensitivity).issubset(set(old_sensitivity)):
            dimensions.append("allowed_sensitivity")
    weakened.extend(dimensions)
    return {
        "schema": "edaios.policy-diff/v1",
        "current": current.get("id"),
        "proposed": proposed.get("id"),
        "added": added,
        "removed": removed,
        "changed": changed,
        "weakening": sorted(set(weakened)),
        "dimension_weakening": sorted(set(dimensions)),
        "applicable": not weakened,
    }


def require_monotonic_policy(current: Mapping[str, Any], proposed: Mapping[str, Any]) -> dict[str, Any]:
    report = diff_policy(current, proposed)
    if report["weakening"]:
        raise PolicyWeakeningError(
            "la politica propuesta retira o debilita controles: "
            + ", ".join(report["weakening"])
        )
    return report


def load_policy(path: str | Path) -> dict[str, Any]:
    return read_json(path)


def explain_failure(code: str) -> dict[str, str]:
    explanations = {
        "SCHEMA_INVALID": "El artefacto no satisface su schema; corrige la fuente y vuelve a validar.",
        "PROFILE_WEAKENING": "Un perfil hijo retiro o debilito un control heredado; solo puede agregar controles.",
        "AUTHORITY_DENIED": "El actor no posee una delegacion activa para la capacidad y scope solicitados.",
        "APPROVAL_REQUIRED": "La politica exige ApprovalReceipt de una persona autorizada y no esta presente o no coincide.",
        "EVIDENCE_TAMPERED": "El digest registrado no coincide con los bytes actuales de la evidencia.",
        "EVIDENCE_STALE": "El receipt excede la antiguedad admitida por la politica.",
        "HEAD_MISMATCH": "El commit head esperado no coincide con el ligado al receipt.",
        "ROLLBACK_DRIFT": "Un archivo creado por init cambio; Core no lo elimina automaticamente.",
    }
    if code not in explanations:
        raise ProfileError(f"codigo no registrado: {code}")
    return {"code": code, "explanation": explanations[code], "decision": "blocked"}


__all__ = [
    "PolicyWeakeningError", "ProfileError", "ProfileRegistry", "diff_policy",
    "explain_failure", "load_policy", "require_monotonic_policy",
]
