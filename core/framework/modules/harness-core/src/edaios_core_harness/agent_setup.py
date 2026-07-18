"""Onboarding project-local, explícito, reversible y fail-closed."""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from edaios_conformance import SchemaRegistry
from edaios_core.io import atomic_write_bytes, workspace_lock


SETUP_SCHEMA = "edaios.agent-setup-receipt/v1"
SURFACES = {
    "codex": Path("AGENTS.md"),
    "claude-code": Path("CLAUDE.md"),
    "copilot": Path(".github/copilot-instructions.md"),
}
BEGIN = "<!-- EDAIOS-CORE:BEGIN agent-working-memory -->"
END = "<!-- EDAIOS-CORE:END agent-working-memory -->"
RECEIPTS_REL = Path(".edaios/agent-setup/receipts")
BACKUPS_REL = Path(".edaios/agent-setup/backups")
RECEIPT_ID_RE = re.compile(r"^SETUP-[0-9A-F]{24}$")


class AgentSetupError(ValueError):
    """El setup no puede planificarse o aplicarse de forma segura."""


class AgentSetupCollision(AgentSetupError):
    """Contenido administrado ambiguo o target inseguro."""


def _sha(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"


def _root(value: str | Path) -> Path:
    raw = Path(value).expanduser()
    if raw.is_symlink():
        raise AgentSetupError("workspace root no puede ser symlink")
    try:
        resolved = raw.resolve(strict=True)
    except OSError as exc:
        raise AgentSetupError("workspace root no resoluble") from exc
    if not resolved.is_dir():
        raise AgentSetupError("workspace root no es directorio")
    return resolved


def _target(root: Path, surface: str) -> Path:
    if surface not in SURFACES:
        raise AgentSetupError(f"surface no soportada: {surface}")
    candidate = root / SURFACES[surface]
    cursor = root
    for part in SURFACES[surface].parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise AgentSetupCollision(f"symlink no admitido en target: {cursor}")
    return candidate


def _project_relative(root: Path, value: str | Path, *, label: str) -> Path:
    """Normaliza una ruta lexical sin permitir absolute escape o traversal."""
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(root)
        except ValueError as exc:
            raise AgentSetupCollision(f"{label} fuera del workspace") from exc
    if not candidate.parts or ".." in candidate.parts:
        raise AgentSetupCollision(f"{label} fuera del workspace")
    return candidate


def _existing_project_file(root: Path, relative: Path, *, label: str) -> Path:
    """Resuelve un archivo regular sin aceptar symlinks en ningún componente."""
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise AgentSetupCollision(f"{label} symlink no admitido: {cursor}")
    try:
        resolved = cursor.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise AgentSetupError(f"{label} no resoluble bajo el workspace") from exc
    if not resolved.is_file():
        raise AgentSetupError(f"{label} no es archivo regular")
    return resolved


def _receipt_identity(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "surface": value["surface"],
        "target": value["target"],
        "before_digest": value["before_digest"],
        "after_digest": value["after_digest"],
        "integration_lock_digest": value["integration_lock_digest"],
    }


def _receipt_id(identity: dict[str, Any]) -> str:
    return "SETUP-" + sha256(_canonical(identity)).hexdigest()[:24].upper()


def _lock(root: Path) -> tuple[dict[str, Any], str]:
    path = root / ".specify" / "integrations.lock.json"
    if path.is_symlink() or not path.is_file():
        raise AgentSetupError(".specify/integrations.lock.json no resoluble")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgentSetupError("integrations.lock.json inválido") from exc
    if not isinstance(value, dict) or value.get("schema") != "edaios.speckit.integrations/v1":
        raise AgentSetupError("schema de integrations.lock no soportado")
    return value, _sha(raw)


def _block(surface: str, lock: dict[str, Any], lock_digest: str) -> str:
    source = str(lock.get("source", "unknown"))
    return "\n".join(
        [
            BEGIN,
            "## EDAIOS · memoria operativa del agente",
            "",
            f"Superficie: `{surface}` · integración: `{source}` · lock: `{lock_digest}`.",
            "",
            "- Git y los Knowledge Objects son la autoridad; `.edaios/` es local y reconstruible.",
            "- Busca primero con `edaios-core memory search`; no presentes memoria como evidencia.",
            "- Guarda solo observaciones T0/T1; una sugerencia nunca aprueba ni promueve.",
            "- Cierra la sesión con summary y enlaces a receipts; el summary sigue `unverified`.",
            "- Un conflicto `review-required` exige revisión humana antes de promoción.",
            "",
            "Este bloque es administrado por `edaios-core agent-setup`; no edites sus marcadores.",
            END,
        ]
    )


def _merge(current: str, block: str) -> str:
    begin_count = current.count(BEGIN)
    end_count = current.count(END)
    if begin_count != end_count or begin_count > 1:
        raise AgentSetupCollision("marcadores administrados incompletos o duplicados")
    if begin_count == 1:
        start = current.index(BEGIN)
        end = current.index(END, start) + len(END)
        if end <= start:
            raise AgentSetupCollision("orden de marcadores inválido")
        result = current[:start] + block + current[end:]
    else:
        prefix = current.rstrip()
        result = (prefix + "\n\n" if prefix else "") + block
    return result.rstrip() + "\n"


def plan_setup(root: str | Path, *, surface: str) -> dict[str, Any]:
    workspace = _root(root)
    target = _target(workspace, surface)
    lock, lock_digest = _lock(workspace)
    if target.exists() and not target.is_file():
        raise AgentSetupCollision("target existe y no es archivo")
    try:
        before = target.read_bytes() if target.exists() else b""
        current = before.decode("utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as exc:
        raise AgentSetupCollision("target no es texto UTF-8 legible") from exc
    desired = _merge(current, _block(surface, lock, lock_digest)).encode("utf-8")
    return {
        "schema": "edaios.agent-setup-plan/v1",
        "surface": surface,
        "target": target.relative_to(workspace).as_posix(),
        "target_exists": target.exists(),
        "before_digest": _sha(before),
        "after_digest": _sha(desired),
        "integration_lock_digest": lock_digest,
        "change": "unchanged" if before == desired else "write",
        "write_authorized": False,
        "project_local": True,
        "claim_boundary": "plan read-only; no configura $HOME ni concede autoridad",
        "_desired": desired,
        "_before": before,
    }


def _public_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in plan.items() if not key.startswith("_")}


def apply_setup(root: str | Path, *, surface: str) -> dict[str, Any]:
    workspace = _root(root)
    with workspace_lock(workspace, "agent-setup"):
        plan = plan_setup(workspace, surface=surface)
        if plan["change"] == "unchanged":
            return {**_public_plan(plan), "status": "unchanged", "receipt": None}
        identity = _receipt_identity({"surface": surface, **plan})
        receipt_id = _receipt_id(identity)
        local_root = workspace / ".edaios" / "agent-setup"
        backup = local_root / "backups" / receipt_id / "original.bin"
        receipt_path = local_root / "receipts" / f"{receipt_id}.json"
        target = workspace / str(plan["target"])
        atomic_write_bytes(backup, plan["_before"])
        atomic_write_bytes(target, plan["_desired"])
        receipt = {
            "schema": SETUP_SCHEMA,
            "receipt_id": receipt_id,
            "surface": surface,
            "target": plan["target"],
            "target_existed": plan["target_exists"],
            "before_digest": plan["before_digest"],
            "after_digest": plan["after_digest"],
            "integration_lock_digest": plan["integration_lock_digest"],
            "backup": backup.relative_to(workspace).as_posix(),
            "status": "applied",
            "project_local": True,
            "write_authorized": True,
            "claim_boundary": "setup local reversible; no concede autoridad ni configura $HOME",
        }
        receipt["integrity"] = {
            "algorithm": "SHA-256",
            "payload_sha256": _sha(_canonical(receipt)),
            "claim": "local-integrity-only; not identity or non-repudiation",
        }
        atomic_write_bytes(receipt_path, _canonical(receipt))
        return {
            **_public_plan(plan),
            "status": "applied",
            "write_authorized": True,
            "receipt": receipt_path.relative_to(workspace).as_posix(),
            "receipt_id": receipt_id,
        }


def verify_setup(root: str | Path, *, surface: str) -> dict[str, Any]:
    plan = plan_setup(root, surface=surface)
    return {
        **_public_plan(plan),
        "status": "valid" if plan["change"] == "unchanged" else "drift",
    }


def rollback_setup(root: str | Path, *, receipt: str | Path) -> dict[str, Any]:
    workspace = _root(root)
    with workspace_lock(workspace, "agent-setup"):
        # Toda la confianza se reconstruye después de adquirir el lock. Esto
        # evita usar un receipt o archivos que cambiaron entre validación y uso.
        receipt_rel = _project_relative(workspace, receipt, label="receipt")
        if receipt_rel.parent != RECEIPTS_REL:
            raise AgentSetupError(
                "receipt no resoluble bajo .edaios/agent-setup/receipts"
            )
        receipt_path = _existing_project_file(
            workspace, receipt_rel, label="receipt"
        )
        try:
            receipt_raw = receipt_path.read_bytes()
            value = json.loads(receipt_raw.decode("utf-8", errors="strict"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AgentSetupError("receipt JSON inválido") from exc
        if not isinstance(value, dict):
            raise AgentSetupError("receipt debe ser un objeto")
        try:
            SchemaRegistry().validate("agent-setup-receipt", value)
        except ValueError as exc:
            raise AgentSetupError("contrato de receipt inválido") from exc

        receipt_id = value["receipt_id"]
        if RECEIPT_ID_RE.fullmatch(receipt_id) is None:
            raise AgentSetupError("receipt_id inválido")
        expected_receipt_rel = RECEIPTS_REL / f"{receipt_id}.json"
        if receipt_rel != expected_receipt_rel:
            raise AgentSetupCollision("receipt path no corresponde a receipt_id")

        integrity = value["integrity"]
        unsigned = {key: item for key, item in value.items() if key != "integrity"}
        if integrity["payload_sha256"] != _sha(_canonical(unsigned)):
            raise AgentSetupError("integridad del receipt inválida")
        if _receipt_id(_receipt_identity(value)) != receipt_id:
            raise AgentSetupError("receipt_id no corresponde a la identidad del apply")

        surface = value["surface"]
        expected_target_rel = SURFACES[surface]
        if value["target"] != expected_target_rel.as_posix():
            raise AgentSetupCollision("target no corresponde a surface")
        target = _target(workspace, surface)

        expected_backup_rel = BACKUPS_REL / receipt_id / "original.bin"
        if value["backup"] != expected_backup_rel.as_posix():
            raise AgentSetupCollision("backup no corresponde a receipt_id")
        backup = _existing_project_file(
            workspace, expected_backup_rel, label="backup"
        )
        target = _existing_project_file(
            workspace, expected_target_rel, label="target"
        )

        target_bytes = target.read_bytes()
        backup_bytes = backup.read_bytes()
        if _sha(target_bytes) != value["after_digest"]:
            raise AgentSetupCollision(
                "target cambió después del apply; rollback bloqueado"
            )
        if _sha(backup_bytes) != value["before_digest"]:
            raise AgentSetupCollision("backup ausente o corrupto")
        # Releer el receipt justo antes de mutar mantiene su validación dentro
        # de la misma sección crítica incluso ante writers no cooperativos.
        if receipt_path.read_bytes() != receipt_raw:
            raise AgentSetupCollision("receipt cambió durante el rollback")

        if value.get("target_existed"):
            atomic_write_bytes(target, backup_bytes)
            if _sha(target.read_bytes()) != value["before_digest"]:
                raise AgentSetupError("restauración no coincide con before_digest")
        else:
            target.unlink()
            if target.exists() or target.is_symlink():
                raise AgentSetupError("target nuevo no pudo eliminarse")
        rolled = dict(value)
        rolled["status"] = "rolled-back"
        rolled["rolled_back_from"] = receipt_id
        rolled.pop("integrity", None)
        rolled["integrity"] = {
            "algorithm": "SHA-256",
            "payload_sha256": _sha(_canonical(rolled)),
            "claim": "local-integrity-only; not identity or non-repudiation",
        }
        rollback_path = receipt_path.with_name(receipt_path.stem + ".rollback.json")
        if rollback_path.is_symlink():
            raise AgentSetupCollision("rollback receipt symlink no admitido")
        atomic_write_bytes(rollback_path, _canonical(rolled))
    return {
        "status": "rolled-back",
        "receipt_id": receipt_id,
        "target": expected_target_rel.as_posix(),
        "restored_digest": value["before_digest"],
        "claim_boundary": "rollback local verificado; no cambia autoridad",
    }


__all__ = [
    "AgentSetupCollision", "AgentSetupError", "apply_setup", "plan_setup",
    "rollback_setup", "verify_setup",
]
