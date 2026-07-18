"""Consumer-side initiative attachment lifecycle.

All writes are restricted to the selected workspace.  Initialization records
digests so rollback can remove only untouched files created by Core.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from edaios_core.io import atomic_write_bytes, workspace_lock
from edaios_core.knowledge import (
    NAMESPACE_RE,
    KnowledgeMount,
    corpus_digest,
    normalize_mounts,
    resolve_authorized_path,
)

from .profiles import ProfileRegistry, require_monotonic_policy
from .schemas import SchemaRegistry, ValidationError, read_json


class AttachmentError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_workspace(root: str | Path, *, create: bool = False) -> Path:
    candidate = Path(root)
    if candidate.is_symlink():
        raise AttachmentError("workspace symlink no admitido")
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    workspace = candidate.resolve()
    if not workspace.is_dir():
        raise AttachmentError("workspace no existe o no es directorio")
    return workspace


def _safe_target(workspace: Path, relative: str) -> Path:
    relative_path = Path(relative)
    if (
        not relative
        or relative_path.is_absolute()
        or ".." in relative_path.parts
    ):
        raise AttachmentError(f"ruta relativa invalida: {relative!r}")

    # Inspect the lexical path before resolve(): resolving first would erase a
    # symlink leaf (or parent) and make an external AuthorityRegistry appear to
    # belong to the attachment.
    target = workspace
    for part in relative_path.parts:
        target = target / part
        if target.is_symlink():
            raise AttachmentError(f"symlink no admitido: {relative}")

    try:
        resolved = target.resolve(strict=False)
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise AttachmentError(f"ruta fuera del workspace: {relative}") from exc
    return resolved


def _write_json(target: Path, value: Mapping[str, Any]) -> None:
    atomic_write_bytes(
        target,
        (json.dumps(dict(value), ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )


def _file_digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def initialize_attachment(
    root: str | Path,
    *,
    initiative_id: str,
    namespace: str,
    owner: str,
    value_owner: str,
    core_version: str = "3.1.0",
) -> dict[str, Any]:
    """Create a draft T0 attachment; it does not approve or register adoption."""
    if re.fullmatch(r"\d+\.\d+\.\d+", core_version) is None:
        raise AttachmentError("core_version debe ser SemVer estable")
    next_major = int(core_version.split(".", 1)[0]) + 1
    if re.fullmatch(r"[a-z][a-z0-9-]{2,63}", initiative_id) is None:
        raise AttachmentError("initiative_id debe usar kebab-case (3..64)")
    if NAMESPACE_RE.fullmatch(namespace) is None:
        raise AttachmentError("namespace debe ser global y separado por puntos")
    if not owner.strip() or not value_owner.strip():
        raise AttachmentError("owner y value_owner son obligatorios y no se infieren")
    workspace = _safe_workspace(root, create=True)
    paths = {
        "manifest": "edaios.initiative.json",
        "policy": ".edaios/policies/initiative-policy.json",
        "sensitivity": ".edaios/policies/sensitivity-t0.json",
        "authority": ".edaios/authority-registry.json",
    }
    for relative in paths.values():
        if _safe_target(workspace, relative).exists():
            raise AttachmentError(f"init no sobrescribe: {relative}")

    manifest = {
        "schema": "edaios.initiative-manifest/v1",
        "id": initiative_id,
        "namespace": namespace,
        "owner": owner,
        "value_owner": value_owner,
        "core_compatibility": f">={core_version} <{next_major}.0.0",
        "conformance_profile": "initiative-adoption",
        "policy_profile": paths["policy"],
        "sensitivity_profile": paths["sensitivity"],
        "authority_registry": paths["authority"],
        "sources": [{"path": "README.md", "authority": owner}],
        "capabilities": ["validate", "evidence:create", "evidence:verify"],
        "required_gates": ["core-release", "initiative-adoption"],
        "evidence_path": ".edaios/evidence",
        "lifecycle": "draft",
        "human_approval_required": True,
    }
    policy = {
        "schema": "edaios.policy-profile/v1",
        "id": f"{initiative_id}-policy",
        "version": "1.0.0",
        "parent": "initiative-adoption",
        "controls": [
            {"id": "traceability", "level": "required"},
            {"id": "human-authority", "level": "required"},
            {"id": "evidence-integrity", "level": "required"},
        ],
        "approval_required": True,
        "max_receipt_age_seconds": 86400,
        "allowed_sensitivity": ["T0"],
        "exceptions_allowed": False,
    }
    sensitivity = {
        "schema": "edaios.sensitivity-profile/v1",
        "id": "sensitivity-t0",
        "level": "T0",
        "data_classes": ["public-metadata", "synthetic-fixture"],
        "required_controls": ["no-pii", "no-secret", "no-network-required"],
        "forbidden_routes": ["llm", "external-network", "production-data"],
        "approval_roles": ["initiative-owner"],
    }
    authority = {
        "schema": "edaios.authority-registry/v1",
        "initiative": initiative_id,
        "version": "1.0.0",
        "actors": [
            {
                "actor_id": owner,
                "type": "human",
                "roles": ["initiative-owner", "approver"],
                "capabilities": ["approve", "delegate", "rollback"],
                "active": True,
            },
            {
                "actor_id": value_owner,
                "type": "human",
                "roles": ["value-owner"],
                "capabilities": ["outcome:verify"],
                "active": True,
            },
        ],
    }
    registry = SchemaRegistry()
    for schema_name, value in (
        ("initiative-manifest", manifest),
        ("policy-profile", policy),
        ("sensitivity-profile", sensitivity),
        ("authority-registry", authority),
    ):
        registry.validate(schema_name, value)

    values = {"manifest": manifest, "policy": policy, "sensitivity": sensitivity, "authority": authority}
    with workspace_lock(workspace, "initiative-init"):
        for key, value in values.items():
            _write_json(_safe_target(workspace, paths[key]), value)
        state_files = {
            relative: _file_digest(_safe_target(workspace, relative))
            for relative in paths.values()
        }
        state = {
            "schema": "edaios.attachment-state/v1",
            "created_at": _now(),
            "initiative": initiative_id,
            "files": state_files,
            "claim_boundary": "draft local; no adoption or approval implied",
        }
        state_path = _safe_target(workspace, ".edaios/attachment-state.json")
        _write_json(state_path, state)
    return {
        "status": "initialized",
        "workspace": str(workspace),
        "manifest": str(_safe_target(workspace, paths["manifest"])),
        "state": str(state_path),
        "claim_boundary": state["claim_boundary"],
    }


def validate_attachment(root: str | Path) -> dict[str, Any]:
    workspace = _safe_workspace(root)
    manifest_path = _safe_target(workspace, "edaios.initiative.json")
    manifest = read_json(manifest_path)
    registry = SchemaRegistry()
    registry.validate("initiative-manifest", manifest)
    profile = ProfileRegistry().resolve(manifest["conformance_profile"])
    artifacts: dict[str, dict[str, Any]] = {}
    refs = {
        "policy-profile": manifest["policy_profile"],
        "sensitivity-profile": manifest["sensitivity_profile"],
        "authority-registry": manifest["authority_registry"],
    }
    for schema_name, relative in refs.items():
        target = _safe_target(workspace, relative)
        if target.is_symlink() or not target.is_file():
            raise AttachmentError(f"recurso ausente o symlink: {relative}")
        artifacts[schema_name] = registry.validate_file(schema_name, target)
    authority = artifacts["authority-registry"]
    if authority["initiative"] != manifest["id"]:
        raise ValidationError(["$.authority_registry: initiative no coincide"])
    if artifacts["sensitivity-profile"]["level"] not in artifacts["policy-profile"]["allowed_sensitivity"]:
        raise ValidationError(["$.sensitivity_profile: nivel no permitido por policy"])
    return {
        "status": "valid",
        "initiative": manifest["id"],
        "namespace": manifest["namespace"],
        "lifecycle": manifest["lifecycle"],
        "profile": profile,
        "artifacts": sorted(refs),
        "adopted": False,
        "claim_boundary": "conformance local; no human acceptance or remote operation",
    }


def validate_federation_mounts(path: str | Path) -> list[dict[str, Any]]:
    """Valida mounts y liga cada corpus a un attachment gobernado."""
    raw_document_path = Path(path)
    if raw_document_path.is_symlink():
        raise AttachmentError("federation mounts symlink no admitido")
    document_path = raw_document_path.resolve()
    document = read_json(document_path)
    SchemaRegistry().validate("federation-mounts", document)
    base = document_path.parent
    validated: list[dict[str, Any]] = []
    for index, row in enumerate(document["mounts"]):
        label = f"mounts[{index}]"

        def candidate(value: str) -> Path:
            candidate = Path(value)
            return base / candidate if not candidate.is_absolute() else candidate

        attachment = _safe_workspace(candidate(row["attachment"]))
        report = validate_attachment(attachment)
        manifest_path = attachment / "edaios.initiative.json"
        manifest = read_json(manifest_path)
        authority_path = _safe_target(attachment, manifest["authority_registry"])
        if _file_digest(manifest_path) != row["manifest_sha256"]:
            raise AttachmentError(f"{label}: digest de manifest no coincide")
        if _file_digest(authority_path) != row["authority_registry_sha256"]:
            raise AttachmentError(f"{label}: digest de authority registry no coincide")
        if report["namespace"] != row["namespace"]:
            raise AttachmentError(f"{label}: namespace no coincide con attachment")
        if manifest["conformance_profile"] != "federation":
            raise AttachmentError(f"{label}: attachment no declara profile federation")
        if row["authority_layer"] != "Consumer":
            raise AttachmentError(f"{label}: authority_layer debe ser Consumer")
        if manifest["owner"] != row["owner_actor_id"]:
            raise AttachmentError(f"{label}: owner_actor_id no coincide con manifest")
        authority = read_json(authority_path)
        active_actor_ids = tuple(
            sorted(
                {
                    str(item.get("actor_id"))
                    for item in authority.get("actors", [])
                    if item.get("active") and item.get("actor_id")
                }
            )
        )
        actor = next(
            (
                item for item in authority.get("actors", [])
                if item.get("actor_id") == row["owner_actor_id"] and item.get("active")
            ),
            None,
        )
        if actor is None or "initiative-owner" not in actor.get("roles", []):
            raise AttachmentError(f"{label}: authority activa no resoluble")

        # Normalize platform aliases (for example /var -> /private/var on
        # macOS) while preserving the declared relative path. This avoids
        # resolving away a user-controlled symlink before the secure walker
        # can reject it.
        declared_root = candidate(row["authorized_root"])
        corpus = candidate(row["path"])
        try:
            declared_relative = corpus.relative_to(declared_root)
        except ValueError:
            declared_relative = None
        authorized_root = _safe_workspace(declared_root)
        try:
            authorized_root.relative_to(attachment)
        except ValueError as exc:
            raise AttachmentError(
                f"{label}: authorized_root debe pertenecer al attachment"
            ) from exc
        if declared_relative is not None:
            corpus = authorized_root / declared_relative
        corpus = resolve_authorized_path(
            corpus,
            authorized_root,
            expected="directory",
            label=f"{label}: corpus",
        )
        normalized_mount = KnowledgeMount.from_value(
            {
                "namespace": row["namespace"],
                "path": corpus,
                "authority_layer": row["authority_layer"],
                "owner_actor_id": row["owner_actor_id"],
                "allowed_owner_actor_ids": active_actor_ids,
                "authorized_root": authorized_root,
                "corpus_sha256": row["corpus_sha256"],
            }
        )
        observed_corpus_digest = corpus_digest(normalized_mount)
        if observed_corpus_digest != row["corpus_sha256"]:
            raise AttachmentError(f"{label}: digest de corpus no coincide")
        validated.append(
            {
                "namespace": row["namespace"],
                "path": str(corpus),
                "authority_layer": row["authority_layer"],
                "owner_actor_id": row["owner_actor_id"],
                "allowed_owner_actor_ids": list(active_actor_ids),
                "authorized_root": str(authorized_root),
                "corpus_sha256": observed_corpus_digest,
            }
        )
    # La unicidad del schema opera sobre strings declarados. La frontera real es
    # la ruta resuelta: aliases como `corpus` y `corpus/./` no pueden montar los
    # mismos bytes dos veces bajo identidades distintas.
    normalized = normalize_mounts(validated)
    return [
        {
            "namespace": mount.namespace,
            "path": str(mount.path),
            "authority_layer": mount.authority_layer,
            "owner_actor_id": mount.owner_actor_id,
            "allowed_owner_actor_ids": list(mount.allowed_owner_actor_ids),
            "authorized_root": str(mount.authorized_root),
            "corpus_sha256": str(mount.corpus_sha256),
        }
        for mount in normalized
    ]


def prepare_upgrade(
    manifest: Mapping[str, Any],
    current_policy: Mapping[str, Any],
    target_policy: Mapping[str, Any],
    *,
    target_core: str,
) -> dict[str, Any]:
    if re.fullmatch(r"\d+\.\d+\.\d+", target_core) is None:
        raise AttachmentError("target_core debe ser SemVer estable")
    policy_diff = require_monotonic_policy(current_policy, target_policy)
    return {
        "schema": "edaios.upgrade-plan/v1",
        "initiative": manifest.get("id"),
        "from_core": manifest.get("core_compatibility"),
        "to_core": target_core,
        "policy_diff": policy_diff,
        "steps": [
            "validate current initiative-adoption profile",
            "stage target policy without replacing authority",
            "run core-release and initiative-adoption gates",
            "request human approval",
            "update compatibility only after approval",
        ],
        "automatic_apply": False,
        "rollback": "restore manifest and policy bytes captured before promotion",
    }


def write_upgrade_plan(path: str | Path, plan: Mapping[str, Any]) -> Path:
    target = Path(path)
    _write_json(target, plan)
    return target


def rollback_attachment(root: str | Path, *, apply: bool = False) -> dict[str, Any]:
    workspace = _safe_workspace(root)
    state_path = _safe_target(workspace, ".edaios/attachment-state.json")
    state = read_json(state_path)
    if state.get("schema") != "edaios.attachment-state/v1":
        raise AttachmentError("attachment state no soportado")
    files = state.get("files")
    if not isinstance(files, dict) or not files:
        raise AttachmentError("attachment state sin archivos")
    checked: list[str] = []
    for relative, expected in files.items():
        target = _safe_target(workspace, relative)
        if target.is_symlink() or not target.is_file():
            raise AttachmentError(f"rollback drift: {relative} ausente o symlink")
        if _file_digest(target) != expected:
            raise AttachmentError(f"rollback drift: {relative} fue modificado")
        checked.append(relative)
    report = {
        "schema": "edaios.rollback-report/v1",
        "workspace": str(workspace),
        "files": sorted(checked),
        "applied": False,
    }
    if not apply:
        return report
    with workspace_lock(workspace, "initiative-rollback"):
        # Revalidar dentro del lock evita TOCTOU entre la inspección y el borrado.
        for relative, expected in files.items():
            target = _safe_target(workspace, relative)
            if target.is_symlink() or not target.is_file() or _file_digest(target) != expected:
                raise AttachmentError(f"rollback drift bajo lock: {relative}")
        for relative in sorted(checked, key=lambda item: (item.count("/"), item), reverse=True):
            _safe_target(workspace, relative).unlink()
        state_path.unlink()
    report["applied"] = True
    return report


__all__ = [
    "AttachmentError", "initialize_attachment", "prepare_upgrade",
    "rollback_attachment", "validate_attachment", "validate_federation_mounts",
    "write_upgrade_plan",
]
