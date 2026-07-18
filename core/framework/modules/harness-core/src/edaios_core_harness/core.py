"""Executable local control plane; coordinates and validates, never approves."""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping

from edaios_conformance.schemas import SchemaRegistry
from edaios_core.io import atomic_write_bytes, workspace_lock

from .receipts import (
    ReceiptError,
    create_approval_receipt,
    create_evidence_receipt,
    verify_approval_receipt,
    verify_evidence_receipt,
)

EXPECTED_HARNESSES = {
    "sdd-orchestrator", "request-router", "phase-dag", "strict-tdd",
    "artifact-store", "result-contract", "memory-port", "permission-guard",
    "human-acceptance", "backup-rollback", "telemetry", "command-wrapper",
}


class HarnessError(ValueError):
    pass


class ContractError(ValueError):
    pass


def _timestamp(value: str | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("timestamp invalido") from exc
    if parsed.tzinfo is None:
        raise ContractError("timestamp exige timezone")
    return parsed.astimezone(timezone.utc)


class CoreHarness:
    def __init__(self, resource_root: str | Path | None = None) -> None:
        self.resource_root = (
            Path(resource_root).resolve()
            if resource_root
            else Path(str(files("edaios_core_harness").joinpath("resources")))
        )

    def _load(self, name: str) -> dict[str, Any]:
        value = json.loads((self.resource_root / name).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise HarnessError(f"{name}: raiz debe ser objeto")
        return value

    def _validate_dag(self) -> list[dict[str, Any]]:
        dag = self._load("phase-dag.json")
        phases = dag.get("phases", [])
        phase_ids = [row.get("id") for row in phases]
        expected = [
            "constitution", "specify", "clarify", "checklist",
            "plan", "tasks", "analyze", "implement",
        ]
        if phase_ids != expected:
            raise HarnessError("phase DAG no coincide con Spec Kit")
        known = set(phase_ids)
        indegree = {item: 0 for item in known}
        outgoing = {item: [] for item in known}
        for row in phases:
            dependencies = row.get("dependencies", [])
            if not isinstance(dependencies, list):
                raise HarnessError(f"{row.get('id')}: dependencies invalido")
            for dependency in dependencies:
                if dependency not in known:
                    raise HarnessError(f"fase desconocida: {dependency}")
                indegree[row["id"]] += 1
                outgoing[dependency].append(row["id"])
        queue = deque(item for item, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for child in outgoing[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(known):
            raise HarnessError("phase DAG ciclico")
        return phases

    def validate(self) -> dict[str, Any]:
        registry = self._load("harness-registry.json")
        rows = registry.get("harnesses", [])
        ids = [row.get("id") for row in rows]
        if set(ids) != EXPECTED_HARNESSES or len(ids) != len(set(ids)):
            raise HarnessError("harness registry fuera del contrato")
        required = {
            "id", "purpose", "authority", "inputs", "outputs", "invariants",
            "maturity", "implementation",
        }
        for row in rows:
            if required - set(row):
                raise HarnessError(f"{row.get('id')}: contrato incompleto")
            if row["authority"] not in {"ADR-0002", "ADR-0003", "ADR-0005", "ADR-0011"}:
                raise HarnessError(f"{row['id']}: autoridad no resoluble")
            if row["maturity"] != "enforced":
                raise HarnessError(f"{row['id']}: madurez no coincide con el release")
            implementation = row["implementation"]
            if not isinstance(implementation, str) or not callable(getattr(self, implementation, None)):
                raise HarnessError(f"{row['id']}: implementation no ejecutable")
        phases = self._validate_dag()
        modes = self._load("execution-modes.json").get("modes", {})
        if set(modes) != {"fast", "standard", "controlled"}:
            raise HarnessError("modos incompletos")
        for mode in modes.values():
            if not {"traceability", "human-authority", "validation"} <= set(mode.get("invariants", [])):
                raise HarnessError("un modo debilita invariantes")
        return {
            "status": "ok",
            "version": registry["version"],
            "harnesses": len(rows),
            "enforced": len(rows),
            "phases": len(phases),
            "modes": sorted(modes),
            "execution_policy": "coordinate-and-validate-only",
        }

    # 1. sdd-orchestrator
    def next_phase(self, completed: list[str]) -> dict[str, Any]:
        phases = self._validate_dag()
        ordered = [row["id"] for row in phases]
        if len(completed) != len(set(completed)) or any(item not in ordered for item in completed):
            raise ContractError("completed contiene fases duplicadas o desconocidas")
        if completed != ordered[: len(completed)]:
            raise ContractError("las fases completadas no respetan el DAG")
        next_value = ordered[len(completed)] if len(completed) < len(ordered) else None
        return {"status": "complete" if next_value is None else "ready", "next_phase": next_value, "executes": False}

    # 2. request-router
    def route_request(self, *, intent: str, declared_kind: str) -> dict[str, Any]:
        routes = {
            "task": "task-lane", "feature": "spec-kit", "rfc": "governance-rfc",
            "adr": "governance-adr", "incident": "incident-lane",
        }
        if not intent.strip() or declared_kind not in routes:
            raise ContractError("intent no vacio y declared_kind admitido son obligatorios")
        return {"route": routes[declared_kind], "declared_kind": declared_kind, "reason": "clasificacion declarada; no inferida", "executes": False}

    # 3. phase-dag (public operation)
    def validate_phase_dag(self) -> dict[str, Any]:
        phases = self._validate_dag()
        return {"status": "acyclic", "order": [row["id"] for row in phases]}

    # 4. strict-tdd
    def strict_tdd(self, stages: list[str]) -> dict[str, Any]:
        expected = self._load("phase-dag.json").get("strict_tdd", [])
        if stages != expected:
            raise ContractError(f"TDD exige secuencia completa {expected}")
        return {"status": "valid", "stages": list(stages), "tests_first": True}

    @staticmethod
    def _workspace_file(root: str | Path, relative: str) -> tuple[Path, Path]:
        workspace = Path(root).resolve()
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ContractError("ruta fuera del workspace")
        unresolved = workspace / candidate
        if unresolved.is_symlink():
            raise ContractError("symlink no admitido")
        parent = unresolved.parent
        while parent != workspace:
            if parent.is_symlink():
                raise ContractError("parent symlink no admitido")
            parent = parent.parent
        target = unresolved.resolve(strict=True)
        try:
            target.relative_to(workspace)
        except ValueError as exc:
            raise ContractError("ruta fuera del workspace") from exc
        if not target.is_file():
            raise ContractError("artefacto no es archivo")
        return workspace, target

    # 5. artifact-store
    def store_artifact(self, root: str | Path, *, artifact: str, source: str) -> Path:
        workspace, target = self._workspace_file(root, artifact)
        if not source.strip():
            raise ContractError("source es obligatorio")
        content = target.read_bytes()
        record = {
            "schema": "edaios.artifact-record/v1",
            "artifact": artifact,
            "source": source,
            "sha256": sha256(content).hexdigest(),
            "size": len(content),
            "authority": "Git path supplied by caller; not promoted automatically",
        }
        receipt = workspace / ".edaios/artifacts" / f"{record['sha256']}.json"
        with workspace_lock(workspace, "artifact-store"):
            atomic_write_bytes(receipt, (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        return receipt

    # 6. result-contract
    def normalize_result(
        self, *, status: str, summary: str, exit_code: int,
        evidence: list[str], claim_boundary: str,
    ) -> dict[str, Any]:
        if status not in {"passed", "failed", "blocked"}:
            raise ContractError("status no tipado")
        if not summary.strip() or not claim_boundary.strip() or not evidence:
            raise ContractError("summary, evidence y claim_boundary son obligatorios")
        if (status == "passed") != (exit_code == 0):
            raise ContractError("status y exit_code son incompatibles")
        return {
            "schema": "edaios.result/v1", "status": status, "summary": summary,
            "exit_code": exit_code, "evidence": sorted(set(evidence)),
            "claim_boundary": claim_boundary,
        }

    # 7. memory-port
    def memory_port(self, *, tier: str, record: Mapping[str, Any]) -> dict[str, Any]:
        if tier not in {"durable", "local", "ephemeral"} or not record:
            raise ContractError("tier admitido y record no vacio son obligatorios")
        if tier == "durable" and not record.get("git_path"):
            raise ContractError("memoria durable exige git_path explicito")
        if tier != "durable" and record.get("authoritative") is True:
            raise ContractError("memoria local o efimera no puede autoafirmar autoridad")
        channels = {
            "durable": "canonical",
            "local": "local-working",
            "ephemeral": "ephemeral",
        }
        return {
            "tier": tier,
            "channel": channels[tier],
            "authoritative": tier == "durable",
            "rebuildable": tier != "durable",
            "persisted_by_core": False,
            "adapter_allowed": tier == "local",
            "forbidden_operations": [
                "approve", "decide", "promote", "write-canonical"
            ] if tier != "durable" else [],
            "claim_boundary": (
                "clasificación de memoria; el harness no persiste, aprueba ni promueve"
            ),
            "digest": sha256(json.dumps(dict(record), sort_keys=True).encode()).hexdigest(),
        }

    # 8. permission-guard
    def permission_guard(
        self,
        *,
        request: Mapping[str, Any],
        authority_registry: Mapping[str, Any],
        grants: list[Mapping[str, Any]] | None = None,
        now: str | None = None,
    ) -> dict[str, Any]:
        SchemaRegistry().validate("authority-registry", authority_registry)
        actor_id = request.get("actor_id")
        capability = request.get("capability")
        scope = request.get("scope")
        if not all(isinstance(item, str) and item for item in (actor_id, capability, scope)):
            raise ContractError("request exige actor_id, capability y scope")
        actors = {row["actor_id"]: row for row in authority_registry["actors"]}
        actor = actors.get(actor_id)
        # `outcome:verify` is canonical. The historical spelling is rejected,
        # rather than silently normalized, so policy and runtime cannot drift.
        aliases = {"verify-outcome": "outcome:verify"}
        if capability in aliases:
            raise ContractError("AUTHORITY_DENIED: capability alias no canonico")
        reserved = {"approve", "accept-adr", "accept-risk", "outcome:verify", "merge", "publish"}
        if actor and actor["type"] != "human" and capability in reserved:
            raise ContractError("AUTHORITY_DENIED: capacidad reservada a una persona")
        if actor and actor["active"] and capability in actor["capabilities"]:
            return {"decision": "allow", "actor_id": actor_id, "basis": "direct-authority", "scope": scope}
        instant = _timestamp(now)
        for grant in grants or []:
            SchemaRegistry().validate("delegation-grant", grant)
            if grant["initiative"] != authority_registry["initiative"]:
                continue
            grantor = actors.get(grant["grantor_actor_id"])
            grantee = actors.get(grant["grantee_actor_id"])
            if (
                not grantor or not grantor["active"] or grantor["type"] != "human"
                or "delegate" not in grantor["capabilities"]
                or capability not in grantor["capabilities"]
            ):
                continue
            if not grantee or not grantee["active"]:
                continue
            if grant["grantee_actor_id"] != actor_id or grant["revoked"]:
                continue
            if capability not in grant["capabilities"] or scope not in grant["scope"]:
                continue
            start = _timestamp(grant["valid_from"])
            end = _timestamp(grant["valid_until"])
            if start <= instant < end:
                return {"decision": "allow", "actor_id": actor_id, "basis": grant["id"], "scope": scope}
        raise ContractError("AUTHORITY_DENIED: sin autoridad directa o delegacion activa")

    # 9. human-acceptance
    def human_acceptance(
        self,
        approval: str | Path | Mapping[str, Any],
        *,
        evidence_receipt_digest: str,
        allowed_roles: list[str],
        authority_registry: Mapping[str, Any],
    ) -> dict[str, Any]:
        SchemaRegistry().validate("authority-registry", authority_registry)
        report = verify_approval_receipt(
            approval,
            evidence_receipt_digest=evidence_receipt_digest,
            allowed_roles=allowed_roles,
            expected_initiative=authority_registry["initiative"],
        )
        actors = {row["actor_id"]: row for row in authority_registry["actors"]}
        actor = actors.get(report["actor_id"])
        if (
            authority_registry["initiative"] != report["initiative"]
            or not actor or not actor["active"] or actor["type"] != "human"
            or report["authority_role"] not in actor["roles"]
            or "approve" not in actor["capabilities"]
        ):
            raise ContractError("approval actor no autorizado por AuthorityRegistry")
        report["authority"] = "verified-against-local-registry"
        return report

    # 10. backup-rollback
    def backup_rollback(self, plan: Mapping[str, Any]) -> dict[str, Any]:
        required = {"target_ref", "steps", "verification", "owner"}
        if required - set(plan):
            raise ContractError(f"rollback incompleto: {sorted(required - set(plan))}")
        if not isinstance(plan["steps"], list) or not plan["steps"]:
            raise ContractError("rollback exige steps")
        if any(not isinstance(plan[key], str) or not plan[key].strip() for key in ("target_ref", "verification", "owner")):
            raise ContractError("rollback contiene campos vacios")
        return {"status": "ready", "target_ref": plan["target_ref"], "automatic_apply": False}

    # 11. telemetry
    def telemetry(self, event: Mapping[str, Any]) -> dict[str, Any]:
        forbidden = {"outcome", "value", "business_value", "accepted"} & set(event)
        if forbidden:
            raise ContractError(f"telemetry no puede inferir {sorted(forbidden)}")
        required = {"event_name", "observed_at", "source", "attributes"}
        if required - set(event) or not isinstance(event.get("attributes"), Mapping):
            raise ContractError("telemetry exige evento, fecha, fuente y attributes")
        _timestamp(str(event["observed_at"]))
        return {
            "schema": "edaios.telemetry-observation/v1",
            "event_name": event["event_name"],
            "observed_at": event["observed_at"],
            "source": event["source"],
            "attributes": dict(event["attributes"]),
            "claim_boundary": "observation only; not an outcome",
        }

    # 12. command-wrapper
    def command_wrapper(
        self, *, command: list[str], exit_code: int, stdout: bytes = b"", stderr: bytes = b""
    ) -> dict[str, Any]:
        if not command or any(not isinstance(item, str) or not item for item in command):
            raise ContractError("command debe ser argv no vacio")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            raise ContractError("exit_code debe ser entero")
        return {
            "schema": "edaios.command-observation/v1",
            "argv": command,
            "exit_code": exit_code,
            "stdout_sha256": sha256(stdout).hexdigest(),
            "stderr_sha256": sha256(stderr).hexdigest(),
            "executed_by_core": False,
        }

    # Receipt operations are public harness entry points.
    evidence_receipt = staticmethod(create_evidence_receipt)
    verify_evidence = staticmethod(verify_evidence_receipt)
    approval_receipt = staticmethod(create_approval_receipt)

    def receipt(self, *_args: Any, **_kwargs: Any) -> Path:
        raise ContractError(
            "edaios.receipt/v1 es solo lectura; use evidence_receipt con contexto v2 completo"
        )


__all__ = ["ContractError", "CoreHarness", "HarnessError", "ReceiptError"]
