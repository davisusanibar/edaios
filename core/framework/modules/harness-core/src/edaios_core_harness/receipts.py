"""EvidenceReceipt v2 and ApprovalReceipt local integrity contracts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from edaios_conformance.schemas import (
    SchemaRegistry,
    ValidationError,
    canonical_digest,
    read_json,
)
from edaios_core.io import atomic_write_bytes, workspace_lock


class ReceiptError(ValueError):
    pass


INTEGRITY_CLAIM = "local-integrity-only; not identity or non-repudiation"


def _utc(value: datetime | None = None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ReceiptError("timestamp debe incluir timezone")
    return current.astimezone(timezone.utc)


def _timestamp(value: datetime | None = None) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _safe_file(workspace: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ReceiptError(f"evidence path fuera de workspace: {relative}")
    unresolved = workspace / candidate
    if unresolved.is_symlink():
        raise ReceiptError(f"evidence symlink no admitido: {relative}")
    parent = unresolved.parent
    while parent != workspace:
        if parent.is_symlink():
            raise ReceiptError(f"parent symlink no admitido: {relative}")
        parent = parent.parent
    resolved = unresolved.resolve(strict=True)
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ReceiptError(f"evidence path fuera de workspace: {relative}") from exc
    if not resolved.is_file():
        raise ReceiptError(f"evidence no es archivo regular: {relative}")
    return resolved


def _write_json(path: Path, value: Mapping[str, Any]) -> Path:
    atomic_write_bytes(
        path,
        (json.dumps(dict(value), ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return path


def _integrity(payload: Mapping[str, Any]) -> dict[str, str]:
    return {
        "algorithm": "SHA-256",
        "payload_sha256": canonical_digest(dict(payload)),
        "claim": INTEGRITY_CLAIM,
    }


def _receipt_id(prefix: str, payload: Mapping[str, Any]) -> str:
    identity = {key: value for key, value in payload.items() if key not in {"receipt_id", "integrity"}}
    return f"{prefix}-{canonical_digest(identity)[:12]}"


def create_evidence_receipt(
    root: str | Path,
    *,
    initiative: str,
    feature_run: str,
    actor_id: str,
    actor_type: str,
    core_version: str,
    policy: Mapping[str, Any],
    base_commit: str,
    head_commit: str,
    evidence: list[str],
    sensitivity: str,
    exit_code: int,
    verdict: str,
    claim_boundary: str,
    rollback: Mapping[str, Any],
    approval_required: bool = False,
    approval_roles: list[str] | None = None,
    recorded_at: datetime | None = None,
) -> Path:
    workspace = Path(root).resolve()
    if not workspace.is_dir():
        raise ReceiptError("workspace no existe")
    if not evidence:
        raise ReceiptError("evidence no puede estar vacio")
    rows = []
    for relative in sorted(set(evidence)):
        target = _safe_file(workspace, relative)
        content = target.read_bytes()
        rows.append({"path": relative, "sha256": sha256(content).hexdigest(), "size": len(content)})
    if verdict == "passed" and exit_code != 0:
        raise ReceiptError("verdict passed exige exit_code 0")
    if verdict in {"failed", "blocked"} and exit_code == 0:
        raise ReceiptError("verdict failed/blocked exige exit_code no cero")
    policy_id = policy.get("id")
    policy_version = policy.get("version")
    if not isinstance(policy_id, str) or not isinstance(policy_version, str):
        raise ReceiptError("policy exige id y version")
    payload: dict[str, Any] = {
        "schema": "edaios.evidence-receipt/v2",
        "initiative": initiative,
        "feature_run": feature_run,
        "actor": {"id": actor_id, "type": actor_type},
        "core_version": core_version,
        "policy": {
            "id": policy_id,
            "version": policy_version,
            "digest": canonical_digest(dict(policy)),
        },
        "base_commit": base_commit,
        "head_commit": head_commit,
        "evidence": rows,
        "sensitivity": sensitivity,
        "exit_code": exit_code,
        "verdict": verdict,
        "claim_boundary": claim_boundary,
        "rollback": dict(rollback),
        "approval": {
            "required": approval_required,
            "roles": sorted(set(approval_roles or [])),
        },
        "recorded_at": _timestamp(recorded_at),
    }
    payload["receipt_id"] = _receipt_id("EVR", payload)
    payload["integrity"] = _integrity(payload)
    SchemaRegistry().validate("evidence-receipt", payload)
    target = workspace / ".edaios/receipts" / f"{payload['receipt_id']}.json"
    with workspace_lock(workspace, "evidence-receipts"):
        _write_json(target, payload)
    return target


def create_approval_receipt(
    root: str | Path,
    *,
    initiative: str,
    feature_run: str,
    actor_id: str,
    authority_role: str,
    evidence_receipt_digest: str,
    verdict: str,
    statement: str,
    approved_at: datetime | None = None,
) -> Path:
    workspace = Path(root).resolve()
    if not workspace.is_dir():
        raise ReceiptError("workspace no existe")
    if verdict not in {"accepted", "rejected"}:
        raise ReceiptError("approval verdict invalido")
    payload: dict[str, Any] = {
        "schema": "edaios.approval-receipt/v1",
        "initiative": initiative,
        "feature_run": feature_run,
        "actor": {"id": actor_id, "type": "human"},
        "authority_role": authority_role,
        "evidence_receipt_digest": evidence_receipt_digest,
        "approved_at": _timestamp(approved_at),
        "verdict": verdict,
        "statement": statement,
    }
    payload["receipt_id"] = _receipt_id("APR", payload)
    payload["integrity"] = _integrity(payload)
    SchemaRegistry().validate("approval-receipt", payload)
    target = workspace / ".edaios/approvals" / f"{payload['receipt_id']}.json"
    with workspace_lock(workspace, "approval-receipts"):
        _write_json(target, payload)
    return target


def _load_receipt(value: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    return read_json(value) if isinstance(value, (str, Path)) else dict(value)


def verify_approval_receipt(
    value: str | Path | Mapping[str, Any],
    *,
    evidence_receipt_digest: str,
    allowed_roles: list[str] | None = None,
    expected_initiative: str | None = None,
    expected_feature_run: str | None = None,
) -> dict[str, Any]:
    payload = _load_receipt(value)
    SchemaRegistry().validate("approval-receipt", payload)
    integrity = payload.pop("integrity")
    if canonical_digest(payload) != integrity["payload_sha256"]:
        raise ReceiptError("approval receipt alterado")
    if payload["receipt_id"] != _receipt_id("APR", payload):
        raise ReceiptError("approval receipt_id no corresponde al payload")
    payload["integrity"] = integrity
    if payload["evidence_receipt_digest"] != evidence_receipt_digest:
        raise ReceiptError("approval no corresponde al evidence receipt")
    if expected_initiative is not None and payload["initiative"] != expected_initiative:
        raise ReceiptError("approval no corresponde a la iniciativa")
    if expected_feature_run is not None and payload["feature_run"] != expected_feature_run:
        raise ReceiptError("approval no corresponde al feature run")
    if payload["actor"]["type"] != "human":
        raise ReceiptError("approval requiere actor humano")
    if payload["verdict"] != "accepted":
        raise ReceiptError("approval no fue aceptado")
    if allowed_roles is not None and payload["authority_role"] not in allowed_roles:
        raise ReceiptError("rol de approval no autorizado")
    return {
        "status": "valid",
        "receipt_id": payload["receipt_id"],
        "actor_id": payload["actor"]["id"],
        "authority_role": payload["authority_role"],
        "initiative": payload["initiative"],
        "feature_run": payload["feature_run"],
        "claim": INTEGRITY_CLAIM,
    }


def verify_evidence_receipt(
    root: str | Path,
    value: str | Path | Mapping[str, Any],
    *,
    expected_head: str | None = None,
    expected_base: str | None = None,
    expected_policy: str | Path | Mapping[str, Any] | None = None,
    max_age_seconds: int | None = None,
    now: datetime | None = None,
    approval_required: bool = False,
    approval: str | Path | Mapping[str, Any] | None = None,
    approval_roles: list[str] | None = None,
    approval_authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    workspace = Path(root).resolve()
    payload = _load_receipt(value)
    SchemaRegistry().validate("evidence-receipt", payload)
    integrity = payload.pop("integrity")
    digest = canonical_digest(payload)
    if digest != integrity["payload_sha256"]:
        raise ReceiptError("evidence receipt alterado")
    if payload["receipt_id"] != _receipt_id("EVR", payload):
        raise ReceiptError("evidence receipt_id no corresponde al payload")
    payload["integrity"] = integrity
    if expected_head is not None and payload["head_commit"] != expected_head:
        raise ReceiptError("head commit no coincide")
    if expected_base is not None and payload["base_commit"] != expected_base:
        raise ReceiptError("base commit no coincide")
    policy_payload: dict[str, Any] | None = None
    if expected_policy is not None:
        policy_payload = _load_receipt(expected_policy)
        SchemaRegistry().validate("policy-profile", policy_payload)
        if canonical_digest(policy_payload) != payload["policy"]["digest"]:
            raise ReceiptError("policy digest no coincide")
        if policy_payload.get("id") != payload["policy"]["id"] or policy_payload.get("version") != payload["policy"]["version"]:
            raise ReceiptError("policy id/version no coincide")
    recorded = datetime.fromisoformat(payload["recorded_at"].replace("Z", "+00:00"))
    effective_max_age = max_age_seconds
    if policy_payload is not None:
        policy_max_age = policy_payload["max_receipt_age_seconds"]
        effective_max_age = (
            policy_max_age if max_age_seconds is None
            else min(max_age_seconds, policy_max_age)
        )
        if payload["sensitivity"] not in policy_payload["allowed_sensitivity"]:
            raise ReceiptError("sensibilidad no permitida por PolicyProfile")
    if effective_max_age is not None:
        if effective_max_age < 1:
            raise ReceiptError("max_age_seconds debe ser positivo")
        age = (_utc(now) - recorded.astimezone(timezone.utc)).total_seconds()
        if age < 0:
            raise ReceiptError("receipt fechado en el futuro")
        if age > effective_max_age:
            raise ReceiptError("evidence receipt obsoleto")
    for row in payload["evidence"]:
        target = _safe_file(workspace, row["path"])
        content = target.read_bytes()
        if len(content) != row["size"] or sha256(content).hexdigest() != row["sha256"]:
            raise ReceiptError(f"evidencia alterada: {row['path']}")
    approval_report = None
    receipt_approval = payload["approval"]
    must_approve = approval_required or receipt_approval["required"]
    if policy_payload is not None:
        must_approve = must_approve or policy_payload["approval_required"]
    if must_approve:
        if approval is None or approval_authority is None:
            raise ReceiptError("approval y AuthorityRegistry requeridos y ausentes")
        approval_payload = _load_receipt(approval)
        effective_roles = receipt_approval["roles"]
        if approval_roles is not None:
            effective_roles = sorted(set(effective_roles) & set(approval_roles))
            if not effective_roles:
                raise ReceiptError("no existe rol de approval comun entre receipt y policy")
        approval_report = verify_approval_receipt(
            approval_payload,
            evidence_receipt_digest=integrity["payload_sha256"],
            allowed_roles=effective_roles or None,
            expected_initiative=payload["initiative"],
            expected_feature_run=payload["feature_run"],
        )
        SchemaRegistry().validate("authority-registry", approval_authority)
        actors = {row["actor_id"]: row for row in approval_authority["actors"]}
        actor = actors.get(approval_report["actor_id"])
        if (
            not actor or not actor["active"] or actor["type"] != "human"
            or approval_report["authority_role"] not in actor["roles"]
            or "approve" not in actor["capabilities"]
        ):
            raise ReceiptError("approval actor no autorizado por AuthorityRegistry")
        approval_report["authority"] = "verified-against-local-registry"
    return {
        "status": "valid",
        "receipt_id": payload["receipt_id"],
        "evidence": len(payload["evidence"]),
        "head_commit": payload["head_commit"],
        "approval": approval_report,
        "claim": INTEGRITY_CLAIM,
    }


__all__ = [
    "INTEGRITY_CLAIM", "ReceiptError", "create_approval_receipt",
    "create_evidence_receipt", "verify_approval_receipt",
    "verify_evidence_receipt",
]
