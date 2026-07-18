#!/usr/bin/env python3
"""Valida el candidato local y, bajo pedido, las precondiciones del sello final."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit


PUBLISHING = Path(__file__).resolve().parents[1] / "publishing"
if str(PUBLISHING) not in sys.path:
    sys.path.insert(0, str(PUBLISHING))

from prepare_core_release import (  # noqa: E402
    CLAIM_BOUNDARY,
    CUTOVER_TARGET_RELATIVE,
    FINAL_REQUIREMENTS,
    INPUT_SCHEMA,
    MANIFEST_RELATIVE,
    MANIFEST_SCHEMA,
    RELEASE_AUTHORITY_RELATIVE,
    RELEASE_POLICY_RELATIVE,
    VALIDATION_COMMANDS,
    ReleasePreparationError,
    _git,
    core_version,
    current_head,
    current_tree,
    full_worktree_clean,
    governed_input_digest,
    governed_worktree_dirty,
    release_artifacts,
    repository_root,
    tree_for_ref,
)

FRAMEWORK = Path(__file__).resolve().parents[2] / "core/framework"
for relative in (
    "modules/ess-core/src",
    "modules/conformance-core/src",
    "modules/harness-core/src",
):
    source = str(FRAMEWORK / relative)
    if source not in sys.path:
        sys.path.insert(0, source)

from edaios_conformance import SchemaRegistry, ValidationError  # noqa: E402
from edaios_core_harness import ReceiptError, verify_evidence_receipt  # noqa: E402


DIGEST = re.compile(r"^[0-9a-f]{64}$")
CUTOVER_SCHEMA = "edaios.git-cutover-receipt/v1"
REPORT_SCHEMA = "edaios.core-release-verification-report/v1"
CUTOVER_CLAIM = (
    "Observacion autorizada con evidencia referenciada del estado Git remoto; "
    "sin verificacion live del proveedor ni firma criptografica externa."
)
LOCAL_APPROVAL_BOUNDARY = (
    "Receipts, policy, autoridad y target coinciden con el HEAD candidato; "
    "no demuestra cutover remoto."
)
OBSERVED_SEAL_BOUNDARY = (
    "Cutover registrado por observacion autorizada y evidencia durable; "
    "no equivale a verificacion live o firma externa."
)
RELEASE_STATE_RELATIVE = Path(".specify/release.json")


class ReleaseSealError(RuntimeError):
    """El candidato o sus precondiciones de sello no son verificables."""


def _derive_unique_root(workspace: Path, current: str) -> tuple[str, str]:
    """Deriva la raíz nativa de Git sin aceptar historia incompleta o sustituida."""
    if os.environ.get("GIT_REPLACE_REF_BASE") is not None:
        raise ReleaseSealError(
            "genealogia single-root no admite GIT_REPLACE_REF_BASE"
        )
    shallow = _git(
        workspace, "rev-parse", "--is-shallow-repository"
    ).stdout.decode("ascii", errors="strict").strip()
    if shallow != "false":
        raise ReleaseSealError(
            "genealogia single-root exige un repositorio completo, no shallow"
        )

    replacements = _git(
        workspace,
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace/",
    ).stdout.decode("utf-8", errors="strict").splitlines()
    if replacements:
        raise ReleaseSealError(
            "genealogia single-root no admite refs/replace"
        )

    grafts_value = _git(
        workspace, "rev-parse", "--git-path", "info/grafts"
    ).stdout.decode("utf-8", errors="strict").strip()
    grafts_path = Path(grafts_value)
    if not grafts_path.is_absolute():
        grafts_path = workspace / grafts_path
    if grafts_path.exists() or grafts_path.is_symlink():
        raise ReleaseSealError("genealogia single-root no admite grafts")

    raw_roots = _git(
        workspace,
        "--no-replace-objects",
        "rev-list",
        "--max-parents=0",
        current,
    ).stdout.decode("ascii", errors="strict").splitlines()
    roots = [value.strip() for value in raw_roots if value.strip()]
    if len(roots) != 1:
        raise ReleaseSealError(
            "genealogia single-root exige exactamente una raiz alcanzable"
        )
    root_commit = roots[0]
    if re.fullmatch(r"[0-9a-f]{40,64}", root_commit) is None:
        raise ReleaseSealError("raiz Git derivada no es un object id canonico")
    parents = _git(
        workspace,
        "--no-replace-objects",
        "show",
        "-s",
        "--format=%P",
        root_commit,
    ).stdout.decode("ascii", errors="strict").strip()
    if parents:
        raise ReleaseSealError("raiz Git derivada contiene padres")
    root_tree = _git(
        workspace,
        "--no-replace-objects",
        "rev-parse",
        f"{root_commit}^{{tree}}",
    ).stdout.decode("ascii", errors="strict").strip()
    return root_commit, root_tree


def validate_release_state(
    root: str | Path,
    state_relative: str | Path = RELEASE_STATE_RELATIVE,
) -> dict[str, Any]:
    """Valida el baseline y resuelve, sin inferir, un candidato explícito."""
    workspace = repository_root(root)
    relative = Path(state_relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ReleaseSealError(f"path de release state inseguro: {relative}")
    state_path = workspace / relative
    current_parent = workspace
    for part in relative.parent.parts:
        current_parent = current_parent / part
        if current_parent.is_symlink():
            raise ReleaseSealError(
                f"CoreReleaseState usa parent symlink no permitido: {relative}"
            )
    try:
        state_path.resolve(strict=True).relative_to(workspace.resolve())
    except (OSError, ValueError) as exc:
        raise ReleaseSealError(
            f"CoreReleaseState debe vivir dentro del repositorio: {relative}"
        ) from exc
    state = _read_object(state_path, "CoreReleaseState")
    try:
        SchemaRegistry().validate("core-release-state", state)
    except ValidationError as exc:
        raise ReleaseSealError(f"CoreReleaseState no verificable: {exc}") from exc
    version = core_version(workspace)
    if state.get("version") != version:
        raise ReleaseSealError("CoreReleaseState diverge de VERSION")
    adr_id = str(state.get("governing_adr", ""))
    matches = list((workspace / "governance").glob(f"{adr_id}-*.md"))
    if len(matches) != 1 or "**Estado:** Aceptado" not in matches[0].read_text(
        encoding="utf-8"
    ):
        raise ReleaseSealError("CoreReleaseState no resuelve a un ADR aceptado")
    genealogy = state.get("genealogy")
    if not isinstance(genealogy, dict):
        raise ReleaseSealError("CoreReleaseState genealogy debe ser objeto")
    current = current_head(workspace)
    root_commit, root_tree = _derive_unique_root(workspace, current)
    candidate = state.get("active_candidate")
    return {
        "schema": "edaios.core-release-gate/v1",
        "status": "baseline-no-candidate" if candidate is None else "candidate-configured",
        "version": version,
        "baseline_root": root_commit,
        "baseline_tree": root_tree,
        "root_derivation": genealogy.get("root_derivation"),
        "canonical_branch": genealogy.get("canonical_branch"),
        "active_candidate": candidate,
        "publication": state.get("publication"),
        "promotion_allowed": False,
        "claim_boundary": state.get("claim_boundary"),
    }


def _canonical_digest(value: Any) -> str:
    content = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _read_object(path: Path, label: str) -> dict[str, Any]:
    lexical = path.expanduser()
    if lexical.is_symlink():
        raise ReleaseSealError(f"{label} usa symlink no permitido: {lexical}")
    try:
        target = lexical.resolve(strict=True)
    except OSError as exc:
        raise ReleaseSealError(f"{label} no resoluble: {path}") from exc
    if not target.is_file():
        raise ReleaseSealError(f"{label} ausente, symlink o no regular: {path}")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseSealError(f"{label} no es JSON valido: {path}") from exc
    if not isinstance(value, dict):
        raise ReleaseSealError(f"{label} debe ser un objeto JSON")
    return value


def _expect_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    if missing:
        raise ReleaseSealError(f"{label} incompleto; faltan: {', '.join(missing)}")


def _expect_exact_keys(
    value: dict[str, Any], required: set[str], label: str
) -> None:
    _expect_keys(value, required, label)
    extra = sorted(set(value) - required)
    if extra:
        raise ReleaseSealError(
            f"{label} contiene campos no soportados: {', '.join(extra)}"
        )


def _is_ancestor(root: Path, base: str, head: str) -> bool:
    if base == head:
        return True
    return _git(
        root, "merge-base", "--is-ancestor", base, head, check=False
    ).returncode == 0


def _manifest_is_committed(root: Path, relative: str, path: Path) -> bool:
    tracked = _git(
        root, "ls-files", "--error-unmatch", "--", relative, check=False
    )
    if tracked.returncode:
        return False
    committed = _git(root, "show", f"HEAD:{relative}", check=False)
    return committed.returncode == 0 and committed.stdout == path.read_bytes()


def _canonical_committed_file(
    root: Path,
    supplied: str | Path,
    label: str,
) -> Path:
    lexical = Path(supplied).expanduser()
    candidate = lexical if lexical.is_absolute() else root / lexical
    actual = candidate.resolve(strict=True)
    try:
        relative = actual.relative_to(root.resolve())
    except ValueError as exc:
        raise ReleaseSealError(
            f"{label} debe usar una ruta canonica gobernada dentro del repositorio"
        ) from exc
    current = root.resolve()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ReleaseSealError(f"{label} usa symlink no permitido: {relative}")
    if not _manifest_is_committed(root, relative.as_posix(), actual):
        raise ReleaseSealError(f"{label} no es identico al candidate HEAD")
    return actual


def _parse_timestamp(value: object, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseSealError(f"{label} no es date-time") from exc
    if parsed.tzinfo is None:
        raise ReleaseSealError(f"{label} exige timezone")
    return parsed.astimezone(timezone.utc)


def _normalize_repository(value: str) -> str:
    """Normaliza remote URLs sin conservar userinfo, secretos o .git."""
    candidate = value.strip()
    if not candidate or any(character.isspace() for character in candidate):
        raise ReleaseSealError("repository remoto vacio o inseguro")
    host: str | None = None
    path: str | None = None
    if "://" in candidate:
        parsed = urlsplit(candidate)
        if parsed.query or parsed.fragment or parsed.password:
            raise ReleaseSealError("remote.origin.url contiene secreto o metadata no admitida")
        if parsed.scheme in {"http", "https"} and parsed.username:
            raise ReleaseSealError("remote.origin.url HTTP contiene userinfo no admitido")
        if parsed.username and parsed.username != "git":
            raise ReleaseSealError("remote.origin.url contiene userinfo no admitido")
        host = parsed.hostname
        path = parsed.path
    else:
        match = re.fullmatch(r"(?:git@)?([^:]+):(.+)", candidate)
        if match:
            host, path = match.groups()
        else:
            pieces = candidate.split("/", 1)
            if len(pieces) == 2:
                host, path = pieces
    if not host or not path:
        raise ReleaseSealError("remote.origin.url no se puede normalizar")
    normalized_path = path.strip("/")
    if normalized_path.endswith(".git"):
        normalized_path = normalized_path[:-4]
    normalized = f"{host.lower()}/{normalized_path}"
    if re.fullmatch(r"[A-Za-z0-9.-]+(?:/[A-Za-z0-9._-]+)+", normalized) is None:
        raise ReleaseSealError("repository normalizado contiene caracteres no admitidos")
    return normalized


def _ci_gate_ids(workspace: Path) -> list[str]:
    registry = _read_object(workspace / ".specify/gates.json", "gate registry")
    result: list[str] = []
    for row in registry.get("gates", []):
        if not isinstance(row, dict):
            raise ReleaseSealError("gate registry contiene una fila invalida")
        scopes = {part.strip() for part in str(row.get("scope", "")).split(",")}
        if "ci" in scopes:
            gate_id = row.get("id")
            if not isinstance(gate_id, str) or not gate_id:
                raise ReleaseSealError("gate CI sin id")
            result.append(gate_id)
    if not result or len(result) != len(set(result)):
        raise ReleaseSealError("gate registry no define IDs CI unicos")
    return sorted(result)


def _load_release_contracts(
    workspace: Path,
    *,
    policy: str | Path,
    authority_registry: str | Path,
    cutover_target: str | Path,
    version: str,
) -> dict[str, Any]:
    """Carga únicamente contratos gobernados, comprometidos e idénticos a HEAD."""
    policy_path = _canonical_committed_file(
        workspace, policy, "PolicyProfile"
    )
    authority_path = _canonical_committed_file(
        workspace,
        authority_registry,
        "AuthorityRegistry",
    )
    target_path = _canonical_committed_file(
        workspace, cutover_target, "GitCutoverTarget"
    )
    policy_payload = _read_object(policy_path, "PolicyProfile")
    authority_payload = _read_object(authority_path, "AuthorityRegistry")
    target_payload = _read_object(target_path, "GitCutoverTarget")
    registry = SchemaRegistry()
    for name, payload, label in (
        ("policy-profile", policy_payload, "PolicyProfile"),
        ("authority-registry", authority_payload, "AuthorityRegistry"),
        ("git-cutover-target", target_payload, "GitCutoverTarget"),
    ):
        try:
            registry.validate(name, payload)
        except ValidationError as exc:
            raise ReleaseSealError(f"{label} no verificable: {exc}") from exc
    if policy_payload.get("version") != version:
        raise ReleaseSealError("PolicyProfile no coincide con VERSION")
    if authority_payload.get("version") != version:
        raise ReleaseSealError("AuthorityRegistry no coincide con VERSION")
    if target_payload.get("version") != version:
        raise ReleaseSealError("GitCutoverTarget no coincide con VERSION")
    if target_payload.get("status") != "proposed":
        raise ReleaseSealError(
            "GitCutoverTarget debe permanecer proposed hasta su aprobacion local"
        )
    if target_payload.get("component") != "edaios-core":
        raise ReleaseSealError("GitCutoverTarget no corresponde a edaios-core")
    expected_checks = _ci_gate_ids(workspace)
    if target_payload.get("required_checks") != expected_checks:
        raise ReleaseSealError(
            "GitCutoverTarget required_checks no coincide exactamente con gates CI"
        )
    expected_provider_evidence = {
        "branch-protection",
        "default-branch",
        "git-refs",
        "required-checks",
    }
    if set(target_payload.get("provider_evidence_kinds", [])) != expected_provider_evidence:
        raise ReleaseSealError(
            "GitCutoverTarget no exige toda la evidencia de proveedor"
        )
    publication = target_payload.get("attestation_publication")
    if not isinstance(publication, dict) or publication.get("required") is not True:
        raise ReleaseSealError("GitCutoverTarget debe exigir publicacion durable")
    origin = _git(
        workspace, "config", "--get", "remote.origin.url", check=False
    ).stdout.decode("utf-8", errors="strict").strip()
    if not origin:
        raise ReleaseSealError("aprobacion local exige remote.origin.url resoluble")
    normalized_origin = _normalize_repository(origin)
    if target_payload.get("repository") != normalized_origin:
        raise ReleaseSealError(
            "GitCutoverTarget repository no coincide con remote.origin.url normalizado"
        )
    return {
        "policy": policy_payload,
        "authority": authority_payload,
        "target": target_payload,
        "paths": {
            "policy": policy_path,
            "authority": authority_path,
            "target": target_path,
        },
    }


def _verify_integrity(payload: dict[str, Any], prefix: str, label: str) -> str:
    integrity = payload.get("integrity")
    if not isinstance(integrity, dict):
        raise ReleaseSealError(f"{label} sin integrity")
    _expect_exact_keys(
        integrity,
        {"algorithm", "payload_sha256", "claim"},
        f"{label}.integrity",
    )
    if integrity.get("algorithm") != "SHA-256" or integrity.get("claim") != (
        "local-integrity-only; not identity or non-repudiation"
    ):
        raise ReleaseSealError(f"{label} declara una integridad no soportada")
    recorded = integrity.get("payload_sha256")
    if not isinstance(recorded, str) or not DIGEST.fullmatch(recorded):
        raise ReleaseSealError(f"{label} integrity digest invalido")
    body = {key: value for key, value in payload.items() if key != "integrity"}
    if _canonical_digest(body) != recorded:
        raise ReleaseSealError(f"{label} alterado")
    identity = {
        key: value
        for key, value in payload.items()
        if key not in {"receipt_id", "integrity"}
    }
    expected_id = f"{prefix}-{_canonical_digest(identity)[:12]}"
    if payload.get("receipt_id") != expected_id:
        raise ReleaseSealError(f"{label} receipt_id no corresponde al payload")
    return recorded


def _verify_local_receipts(
    workspace: Path,
    evidence_path: Path,
    approval_path: Path,
    contracts: dict[str, Any],
    *,
    version: str,
    base_head: str,
    current: str,
) -> dict[str, Any]:
    evidence = _read_object(evidence_path, "EvidenceReceipt")
    if evidence.get("schema") != "edaios.evidence-receipt/v2":
        raise ReleaseSealError("EvidenceReceipt debe usar schema v2")
    if evidence.get("core_version") != version:
        raise ReleaseSealError("EvidenceReceipt no coincide con VERSION")
    if evidence.get("verdict") != "passed" or evidence.get("exit_code") != 0:
        raise ReleaseSealError("EvidenceReceipt final debe registrar passed/0")
    policy = contracts["policy"]
    authority = contracts["authority"]
    if policy.get("approval_required") is not True:
        raise ReleaseSealError("PolicyProfile final debe exigir approval")
    if evidence.get("sensitivity") not in policy.get("allowed_sensitivity", []):
        raise ReleaseSealError("PolicyProfile no admite la sensibilidad del receipt")
    evidence_approval = evidence.get("approval")
    if not isinstance(evidence_approval, dict) or evidence_approval.get("required") is not True:
        raise ReleaseSealError("EvidenceReceipt final debe exigir approval")
    if authority.get("initiative") != evidence.get("initiative"):
        raise ReleaseSealError(
            "AuthorityRegistry no corresponde a la iniciativa del EvidenceReceipt"
        )
    recorded_paths = {
        row.get("path") for row in evidence.get("evidence", []) if isinstance(row, dict)
    }
    required_paths = {
        RELEASE_POLICY_RELATIVE.as_posix(),
        RELEASE_AUTHORITY_RELATIVE.as_posix(),
        CUTOVER_TARGET_RELATIVE.as_posix(),
    }
    missing_paths = sorted(required_paths - recorded_paths)
    if missing_paths:
        raise ReleaseSealError(
            "EvidenceReceipt no cubre contratos canónicos: "
            + ", ".join(missing_paths)
        )
    try:
        report = verify_evidence_receipt(
            workspace,
            evidence_path,
            expected_head=current,
            expected_base=base_head,
            expected_policy=policy,
            max_age_seconds=policy["max_receipt_age_seconds"],
            approval_required=True,
            approval=approval_path,
            approval_roles=["principal-architect"],
            approval_authority=authority,
        )
    except (OSError, ValueError, ReceiptError, ValidationError) as exc:
        raise ReleaseSealError(f"receipts finales no verificables: {exc}") from exc
    approval = report.get("approval")
    if not isinstance(approval, dict):
        raise ReleaseSealError("ApprovalReceipt final no fue verificado")
    approval_payload = _read_object(approval_path, "ApprovalReceipt")
    recorded_at = _parse_timestamp(evidence.get("recorded_at"), "recorded_at")
    approved_at = _parse_timestamp(
        approval_payload.get("approved_at"), "approved_at"
    )
    if approved_at < recorded_at:
        raise ReleaseSealError("ApprovalReceipt precede al EvidenceReceipt")
    age = (datetime.now(timezone.utc) - approved_at).total_seconds()
    if age < 0 or age > policy["max_receipt_age_seconds"]:
        raise ReleaseSealError("ApprovalReceipt es futuro u obsoleto")
    return {
        "evidence_receipt_id": report["receipt_id"],
        "evidence_receipt_digest": evidence["integrity"]["payload_sha256"],
        "recorded_at": evidence["recorded_at"],
        "approval_receipt_id": approval_payload["receipt_id"],
        "approval_receipt_digest": approval_payload["integrity"]["payload_sha256"],
        "approved_at": approval_payload["approved_at"],
        "approval_actor": approval["actor_id"],
        "approval_role": approval["authority_role"],
        "authority": approval["authority"],
    }


def _verify_cutover_receipt(
    path: Path,
    *,
    version: str,
    head: str,
    tree: str,
    target: dict[str, Any],
    authority: dict[str, Any],
    local_receipts: dict[str, Any],
    approved_at: datetime,
) -> dict[str, Any]:
    payload = _read_object(path, "GitCutoverReceipt")
    try:
        SchemaRegistry().validate("git-cutover-receipt", payload)
    except ValidationError as exc:
        raise ReleaseSealError(f"GitCutoverReceipt no verificable: {exc}") from exc
    if payload["claim_boundary"] != CUTOVER_CLAIM:
        raise ReleaseSealError("GitCutoverReceipt debilita su claim boundary")
    if payload["version"] != version or payload["tag"] != f"v{version}":
        raise ReleaseSealError("GitCutoverReceipt no coincide con la version/tag")
    branch = payload["canonical_branch"]
    if not isinstance(branch, str) or not branch.strip():
        raise ReleaseSealError("canonical_branch no puede estar vacio")
    if branch != target["canonical_branch"]:
        raise ReleaseSealError("canonical_branch no coincide con el objetivo autorizado")
    if payload["default_branch"] != branch:
        raise ReleaseSealError("default branch no es la rama canonica")
    for field in (
        "commit",
        "remote_head",
        "remote_tag_target",
        "default_branch_head",
    ):
        if payload[field] != head:
            raise ReleaseSealError(f"GitCutoverReceipt diverge en {field}")
    if payload["tree"] != tree:
        raise ReleaseSealError("GitCutoverReceipt diverge en tree")
    if payload["legacy_history_merged"] is not False:
        raise ReleaseSealError("el cutover no puede mezclar la historia legacy")
    check_ids = {row["id"] for row in payload["required_checks"]}
    if check_ids != set(target["required_checks"]):
        raise ReleaseSealError(
            "GitCutoverReceipt required_checks no coincide exactamente con target"
        )
    protection = payload["branch_protection"]
    if not isinstance(protection, dict):
        raise ReleaseSealError("branch_protection debe ser objeto")
    _expect_exact_keys(
        protection,
        {"observed", "force_push_allowed"},
        "branch_protection",
    )
    if protection != {"observed": True, "force_push_allowed": False}:
        raise ReleaseSealError("branch protection no fue observada fail-closed")
    observer = payload["observer"]
    if not isinstance(observer, dict):
        raise ReleaseSealError("observer debe ser objeto")
    _expect_exact_keys(observer, {"id", "type"}, "observer")
    if (
        not isinstance(observer["id"], str)
        or not observer["id"].strip()
        or observer["type"] not in {"human", "service"}
    ):
        raise ReleaseSealError("observer no es una identidad admitida")
    if payload["repository"] != target["repository"]:
        raise ReleaseSealError("repository no coincide con GitCutoverTarget")
    provider_evidence = payload["provider_evidence"]
    provider_kinds = {row["kind"] for row in provider_evidence}
    if provider_kinds != set(target["provider_evidence_kinds"]):
        raise ReleaseSealError(
            "GitCutoverReceipt no cubre exactamente evidencia requerida del proveedor"
        )
    publication = payload["attestation_publication"]
    if publication["kind"] not in target["attestation_publication"]["allowed_kinds"]:
        raise ReleaseSealError(
            "publicacion durable no usa un destino autorizado por target"
        )
    published_subjects = {
        row["kind"]: (row["receipt_id"], row["sha256"])
        for row in publication["subjects"]
    }
    expected_subjects = {
        "evidence-receipt": (
            local_receipts["evidence_receipt_id"],
            local_receipts["evidence_receipt_digest"],
        ),
        "approval-receipt": (
            local_receipts["approval_receipt_id"],
            local_receipts["approval_receipt_digest"],
        ),
    }
    if published_subjects != expected_subjects:
        raise ReleaseSealError(
            "publicacion durable no liga los receipts locales aprobados"
        )
    observed = _parse_timestamp(payload["observed_at"], "observed_at")
    if observed < approved_at:
        raise ReleaseSealError("GitCutoverReceipt precede a la aprobacion local")
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    if age < 0 or age > 86400:
        raise ReleaseSealError("GitCutoverReceipt es futuro u obsoleto")
    try:
        SchemaRegistry().validate("authority-registry", authority)
    except ValidationError as exc:
        raise ReleaseSealError(f"AuthorityRegistry no verificable: {exc}") from exc
    actors = {row["actor_id"]: row for row in authority["actors"]}
    actor = actors.get(observer["id"])
    if (
        not actor
        or not actor["active"]
        or actor["type"] != observer["type"]
        or "release-observer" not in actor["roles"]
        or "release:observe" not in actor["capabilities"]
    ):
        raise ReleaseSealError("observer no autorizado por AuthorityRegistry")
    digest = _verify_integrity(payload, "CUT", "GitCutoverReceipt")
    return {
        "receipt_id": payload["receipt_id"],
        "digest": digest,
        "repository": payload["repository"],
        "canonical_branch": branch,
        "tag": payload["tag"],
        "required_checks": sorted(check_ids),
        "provider_evidence": provider_evidence,
        "attestation_publication": publication,
        "observer": observer,
        "observed_at": payload["observed_at"],
        "verification_mode": "authorized-observation",
    }


def validate_release_candidate(
    root: str | Path,
    *,
    manifest_relative: str | Path = MANIFEST_RELATIVE,
    require_local_approval: bool = False,
    require_final_seal: bool = False,
    evidence_receipt: str | Path | None = None,
    approval_receipt: str | Path | None = None,
    policy: str | Path | None = None,
    authority_registry: str | Path | None = None,
    cutover_target: str | Path | None = None,
    cutover_receipt: str | Path | None = None,
    canonical_branch: str | None = None,
    artifact_builder: Callable[[Path, str], dict[str, Any]] = release_artifacts,
) -> dict[str, Any]:
    workspace = repository_root(root)
    relative_path = Path(manifest_relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ReleaseSealError(f"path de manifest inseguro: {relative_path}")
    relative = relative_path.as_posix()
    manifest_path = workspace / relative_path
    manifest = _read_object(manifest_path, "release candidate")
    try:
        SchemaRegistry().validate("core-release-candidate", manifest)
    except ValidationError as exc:
        raise ReleaseSealError(f"release candidate no verificable: {exc}") from exc
    _expect_exact_keys(
        manifest,
        {
            "schema",
            "component",
            "version",
            "status",
            "base_head",
            "base_tree",
            "branch",
            "governed_inputs",
            "artifacts",
            "validation_commands",
            "final_seal",
            "claim_boundary",
        },
        "release candidate",
    )
    if manifest["schema"] != MANIFEST_SCHEMA:
        raise ReleaseSealError("schema de release candidate no soportado")
    if manifest["component"] != "edaios-core":
        raise ReleaseSealError("component debe ser edaios-core")
    version = core_version(workspace)
    if manifest["version"] != version:
        raise ReleaseSealError(
            f"version diverge: manifest={manifest['version']} VERSION={version}"
        )
    if manifest["claim_boundary"] != CLAIM_BOUNDARY:
        raise ReleaseSealError("claim boundary de candidato fue debilitado")
    if manifest["validation_commands"] != VALIDATION_COMMANDS:
        raise ReleaseSealError("comandos de validacion del candidato divergen")
    if manifest["status"] != "prepared":
        raise ReleaseSealError("release candidate v2 solo admite status prepared")

    expected_inputs = governed_input_digest(workspace, relative_path)
    recorded_inputs = manifest["governed_inputs"]
    if not isinstance(recorded_inputs, dict):
        raise ReleaseSealError("governed_inputs debe ser objeto")
    _expect_exact_keys(
        recorded_inputs,
        {
            "schema",
            "algorithm",
            "digest",
            "file_count",
            "deleted_count",
            "scope",
            "excluded",
        },
        "governed_inputs",
    )
    if recorded_inputs.get("schema") != INPUT_SCHEMA:
        raise ReleaseSealError("schema de governed_inputs no soportado")
    for field in (
        "algorithm",
        "digest",
        "file_count",
        "deleted_count",
        "scope",
        "excluded",
    ):
        if recorded_inputs.get(field) != expected_inputs[field]:
            raise ReleaseSealError(f"governed_inputs diverge en {field}")

    expected_artifacts = artifact_builder(workspace, version)
    if manifest["artifacts"] != expected_artifacts:
        raise ReleaseSealError("artefactos de release divergen del candidato")

    current = current_head(workspace)
    base = manifest["base_head"]
    if not isinstance(base, str):
        raise ReleaseSealError("base_head invalido")
    if manifest["base_tree"] != tree_for_ref(workspace, base):
        raise ReleaseSealError("base_tree no coincide con el tree de base_head")
    dirty = governed_worktree_dirty(workspace, relative_path)
    if not _is_ancestor(workspace, base, current):
        raise ReleaseSealError(
            f"base_head no es ancestro de current HEAD: base={base} current={current}"
        )

    final_config = manifest["final_seal"]
    if isinstance(final_config, dict):
        _expect_exact_keys(
            final_config,
            {"required", "requirements", "present"},
            "final_seal",
        )
    if (
        not isinstance(final_config, dict)
        or final_config.get("required") is not True
        or final_config.get("requirements") != FINAL_REQUIREMENTS
        or final_config.get("present") is not False
    ):
        raise ReleaseSealError("candidate manifest no puede autoafirmar un sello final")
    locally_approved = require_local_approval or require_final_seal
    receipts: dict[str, Any] | None = None
    contracts: dict[str, Any] | None = None
    if locally_approved:
        if not full_worktree_clean(workspace):
            raise ReleaseSealError("aprobacion local exige un commit con worktree limpio")
        if not _manifest_is_committed(workspace, relative, manifest_path):
            raise ReleaseSealError(
                "aprobacion local exige manifest trackeado e identico al current HEAD"
            )
        if any(
            value is None
            for value in (
                evidence_receipt,
                approval_receipt,
                policy,
                authority_registry,
                cutover_target,
            )
        ):
            raise ReleaseSealError(
                "aprobacion local exige EvidenceReceipt, ApprovalReceipt, "
                "PolicyProfile, AuthorityRegistry y GitCutoverTarget"
            )
        contracts = _load_release_contracts(
            workspace,
            policy=policy,
            authority_registry=authority_registry,
            cutover_target=cutover_target,
            version=version,
        )
        if (
            canonical_branch is not None
            and canonical_branch != contracts["target"]["canonical_branch"]
        ):
            raise ReleaseSealError(
                "canonical_branch no coincide con GitCutoverTarget canónico"
            )
        receipts = _verify_local_receipts(
            workspace,
            Path(evidence_receipt),
            Path(approval_receipt),
            contracts,
            version=version,
            base_head=base,
            current=current,
        )

    cutover: dict[str, Any] | None = None
    if require_final_seal:
        if cutover_receipt is None:
            raise ReleaseSealError(
                "sello final exige GitCutoverReceipt"
            )
        if contracts is None or receipts is None:
            raise ReleaseSealError("sello final exige aprobacion local verificable")
        cutover = _verify_cutover_receipt(
            Path(cutover_receipt),
            version=version,
            head=current,
            tree=current_tree(workspace),
            target=contracts["target"],
            authority=contracts["authority"],
            local_receipts=receipts,
            approved_at=_parse_timestamp(receipts["approved_at"], "approved_at"),
        )

    readiness = "prepared"
    if not dirty and _manifest_is_committed(workspace, relative, manifest_path):
        readiness = "ready-for-approval"
    status = "valid"
    if locally_approved:
        status = "locally-approved"
    if require_final_seal:
        status = "sealed-by-authorized-observation"

    claim_boundary = CLAIM_BOUNDARY
    if locally_approved:
        claim_boundary = LOCAL_APPROVAL_BOUNDARY
    if require_final_seal:
        claim_boundary = OBSERVED_SEAL_BOUNDARY

    report = {
        "schema": REPORT_SCHEMA,
        "status": status,
        "candidate_status": manifest["status"],
        "readiness": readiness,
        "verification_mode": (
            "authorized-observation" if require_final_seal else "local-validation"
        ),
        "provider_live_verified": False,
        "version": version,
        "base_head": base,
        "base_tree": manifest["base_tree"],
        "current_head": current,
        "governed_inputs_sha256": expected_inputs["digest"],
        "release_artifacts_sha256": expected_artifacts["digest"],
        "governed_worktree_clean": not dirty,
        "full_worktree_clean": full_worktree_clean(workspace),
        "receipts": receipts,
        "target": contracts["target"] if contracts else None,
        "cutover": cutover,
        "claim_boundary": claim_boundary,
    }
    try:
        SchemaRegistry().validate("core-release-verification-report", report)
    except ValidationError as exc:
        raise ReleaseSealError(
            f"reporte de verificacion no cumple contrato: {exc}"
        ) from exc
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--state", default=RELEASE_STATE_RELATIVE.as_posix())
    parser.add_argument("--manifest")
    parser.add_argument("--require-local-approval", action="store_true")
    parser.add_argument("--require-final-seal", action="store_true")
    parser.add_argument("--evidence-receipt")
    parser.add_argument("--approval-receipt")
    parser.add_argument("--policy")
    parser.add_argument("--authority-registry")
    parser.add_argument("--cutover-target")
    parser.add_argument("--cutover-receipt")
    parser.add_argument("--canonical-branch")
    parser.add_argument(
        "--json", action="store_true",
        help="emite edaios.core-release-verification-report/v1",
    )
    args = parser.parse_args(argv)
    try:
        release_arguments = (
            args.require_local_approval,
            args.require_final_seal,
            args.evidence_receipt,
            args.approval_receipt,
            args.policy,
            args.authority_registry,
            args.cutover_target,
            args.cutover_receipt,
            args.canonical_branch,
        )
        release_state = validate_release_state(Path(args.root), args.state)
        manifest_relative = args.manifest
        if manifest_relative is None and not any(release_arguments):
            configured = release_state.get("active_candidate")
            if configured is None:
                if args.json:
                    print(json.dumps(release_state, ensure_ascii=False, sort_keys=True))
                else:
                    print(
                        f"[core-release-seal] N/A: {release_state['version']} baseline · "
                        f"{release_state['status']} · promotion_allowed=false · "
                        "sin candidato activo"
                    )
                return 0
            if not isinstance(configured, dict):
                raise ReleaseSealError("active_candidate debe ser objeto o null")
            manifest_relative = configured.get("manifest")
        if manifest_relative is None:
            raise ReleaseSealError("--manifest es obligatorio para validar un candidato")
        report = validate_release_candidate(
            Path(args.root),
            manifest_relative=manifest_relative,
            require_local_approval=args.require_local_approval,
            require_final_seal=args.require_final_seal,
            evidence_receipt=args.evidence_receipt,
            approval_receipt=args.approval_receipt,
            policy=args.policy,
            authority_registry=args.authority_registry,
            cutover_target=args.cutover_target,
            cutover_receipt=args.cutover_receipt,
            canonical_branch=args.canonical_branch,
        )
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        ReceiptError,
        ValidationError,
        ReleasePreparationError,
        ReleaseSealError,
    ) as exc:
        print(f"[core-release-seal] FAIL: {exc}")
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"[core-release-seal] OK: {report['version']} · "
            f"{report['candidate_status']}/{report['readiness']} · "
            f"{report['status']} · {report['verification_mode']} · "
            f"HEAD {report['current_head']} · "
            f"sha256:{report['governed_inputs_sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
