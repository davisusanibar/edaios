from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from edaios_conformance import (
    ProfileRegistry,
    SchemaRegistry,
    diff_policy,
    explain_failure,
    initialize_attachment,
    prepare_upgrade,
    read_json,
    rollback_attachment,
    validate_attachment,
    validate_federation_mounts,
    write_upgrade_plan,
)

from .core import CoreHarness
from .receipts import create_approval_receipt, create_evidence_receipt, verify_evidence_receipt


CLI_OUTPUT_SCHEMA = "edaios.cli-output/v1"
MEMORY_CLI_OUTPUT_SCHEMA = "edaios.memory-cli-output/v1"
READ_ONLY_BOUNDARY = (
    "consulta local de solo lectura; no confiere autoridad, aceptación ni publicación"
)


class CliUsageError(ValueError):
    """Argumentos inválidos sin imprimir una salida fuera del contrato JSON."""


class ContractArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


def _emit(value: Any, *, stream=None) -> None:
    print(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
        file=stream or sys.stdout,
    )


def _consumption(
    command: str,
    *,
    result: Any | None = None,
    error: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema": CLI_OUTPUT_SCHEMA,
        "command": command,
        "status": "blocked" if error is not None else "ok",
        "claim_boundary": READ_ONLY_BOUNDARY,
    }
    payload["error" if error is not None else "result"] = error if error is not None else result
    return SchemaRegistry().validate("cli-output", payload)


def _memory_output(
    command: str,
    *,
    result: Any | None = None,
    error: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema": MEMORY_CLI_OUTPUT_SCHEMA,
        "command": command,
        "status": "blocked" if error is not None else "ok",
        "claim_boundary": (
            "memoria, índice o setup local; no confiere autoridad, evidencia, "
            "aceptación ni promoción"
        ),
    }
    payload["error" if error is not None else "result"] = error if error is not None else result
    return SchemaRegistry().validate("memory-cli-output", payload)


def _as_dict(item: Any) -> Any:
    """Normaliza registros de cualquier provider a dict serializable.

    LocalWorkingMemory devuelve objetos con ``.to_dict()``; el adapter Engram
    ya devuelve sobres ``dict``.
    """
    to_dict = getattr(item, "to_dict", None)
    return to_dict() if callable(to_dict) else item


def _build_memory_provider(args: argparse.Namespace) -> tuple[Any, str]:
    """Selecciona el provider de working memory según ``--provider``.

    El default es ``local``; ``engram`` es opcional y degradable. Un runtime
    Engram ausente o incompatible produce un error contractual, nunca bloquea
    la memoria local ni el canon.
    """
    provider_name = getattr(args, "provider", "local") or "local"
    if provider_name == "engram":
        from edaios_memory_adapter import EngramHTTPProvider

        kwargs: dict[str, Any] = {}
        endpoint = getattr(args, "endpoint", None)
        if endpoint:
            kwargs["base_url"] = endpoint
        return EngramHTTPProvider(**kwargs), "engram"
    from edaios_core.memory import LocalWorkingMemory

    return (
        LocalWorkingMemory(args.root, force_fallback=getattr(args, "force_fallback", False)),
        "local",
    )


def _consumption_command(args: argparse.Namespace) -> str | None:
    if args.command == "kos":
        return f"kos.{args.kos_command}"
    if args.command == "query":
        return f"query.{args.query_command}"
    return None


def _auxiliary_command(args: argparse.Namespace) -> str | None:
    if args.command == "memory":
        return f"memory.{args.memory_command}"
    if args.command == "agent-setup":
        return f"agent-setup.{args.setup_command}"
    return None


def _consumption_command_from_argv(argv: list[str]) -> str | None:
    if len(argv) >= 2 and argv[0] == "kos" and argv[1] in {"list", "get"}:
        return f"kos.{argv[1]}"
    if len(argv) >= 2 and argv[0] == "query" and argv[1] in {
        "find", "impact", "neighborhood",
    }:
        return f"query.{argv[1]}"
    return None


def _auxiliary_command_from_argv(argv: list[str]) -> str | None:
    if len(argv) >= 2 and argv[0] == "memory" and argv[1] in {
        "doctor", "save", "search", "context", "session-start", "session-event",
        "session-end", "timeline", "conflicts", "index-rebuild", "index-status",
        "index-search",
    }:
        return f"memory.{argv[1]}"
    if len(argv) >= 2 and argv[0] == "agent-setup" and argv[1] in {
        "plan", "apply", "verify", "rollback",
    }:
        return f"agent-setup.{argv[1]}"
    return None


def _error_code(exc: Exception) -> str:
    name = type(exc).__name__
    if name in {"KONotFound", "NodeNotFound"}:
        return "NOT_FOUND"
    if isinstance(exc, OSError):
        return "IO_ERROR"
    return "INVALID_REQUEST"


def _parser() -> argparse.ArgumentParser:
    parser = ContractArgumentParser(
        prog="edaios-core",
        description="Control plane local: valida y prepara; no acepta, mergea o publica.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")

    init = commands.add_parser("init", help="crear attachment T0 draft")
    init.add_argument("--workspace", default=".")
    init.add_argument("--id", required=True)
    init.add_argument("--namespace", required=True)
    init.add_argument("--owner", required=True)
    init.add_argument("--value-owner", required=True)
    init.add_argument("--core-version", default="3.1.0")

    adopt = commands.add_parser("adopt", help="validar attachment sin aceptarlo")
    adopt.add_argument("--workspace", default=".")

    validate = commands.add_parser("validate")
    validate.add_argument("--workspace", default=".")
    validate.add_argument(
        "--profile", choices=["core-release", "initiative-adoption", "federation"],
        default="core-release",
    )
    validate.add_argument("--mounts", help="JSON explicito requerido por federation")

    explain = commands.add_parser("explain")
    explain.add_argument("--code", required=True)

    evidence = commands.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_create = evidence_commands.add_parser("create")
    evidence_create.add_argument("--workspace", default=".")
    evidence_create.add_argument("--initiative", required=True)
    evidence_create.add_argument("--feature-run", required=True)
    evidence_create.add_argument("--actor-id", required=True)
    evidence_create.add_argument("--actor-type", choices=["human", "service", "agent"], required=True)
    evidence_create.add_argument("--core-version", default="3.1.0")
    evidence_create.add_argument("--policy", required=True)
    evidence_create.add_argument("--base-commit", required=True)
    evidence_create.add_argument("--head-commit", required=True)
    evidence_create.add_argument("--file", action="append", required=True)
    evidence_create.add_argument("--sensitivity", choices=["T0", "T1", "T2", "T3"], required=True)
    evidence_create.add_argument("--exit-code", type=int, required=True)
    evidence_create.add_argument("--verdict", choices=["passed", "failed", "blocked"], required=True)
    evidence_create.add_argument("--claim-boundary", required=True)
    evidence_create.add_argument("--rollback-plan", required=True)
    evidence_create.add_argument("--approval-required", action="store_true")
    evidence_create.add_argument("--approval-role", action="append")

    evidence_verify = evidence_commands.add_parser("verify")
    evidence_verify.add_argument("--workspace", default=".")
    evidence_verify.add_argument("--receipt", required=True)
    evidence_verify.add_argument("--expected-head")
    evidence_verify.add_argument("--expected-base")
    evidence_verify.add_argument("--policy")
    evidence_verify.add_argument("--max-age-seconds", type=int)
    evidence_verify.add_argument("--approval-required", action="store_true")
    evidence_verify.add_argument("--approval")
    evidence_verify.add_argument("--approval-role", action="append")
    evidence_verify.add_argument("--authority-registry")

    approval = commands.add_parser("approval")
    approval_commands = approval.add_subparsers(dest="approval_command", required=True)
    approval_create = approval_commands.add_parser("create")
    approval_create.add_argument("--workspace", default=".")
    approval_create.add_argument("--initiative", required=True)
    approval_create.add_argument("--feature-run", required=True)
    approval_create.add_argument("--actor-id", required=True)
    approval_create.add_argument("--authority-role", required=True)
    approval_create.add_argument("--evidence-digest", required=True)
    approval_create.add_argument("--verdict", choices=["accepted", "rejected"], required=True)
    approval_create.add_argument("--statement", required=True)

    policy = commands.add_parser("diff-policy")
    policy.add_argument("--current", required=True)
    policy.add_argument("--proposed", required=True)

    upgrade = commands.add_parser("upgrade")
    upgrade.add_argument("--manifest", required=True)
    upgrade.add_argument("--current-policy", required=True)
    upgrade.add_argument("--target-policy", required=True)
    upgrade.add_argument("--target-core", required=True)
    upgrade.add_argument("--output", required=True)

    rollback = commands.add_parser("rollback")
    rollback.add_argument("--workspace", default=".")
    rollback.add_argument("--apply", action="store_true")

    kos = commands.add_parser("kos", help="consumo read-only de Knowledge Objects")
    kos_commands = kos.add_subparsers(dest="kos_command", required=True)
    kos_list = kos_commands.add_parser("list")
    kos_list.add_argument("--root", default=".")
    kos_list.add_argument(
        "--estado", default="Ratificado",
        help="estado a filtrar; 'todos' desactiva el filtro",
    )
    kos_list.add_argument("--autoridad")
    kos_list.add_argument("--tipo")
    kos_get = kos_commands.add_parser("get")
    kos_get.add_argument("--root", default=".")
    kos_get.add_argument("--id", required=True)
    kos_get.add_argument(
        "--kind", choices=["human", "aicontext", "catalog"], default="aicontext",
    )

    query = commands.add_parser("query", help="consulta read-only del grafo EKG")
    query_commands = query.add_subparsers(dest="query_command", required=True)
    query_find = query_commands.add_parser("find")
    query_find.add_argument("--root", default=".")
    query_find.add_argument("--type")
    query_find.add_argument("--name")
    query_find.add_argument("--namespace")
    query_impact = query_commands.add_parser("impact")
    query_impact.add_argument("--root", default=".")
    query_impact.add_argument("--node", required=True)
    query_impact.add_argument("--via", action="append")
    query_neighborhood = query_commands.add_parser("neighborhood")
    query_neighborhood.add_argument("--root", default=".")
    query_neighborhood.add_argument("--node", required=True)
    query_neighborhood.add_argument("--depth", type=int, default=1)

    memory = commands.add_parser(
        "memory", help="working memory e índice derivados; nunca autoridad"
    )
    memory_commands = memory.add_subparsers(dest="memory_command", required=True)

    def _add_provider_args(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--provider",
            choices=["local", "engram"],
            default="local",
            help="provider de working memory; engram es opcional y loopback",
        )
        subparser.add_argument(
            "--endpoint",
            help="base_url loopback del runtime engram (def http://127.0.0.1:7437)",
        )

    memory_doctor = memory_commands.add_parser("doctor")
    memory_doctor.add_argument("--root", default=".")
    memory_doctor.add_argument("--force-fallback", action="store_true")
    _add_provider_args(memory_doctor)
    memory_save = memory_commands.add_parser("save")
    memory_save.add_argument("--root", default=".")
    memory_save.add_argument("--project", required=True)
    memory_save.add_argument("--subject", required=True)
    memory_save.add_argument("--claim", required=True)
    memory_save.add_argument("--value", required=True)
    memory_save.add_argument("--type", default="discovery")
    memory_save.add_argument("--sensitivity", choices=["T0", "T1", "T2", "T3"], default="T0")
    memory_save.add_argument("--session")
    memory_save.add_argument("--source-ref", default="human-or-agent-observation")
    memory_save.add_argument("--source-digest")
    _add_provider_args(memory_save)
    memory_search = memory_commands.add_parser("search")
    memory_search.add_argument("--root", default=".")
    memory_search.add_argument("--query", required=True)
    memory_search.add_argument("--project")
    memory_search.add_argument("--limit", type=int, default=10)
    memory_search.add_argument("--force-fallback", action="store_true")
    _add_provider_args(memory_search)
    memory_context = memory_commands.add_parser(
        "context", help="bloque de contexto agregado (solo provider engram)"
    )
    memory_context.add_argument("--root", default=".")
    memory_context.add_argument("--project")
    memory_context.add_argument("--scope", choices=["project", "personal", "global"])
    _add_provider_args(memory_context)
    session_start = memory_commands.add_parser("session-start")
    session_start.add_argument("--root", default=".")
    session_start.add_argument("--session", required=True)
    session_start.add_argument("--project", required=True)
    session_start.add_argument("--feature", required=True)
    session_start.add_argument("--actor", required=True)
    session_start.add_argument("--agent", required=True)
    session_start.add_argument("--worktree", required=True)
    session_start.add_argument("--branch", required=True)
    session_start.add_argument("--head", required=True)
    _add_provider_args(session_start)
    session_event = memory_commands.add_parser("session-event")
    session_event.add_argument("--root", default=".")
    session_event.add_argument("--session", required=True)
    session_event.add_argument("--kind", required=True)
    session_event.add_argument("--payload", required=True, help="objeto JSON inline")
    _add_provider_args(session_event)
    session_end = memory_commands.add_parser("session-end")
    session_end.add_argument("--root", default=".")
    session_end.add_argument("--session", required=True)
    session_end.add_argument("--summary", required=True)
    session_end.add_argument("--head", required=True)
    _add_provider_args(session_end)
    timeline = memory_commands.add_parser("timeline")
    timeline.add_argument("--root", default=".")
    timeline.add_argument("--session", required=True)
    _add_provider_args(timeline)
    conflicts = memory_commands.add_parser("conflicts")
    conflicts.add_argument("--root", default=".")
    conflicts.add_argument("--project")
    conflicts.add_argument("--subject")
    _add_provider_args(conflicts)
    index_rebuild = memory_commands.add_parser("index-rebuild")
    index_rebuild.add_argument("--root", default=".")
    index_rebuild.add_argument("--channel", action="append")
    index_rebuild.add_argument("--force-fallback", action="store_true")
    index_status = memory_commands.add_parser("index-status")
    index_status.add_argument("--root", default=".")
    index_search = memory_commands.add_parser("index-search")
    index_search.add_argument("--root", default=".")
    index_search.add_argument("--query", required=True)
    index_search.add_argument("--channel", action="append")
    index_search.add_argument("--limit", type=int, default=10)

    setup = commands.add_parser(
        "agent-setup", help="onboarding project-local con plan/apply/verify/rollback"
    )
    setup_commands = setup.add_subparsers(dest="setup_command", required=True)
    for name in ("plan", "apply", "verify"):
        subcommand = setup_commands.add_parser(name)
        subcommand.add_argument("--root", default=".")
        subcommand.add_argument(
            "--surface", choices=["codex", "claude-code", "copilot"], required=True
        )
    setup_rollback = setup_commands.add_parser("rollback")
    setup_rollback.add_argument("--root", default=".")
    setup_rollback.add_argument("--receipt", required=True)
    return parser


def _validate(profile: str, workspace: str, mounts_path: str | None = None) -> dict[str, Any]:
    profiles = ProfileRegistry()
    resolved = profiles.resolve(profile)
    report: dict[str, Any] = {
        "status": "valid",
        "profile": resolved,
        "core": CoreHarness().validate(),
    }
    if profile in {"initiative-adoption", "federation"}:
        report["attachment"] = validate_attachment(workspace)
    if profile == "federation":
        if not mounts_path:
            raise ValueError("federation exige --mounts explicito")
        mounts = validate_federation_mounts(mounts_path)
        from edaios_sdk_consumption import KnowledgeClient
        from edaios_query import QueryEngine

        ko_rows = KnowledgeClient._from_validated_mounts(mounts).list_kos(estado=None)
        graph_mounts = [
            mount for mount in mounts
            if (Path(str(mount.get("path", ""))) / "knowledge-graph").is_dir()
            or Path(str(mount.get("path", ""))).name == "knowledge-graph"
        ]
        graph_rows = (
            QueryEngine._from_validated_mounts(
                graph_mounts, allow_single=True
            ).find()
            if graph_mounts else []
        )
        if validate_federation_mounts(mounts_path) != mounts:
            raise ValueError("federation mounts cambiaron durante el consumo")
        report["federation"] = {
            "mounts": len(mounts),
            "knowledge_objects": len(ko_rows),
            "graph_nodes": len(graph_rows),
            "derived": True,
        }
        report["claim_boundary"] = "explicit local mounts; no remote operation or authority transfer"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    try:
        args = parser.parse_args(raw_argv)
    except CliUsageError as exc:
        command = _consumption_command_from_argv(raw_argv)
        auxiliary = _auxiliary_command_from_argv(raw_argv)
        if command is not None:
            _emit(
                _consumption(
                    command,
                    error={"code": "INVALID_ARGUMENT", "message": str(exc)},
                ),
                stream=sys.stderr,
            )
        elif auxiliary is not None:
            _emit(
                _memory_output(
                    auxiliary,
                    error={"code": "INVALID_ARGUMENT", "message": str(exc)},
                ),
                stream=sys.stderr,
            )
        else:
            _emit({"status": "blocked", "error": str(exc)}, stream=sys.stderr)
        return 2
    try:
        if args.command == "doctor":
            _emit({"harness": CoreHarness().validate(), "profiles": ProfileRegistry().validate_registry()})
        elif args.command == "init":
            _emit(initialize_attachment(
                args.workspace,
                initiative_id=args.id,
                namespace=args.namespace,
                owner=args.owner,
                value_owner=args.value_owner,
                core_version=args.core_version,
            ))
        elif args.command == "adopt":
            _emit(validate_attachment(args.workspace))
        elif args.command == "validate":
            _emit(_validate(args.profile, args.workspace, args.mounts))
        elif args.command == "explain":
            _emit(explain_failure(args.code))
        elif args.command == "evidence" and args.evidence_command == "create":
            path = create_evidence_receipt(
                args.workspace,
                initiative=args.initiative,
                feature_run=args.feature_run,
                actor_id=args.actor_id,
                actor_type=args.actor_type,
                core_version=args.core_version,
                policy=read_json(args.policy),
                base_commit=args.base_commit,
                head_commit=args.head_commit,
                evidence=args.file,
                sensitivity=args.sensitivity,
                exit_code=args.exit_code,
                verdict=args.verdict,
                claim_boundary=args.claim_boundary,
                rollback=read_json(args.rollback_plan),
                approval_required=args.approval_required,
                approval_roles=args.approval_role,
            )
            _emit({"status": "created", "receipt": str(path)})
        elif args.command == "evidence" and args.evidence_command == "verify":
            _emit(verify_evidence_receipt(
                args.workspace,
                args.receipt,
                expected_head=args.expected_head,
                expected_base=args.expected_base,
                expected_policy=args.policy,
                max_age_seconds=args.max_age_seconds,
                approval_required=args.approval_required,
                approval=args.approval,
                approval_roles=args.approval_role,
                approval_authority=(
                    read_json(args.authority_registry) if args.authority_registry else None
                ),
            ))
        elif args.command == "approval" and args.approval_command == "create":
            path = create_approval_receipt(
                args.workspace,
                initiative=args.initiative,
                feature_run=args.feature_run,
                actor_id=args.actor_id,
                authority_role=args.authority_role,
                evidence_receipt_digest=args.evidence_digest,
                verdict=args.verdict,
                statement=args.statement,
            )
            _emit({"status": "created", "receipt": str(path)})
        elif args.command == "diff-policy":
            report = diff_policy(read_json(args.current), read_json(args.proposed))
            _emit(report)
            return 0 if report["applicable"] else 2
        elif args.command == "upgrade":
            plan = prepare_upgrade(
                read_json(args.manifest),
                read_json(args.current_policy),
                read_json(args.target_policy),
                target_core=args.target_core,
            )
            path = write_upgrade_plan(args.output, plan)
            _emit({"status": "prepared", "plan": str(path), "automatic_apply": False})
        elif args.command == "rollback":
            _emit(rollback_attachment(args.workspace, apply=args.apply))
        elif args.command == "kos" and args.kos_command == "list":
            from dataclasses import asdict

            from edaios_sdk_consumption import KnowledgeClient

            estado = None if args.estado in {"todos", "*"} else args.estado
            refs = KnowledgeClient(args.root).list_kos(
                estado=estado, autoridad=args.autoridad, tipo=args.tipo,
            )
            _emit(_consumption("kos.list", result=[asdict(ref) for ref in refs]))
        elif args.command == "kos" and args.kos_command == "get":
            from edaios_sdk_consumption import KnowledgeClient

            representation = KnowledgeClient(args.root).get_representation(
                args.id, kind=args.kind,
            )
            _emit(_consumption("kos.get", result=representation))
        elif args.command == "query" and args.query_command == "find":
            from edaios_query import QueryEngine

            refs = QueryEngine(args.root).find(
                type=args.type, name=args.name, namespace=args.namespace,
            )
            _emit(_consumption("query.find", result=[ref.to_dict() for ref in refs]))
        elif args.command == "query" and args.query_command == "impact":
            from edaios_query import QueryEngine

            via = tuple(args.via) if args.via else ("depends_on",)
            result = QueryEngine(args.root).impact(args.node, via=via)
            _emit(_consumption("query.impact", result=result.to_dict()))
        elif args.command == "query" and args.query_command == "neighborhood":
            from edaios_query import QueryEngine

            subgraph = QueryEngine(args.root).neighborhood(args.node, depth=args.depth)
            _emit(_consumption("query.neighborhood", result=subgraph.to_dict()))
        elif args.command == "memory":
            if args.memory_command.startswith("index-"):
                from edaios_sdk_consumption import DerivedKnowledgeIndex, KnowledgeClient

                index = DerivedKnowledgeIndex(
                    KnowledgeClient(args.root),
                    index_root=args.root,
                    force_fallback=getattr(args, "force_fallback", False),
                )
                if args.memory_command == "index-rebuild":
                    result = index.rebuild(include_channels=args.channel)
                elif args.memory_command == "index-status":
                    result = index.status()
                else:
                    result = [
                        item.to_dict()
                        for item in index.search(
                            args.query, include_channels=args.channel, limit=args.limit
                        )
                    ]
            else:
                if args.memory_command == "save" and args.sensitivity in {"T2", "T3"}:
                    raise ValueError(
                        "working memory solo admite T0/T1; T2/T3 requieren un proveedor seguro gobernado"
                    )
                memory, provider_name = _build_memory_provider(args)
                if args.memory_command == "doctor":
                    result = {"health": memory.health(), "capabilities": memory.capabilities()}
                elif args.memory_command == "save":
                    if provider_name == "engram" and not args.session:
                        raise ValueError("el provider engram exige --session para save")
                    result = _as_dict(
                        memory.save_observation(
                            project=args.project,
                            subject=args.subject,
                            claim=args.claim,
                            value=args.value,
                            record_type=args.type,
                            sensitivity=args.sensitivity,
                            session_id=args.session,
                            source_ref=args.source_ref,
                            source_digest=args.source_digest,
                        )
                    )
                elif args.memory_command == "search":
                    result = []
                    for item in memory.search(args.query, project=args.project, limit=args.limit):
                        row = _as_dict(item)
                        if row.get("sensitivity") in {"T2", "T3"}:
                            row["value"] = "[REDACTED]"
                        result.append(row)
                elif args.memory_command == "context":
                    if provider_name != "engram":
                        raise ValueError(
                            "memory context requiere --provider engram; "
                            "la memoria local no expone contexto agregado"
                        )
                    result = memory.get_context(project=args.project, scope=args.scope)
                elif args.memory_command == "session-start":
                    result = memory.start_session(
                        session_id=args.session,
                        project=args.project,
                        feature=args.feature,
                        actor_id=args.actor,
                        agent=args.agent,
                        worktree=args.worktree,
                        branch=args.branch,
                        head_start=args.head,
                    )
                elif args.memory_command == "session-event":
                    if provider_name == "engram":
                        raise ValueError(
                            "el provider engram no soporta session-event; "
                            "la cadena de eventos es exclusiva de la memoria local"
                        )
                    payload = json.loads(args.payload)
                    if not isinstance(payload, dict):
                        raise ValueError("--payload debe ser un objeto JSON")
                    result = memory.append_session_event(
                        args.session, kind=args.kind, payload=payload
                    ).to_dict()
                elif args.memory_command == "session-end":
                    result = memory.end_session(
                        args.session, summary=args.summary, head_end=args.head
                    )
                elif args.memory_command == "timeline":
                    result = {
                        "events": [_as_dict(item) for item in memory.timeline(args.session)],
                    }
                    if provider_name == "local":
                        result["verification"] = memory.verify_session(args.session)
                else:
                    if provider_name == "engram" and args.subject:
                        raise ValueError(
                            "el provider engram no filtra candidatos por --subject"
                        )
                    if provider_name == "engram":
                        candidates = memory.conflict_candidates(project=args.project)
                    else:
                        candidates = memory.conflict_candidates(
                            project=args.project, subject=args.subject
                        )
                    result = [_as_dict(item) for item in candidates]
            _emit(_memory_output(f"memory.{args.memory_command}", result=result))
        elif args.command == "agent-setup":
            from .agent_setup import apply_setup, plan_setup, rollback_setup, verify_setup

            if args.setup_command == "plan":
                raw = plan_setup(args.root, surface=args.surface)
                result = {key: value for key, value in raw.items() if not key.startswith("_")}
            elif args.setup_command == "apply":
                result = apply_setup(args.root, surface=args.surface)
            elif args.setup_command == "verify":
                result = verify_setup(args.root, surface=args.surface)
            else:
                result = rollback_setup(args.root, receipt=args.receipt)
            _emit(_memory_output(f"agent-setup.{args.setup_command}", result=result))
        return 0
    except Exception as exc:  # noqa: BLE001 — traduce solo errores contractuales esperados
        from edaios_query import NodeNotFound
        from edaios_sdk_consumption import SDKError

        if not isinstance(exc, (OSError, ValueError, SDKError, NodeNotFound)):
            raise
        command = _consumption_command(args)
        auxiliary = _auxiliary_command(args)
        if command is not None:
            message = str(exc).strip() or type(exc).__name__
            _emit(
                _consumption(
                    command,
                    error={"code": _error_code(exc), "message": message},
                ),
                stream=sys.stderr,
            )
        elif auxiliary is not None:
            message = str(exc).strip() or type(exc).__name__
            _emit(
                _memory_output(
                    auxiliary,
                    error={"code": _error_code(exc), "message": message},
                ),
                stream=sys.stderr,
            )
        else:
            _emit(
                {"status": "blocked", "error": str(exc)},
                stream=sys.stderr,
            )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
