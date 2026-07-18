"""Memoria operativa local: reconstruible, no autoritativa y sin promoción.

La autoridad de EDAIOS permanece en Git y los Knowledge Objects. Este módulo
solo conserva contexto de trabajo bajo ``.edaios/`` y nunca escribe al canon.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .io import resolve_contained_path, workspace_lock


MEMORY_SCHEMA = "edaios.memory-record/v1"
SESSION_EVENT_SCHEMA = "edaios.memory-session-event/v1"
CONFLICT_SCHEMA = "edaios.memory-conflict-candidate/v1"
SENSITIVITY_LEVELS = frozenset({"T0", "T1", "T2", "T3"})
SUGGESTED_RELATIONS = frozenset(
    {"related", "compatible", "scoped", "conflicts_with", "supersedes", "not_conflict"}
)
CLAIM_BOUNDARY = (
    "memoria operativa local; no es autoridad, evidencia, aprobación ni promoción"
)


class MemoryContractError(ValueError):
    """Un input no satisface el contrato de memoria local."""


class MemoryIntegrityError(MemoryContractError):
    """Persistencia o cadena de sesión inconsistente."""


class PendingConflictError(MemoryContractError):
    """Una promoción fue intentada con conflictos todavía pendientes."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + sha256(_canonical(value)).hexdigest()


def _timestamp(value: str | None = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise MemoryContractError("timestamp inválido") from exc
    if parsed.tzinfo is None:
        raise MemoryContractError("timestamp exige timezone")
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise MemoryContractError(f"{field} debe ser texto")
    normalized = value.strip()
    if not normalized:
        raise MemoryContractError(f"{field} no puede estar vacío")
    if "\x00" in normalized:
        raise MemoryContractError(f"{field} contiene NUL")
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise MemoryContractError(f"{field} no es UTF-8 válido") from exc
    return normalized


def _source_digest(value: str | None, *, fallback: Any) -> str:
    if value is None:
        return _digest(fallback)
    normalized = value.removeprefix("sha256:").lower()
    if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
        raise MemoryContractError("source_digest debe ser SHA-256")
    return "sha256:" + normalized


def _local_path(root: str | Path, path: str | Path) -> tuple[Path, Path]:
    try:
        return resolve_contained_path(root, path, required_prefix=".edaios")
    except (OSError, ValueError) as exc:
        raise MemoryContractError(str(exc)) from exc

    # Legacy inline checks retained below for source compatibility; the shared
    # resolver above is the authoritative path boundary.
    raw_root = Path(root).expanduser()
    if raw_root.is_symlink():
        raise MemoryContractError("workspace root no puede ser symlink")
    try:
        resolved_root = raw_root.resolve(strict=True)
    except OSError as exc:
        raise MemoryContractError("workspace root no resoluble") from exc
    if not resolved_root.is_dir():
        raise MemoryContractError("workspace root no es directorio")

    raw_path = Path(path).expanduser()
    candidate = raw_path if raw_path.is_absolute() else resolved_root / raw_path
    if ".." in candidate.parts:
        raise MemoryContractError("path traversal no admitido")
    try:
        resolved_candidate = candidate.resolve(strict=False)
        relative = resolved_candidate.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise MemoryContractError("memoria debe permanecer dentro del workspace") from exc
    if not relative.parts or relative.parts[0] != ".edaios":
        raise MemoryContractError("memoria solo puede vivir bajo .edaios/")

    cursor = resolved_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise MemoryContractError(f"symlink no admitido en memoria local: {cursor}")
    return resolved_root, resolved_candidate


@dataclass(frozen=True)
class MemoryRecord:
    record_id: str
    project: str
    subject: str
    claim: str
    value: str
    record_type: str
    sensitivity: str
    session_id: str | None
    source_ref: str
    source_digest: str
    content_digest: str
    created_at: str
    provider: str = "edaios-local"
    provider_version: str = "1"
    channel: str = "local-working"
    authoritative: bool = False
    rebuildable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"schema": MEMORY_SCHEMA, **asdict(self), "claim_boundary": CLAIM_BOUNDARY}


@dataclass(frozen=True)
class ConflictCandidate:
    candidate_id: str
    project: str
    subject: str
    claim: str
    source_record_id: str
    target_record_id: str
    status: str
    created_at: str
    suggested_relation: str | None = None
    suggestion_source: str | None = None
    authoritative: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"schema": CONFLICT_SCHEMA, **asdict(self), "claim_boundary": CLAIM_BOUNDARY}


@dataclass(frozen=True)
class SessionEvent:
    session_id: str
    sequence: int
    kind: str
    payload: dict[str, Any]
    previous_digest: str | None
    event_digest: str
    created_at: str
    authoritative: bool = False
    evidence_status: str = "observation-only"

    def to_dict(self) -> dict[str, Any]:
        return {"schema": SESSION_EVENT_SCHEMA, **asdict(self), "claim_boundary": CLAIM_BOUNDARY}


@runtime_checkable
class MemoryProvider(Protocol):
    """Puerto deliberadamente sin operaciones de decisión o promoción."""

    def capabilities(self) -> dict[str, Any]: ...
    def health(self) -> dict[str, Any]: ...
    def save_observation(self, **values: Any) -> MemoryRecord | dict[str, Any]: ...
    def search(self, query: str, **filters: Any) -> list[Any]: ...
    def start_session(self, **values: Any) -> dict[str, Any]: ...
    def end_session(self, session_id: str, **values: Any) -> dict[str, Any]: ...
    def timeline(self, session_id: str) -> list[Any]: ...
    def conflict_candidates(self, **filters: Any) -> list[Any]: ...


class LocalWorkingMemory:
    """Provider SQLite local, borrable y separado del conocimiento canónico."""

    def __init__(
        self,
        root: str | Path,
        *,
        database: str | Path = ".edaios/memory/working.sqlite3",
        force_fallback: bool = False,
        requested_sensitivity: str | None = None,
    ) -> None:
        if requested_sensitivity not in {None, "T0", "T1"}:
            raise MemoryContractError(
                "memoria local solo admite T0/T1; T2/T3 requieren un proveedor seguro gobernado"
            )
        self.root, self.database = _local_path(root, database)
        self.force_fallback = bool(force_fallback)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.database.parent.chmod(0o700)
        with workspace_lock(self.root, "local-working-memory-schema"):
            with closing(self._connect()) as connection:
                self._initialize(connection)
        self.database.chmod(0o600)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _initialize(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observations (
              record_id TEXT PRIMARY KEY,
              project TEXT NOT NULL,
              subject TEXT NOT NULL,
              claim TEXT NOT NULL,
              value TEXT NOT NULL,
              record_type TEXT NOT NULL,
              sensitivity TEXT NOT NULL,
              session_id TEXT,
              source_ref TEXT NOT NULL,
              source_digest TEXT NOT NULL,
              content_digest TEXT NOT NULL,
              created_at TEXT NOT NULL,
              provider_version TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS observations_subject_claim
              ON observations(project, subject, claim);
            CREATE TABLE IF NOT EXISTS conflicts (
              candidate_id TEXT PRIMARY KEY,
              project TEXT NOT NULL,
              subject TEXT NOT NULL,
              claim TEXT NOT NULL,
              source_record_id TEXT NOT NULL REFERENCES observations(record_id),
              target_record_id TEXT NOT NULL REFERENCES observations(record_id),
              status TEXT NOT NULL CHECK(status = 'review-required'),
              created_at TEXT NOT NULL,
              UNIQUE(source_record_id, target_record_id)
            );
            CREATE TABLE IF NOT EXISTS conflict_suggestions (
              suggestion_id TEXT PRIMARY KEY,
              candidate_id TEXT NOT NULL REFERENCES conflicts(candidate_id),
              relation TEXT NOT NULL,
              source TEXT NOT NULL,
              reasoning TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
              session_id TEXT PRIMARY KEY,
              project TEXT NOT NULL,
              feature TEXT NOT NULL,
              actor_id TEXT NOT NULL,
              agent TEXT NOT NULL,
              worktree TEXT NOT NULL,
              branch TEXT NOT NULL,
              head_start TEXT NOT NULL,
              started_at TEXT NOT NULL,
              ended_at TEXT,
              summary TEXT,
              event_count INTEGER NOT NULL DEFAULT 0,
              head_digest TEXT
            );
            CREATE TABLE IF NOT EXISTS session_events (
              session_id TEXT NOT NULL REFERENCES sessions(session_id),
              sequence INTEGER NOT NULL,
              kind TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              previous_digest TEXT,
              event_digest TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY(session_id, sequence)
            );
            """
        )
        session_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(sessions)")
        }
        if "event_count" not in session_columns:
            connection.execute(
                "ALTER TABLE sessions ADD COLUMN event_count INTEGER NOT NULL DEFAULT 0"
            )
        if "head_digest" not in session_columns:
            connection.execute("ALTER TABLE sessions ADD COLUMN head_digest TEXT")
        mode = "fallback-like"
        if not self.force_fallback:
            try:
                connection.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING "
                    "fts5(record_id UNINDEXED, subject, claim, value, project UNINDEXED)"
                )
                connection.execute("DELETE FROM observations_fts")
                connection.execute(
                    "INSERT INTO observations_fts(record_id,subject,claim,value,project) "
                    "SELECT record_id,subject,claim,value,project FROM observations"
                )
                mode = "fts5"
            except sqlite3.OperationalError:
                mode = "fallback-like"
        connection.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES('search_mode', ?)",
            (mode,),
        )
        connection.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES('schema', ?)",
            ("edaios.local-working-memory/v1",),
        )
        connection.commit()

    @staticmethod
    def _record(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(**dict(row), provider="edaios-local")

    @staticmethod
    def _conflict(row: sqlite3.Row, suggestion: sqlite3.Row | None = None) -> ConflictCandidate:
        return ConflictCandidate(
            candidate_id=row["candidate_id"],
            project=row["project"],
            subject=row["subject"],
            claim=row["claim"],
            source_record_id=row["source_record_id"],
            target_record_id=row["target_record_id"],
            status=row["status"],
            created_at=row["created_at"],
            suggested_relation=suggestion["relation"] if suggestion else None,
            suggestion_source=suggestion["source"] if suggestion else None,
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "schema": "edaios.memory-provider-capabilities/v1",
            "provider": "edaios-local",
            "channel": "local-working",
            "operations": [
                "health", "save-observation", "search", "session-start",
                "session-event", "session-end", "timeline", "conflict-candidates",
            ],
            "forbidden_operations": [
                "approve", "decide", "promote", "write-canonical", "remote-sync",
            ],
            "authoritative": False,
            "rebuildable": True,
        }

    def health(self) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            mode = connection.execute(
                "SELECT value FROM metadata WHERE key='search_mode'"
            ).fetchone()[0]
            observations = connection.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            sessions = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            pending = connection.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0]
        return {
            "status": "ok",
            "provider": "edaios-local",
            "search_mode": mode,
            "observations": observations,
            "sessions": sessions,
            "pending_conflicts": pending,
            "authoritative": False,
            "rebuildable": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def save_observation(
        self,
        *,
        project: str,
        subject: str,
        claim: str,
        value: str,
        record_type: str = "discovery",
        sensitivity: str = "T0",
        session_id: str | None = None,
        source_ref: str = "human-or-agent-observation",
        source_digest: str | None = None,
        created_at: str | None = None,
    ) -> MemoryRecord:
        project = _required_text(project, "project")
        subject = _required_text(subject, "subject")
        claim = _required_text(claim, "claim")
        value = _required_text(value, "value")
        record_type = _required_text(record_type, "record_type")
        source_ref = _required_text(source_ref, "source_ref")
        if sensitivity not in {"T0", "T1"}:
            if sensitivity in {"T2", "T3"}:
                raise MemoryContractError(
                    "memoria local solo admite T0/T1; T2/T3 requieren un proveedor seguro gobernado"
                )
            raise MemoryContractError("sensitivity fuera de T0..T3")
        if session_id is not None:
            session_id = _required_text(session_id, "session_id")
        recorded_at = _timestamp(created_at)
        normalized_source_digest = _source_digest(
            source_digest, fallback={"source_ref": source_ref, "value": value}
        )
        identity = {
            "project": project,
            "subject": subject,
            "claim": claim,
            "value": value,
            "record_type": record_type,
            "sensitivity": sensitivity,
            "source_ref": source_ref,
            "source_digest": normalized_source_digest,
        }
        content_digest = _digest(identity)
        record_id = "MEM-" + content_digest.removeprefix("sha256:")[:24].upper()

        with workspace_lock(self.root, "local-working-memory"):
            with closing(self._connect()) as connection:
                if session_id is not None and connection.execute(
                    "SELECT 1 FROM sessions WHERE session_id=?", (session_id,)
                ).fetchone() is None:
                    raise MemoryContractError("session_id no existe")
                cursor = connection.execute(
                    """INSERT OR IGNORE INTO observations(
                    record_id, project, subject, claim, value, record_type,
                    sensitivity, session_id, source_ref, source_digest,
                    content_digest, created_at, provider_version
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        record_id, project, subject, claim, value, record_type,
                        sensitivity, session_id, source_ref, normalized_source_digest,
                        content_digest, recorded_at, "1",
                    ),
                )
                inserted = cursor.rowcount == 1
                mode = connection.execute(
                    "SELECT value FROM metadata WHERE key='search_mode'"
                ).fetchone()[0]
                if inserted and mode == "fts5":
                    connection.execute(
                        "INSERT INTO observations_fts(record_id,subject,claim,value,project) "
                        "VALUES(?,?,?,?,?)",
                        (record_id, subject, claim, value, project),
                    )

                others = connection.execute(
                    """SELECT record_id, content_digest, value FROM observations
                    WHERE project=? AND subject=? AND claim=? AND record_id<>?""",
                    (project, subject, claim, record_id),
                ).fetchall()
                for other in others:
                    if other["content_digest"] == content_digest or other["value"] == value:
                        continue
                    first, second = sorted((other["record_id"], record_id))
                    candidate_payload = {
                        "project": project,
                        "subject": subject,
                        "claim": claim,
                        "source_record_id": first,
                        "target_record_id": second,
                    }
                    candidate_id = (
                        "CONFLICT-" + _digest(candidate_payload).removeprefix("sha256:")[:24].upper()
                    )
                    connection.execute(
                        """INSERT OR IGNORE INTO conflicts(
                        candidate_id,project,subject,claim,source_record_id,
                        target_record_id,status,created_at
                        ) VALUES(?,?,?,?,?,?,?,?)""",
                        (
                            candidate_id, project, subject, claim, first, second,
                            "review-required", recorded_at,
                        ),
                    )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM observations WHERE record_id=?", (record_id,)
                ).fetchone()
                assert row is not None
                return self._record(row)

    def search(
        self, query: str, *, project: str | None = None, limit: int = 10
    ) -> list[MemoryRecord]:
        query = _required_text(query, "query")
        if project is not None:
            project = _required_text(project, "project")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise MemoryContractError("limit debe estar entre 1 y 100")
        with closing(self._connect()) as connection:
            mode = connection.execute(
                "SELECT value FROM metadata WHERE key='search_mode'"
            ).fetchone()[0]
            if mode == "fts5":
                tokens = re.findall(r"[\w-]+", query, flags=re.UNICODE)
                if not tokens:
                    return []
                expression = " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)
                sql = (
                    "SELECT o.* FROM observations_fts f JOIN observations o "
                    "ON o.record_id=f.record_id WHERE observations_fts MATCH ?"
                )
                values: list[Any] = [expression]
                if project is not None:
                    sql += " AND o.project=?"
                    values.append(project)
                sql += " ORDER BY bm25(observations_fts), o.created_at DESC LIMIT ?"
                values.append(limit)
                rows = connection.execute(sql, values).fetchall()
            else:
                sql = (
                    "SELECT * FROM observations WHERE "
                    "(lower(subject) LIKE ? OR lower(claim) LIKE ? OR lower(value) LIKE ?)"
                )
                pattern = "%" + query.lower() + "%"
                values = [pattern, pattern, pattern]
                if project is not None:
                    sql += " AND project=?"
                    values.append(project)
                sql += " ORDER BY created_at DESC LIMIT ?"
                values.append(limit)
                rows = connection.execute(sql, values).fetchall()
        return [self._record(row) for row in rows]

    def conflict_candidates(
        self, *, project: str | None = None, subject: str | None = None
    ) -> list[ConflictCandidate]:
        sql = "SELECT * FROM conflicts WHERE status='review-required'"
        values: list[str] = []
        if project is not None:
            sql += " AND project=?"
            values.append(_required_text(project, "project"))
        if subject is not None:
            sql += " AND subject=?"
            values.append(_required_text(subject, "subject"))
        sql += " ORDER BY created_at, candidate_id"
        with closing(self._connect()) as connection:
            rows = connection.execute(sql, values).fetchall()
            result: list[ConflictCandidate] = []
            for row in rows:
                suggestion = connection.execute(
                    "SELECT relation,source FROM conflict_suggestions "
                    "WHERE candidate_id=? ORDER BY created_at DESC, suggestion_id DESC LIMIT 1",
                    (row["candidate_id"],),
                ).fetchone()
                result.append(self._conflict(row, suggestion))
            return result

    def suggest_conflict(
        self,
        candidate_id: str,
        *,
        relation: str,
        source: str,
        reasoning: str,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        candidate_id = _required_text(candidate_id, "candidate_id")
        relation = _required_text(relation, "relation")
        if relation not in SUGGESTED_RELATIONS:
            raise MemoryContractError("relation fuera del vocabulario permitido")
        source = _required_text(source, "source")
        reasoning = _required_text(reasoning, "reasoning")
        recorded_at = _timestamp(created_at)
        payload = {
            "candidate_id": candidate_id,
            "relation": relation,
            "source": source,
            "reasoning": reasoning,
        }
        suggestion_id = "SUG-" + _digest(payload).removeprefix("sha256:")[:24].upper()
        with workspace_lock(self.root, "local-working-memory"):
            with closing(self._connect()) as connection:
                if connection.execute(
                    "SELECT 1 FROM conflicts WHERE candidate_id=?", (candidate_id,)
                ).fetchone() is None:
                    raise MemoryContractError("candidate_id no existe")
                connection.execute(
                    "INSERT OR IGNORE INTO conflict_suggestions VALUES(?,?,?,?,?,?)",
                    (suggestion_id, candidate_id, relation, source, reasoning, recorded_at),
                )
                connection.commit()
        return {
            "suggestion_id": suggestion_id,
            **payload,
            "authoritative": False,
            "effect": "advisory-only; candidate remains review-required",
        }

    def assert_promotable(self, *, project: str, subject: str | None = None) -> None:
        candidates = self.conflict_candidates(project=project, subject=subject)
        if candidates:
            raise PendingConflictError(
                f"promoción bloqueada: {len(candidates)} conflicto(s) review-required"
            )

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        session_id: str,
        kind: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> SessionEvent:
        last = connection.execute(
            "SELECT sequence,event_digest FROM session_events "
            "WHERE session_id=? ORDER BY sequence DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        sequence = (last["sequence"] + 1) if last else 1
        previous = last["event_digest"] if last else None
        envelope = {
            "session_id": session_id,
            "sequence": sequence,
            "kind": kind,
            "payload": payload,
            "previous_digest": previous,
            "created_at": created_at,
        }
        event_digest = _digest(envelope)
        connection.execute(
            "INSERT INTO session_events VALUES(?,?,?,?,?,?,?)",
            (
                session_id, sequence, kind,
                _canonical(payload).decode("ascii"), previous, event_digest, created_at,
            ),
        )
        connection.execute(
            "UPDATE sessions SET event_count=?, head_digest=? WHERE session_id=?",
            (sequence, event_digest, session_id),
        )
        return SessionEvent(
            session_id=session_id,
            sequence=sequence,
            kind=kind,
            payload=payload,
            previous_digest=previous,
            event_digest=event_digest,
            created_at=created_at,
        )

    def start_session(
        self,
        *,
        session_id: str,
        project: str,
        feature: str,
        actor_id: str,
        agent: str,
        worktree: str,
        branch: str,
        head_start: str,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        values = {
            name: _required_text(value, name)
            for name, value in {
                "session_id": session_id, "project": project, "feature": feature,
                "actor_id": actor_id, "agent": agent, "worktree": worktree,
                "branch": branch, "head_start": head_start,
            }.items()
        }
        recorded_at = _timestamp(created_at)
        with workspace_lock(self.root, "local-working-memory"):
            with closing(self._connect()) as connection:
                try:
                    connection.execute(
                        """INSERT INTO sessions(
                        session_id,project,feature,actor_id,agent,worktree,branch,
                        head_start,started_at,ended_at,summary,event_count,head_digest
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            values["session_id"], values["project"], values["feature"],
                            values["actor_id"], values["agent"], values["worktree"],
                            values["branch"], values["head_start"], recorded_at, None, None,
                            0, None,
                        ),
                    )
                except sqlite3.IntegrityError as exc:
                    raise MemoryContractError("session_id ya existe") from exc
                event = self._append_event(
                    connection, values["session_id"], "start",
                    {key: value for key, value in values.items() if key != "session_id"},
                    recorded_at,
                )
                connection.commit()
        return {
            "session_id": values["session_id"],
            "status": "open",
            "event": event.to_dict(),
            "authoritative": False,
            "evidence_status": "observation-only",
        }

    def append_session_event(
        self,
        session_id: str,
        *,
        kind: str,
        payload: dict[str, Any],
        created_at: str | None = None,
    ) -> SessionEvent:
        session_id = _required_text(session_id, "session_id")
        kind = _required_text(kind, "kind")
        if kind in {"start", "summary", "end"}:
            raise MemoryContractError("kind reservado al lifecycle de sesión")
        if not isinstance(payload, dict):
            raise MemoryContractError("payload debe ser objeto")
        recorded_at = _timestamp(created_at)
        with workspace_lock(self.root, "local-working-memory"):
            with closing(self._connect()) as connection:
                session = connection.execute(
                    "SELECT ended_at FROM sessions WHERE session_id=?", (session_id,)
                ).fetchone()
                if session is None:
                    raise MemoryContractError("session_id no existe")
                if session["ended_at"] is not None:
                    raise MemoryContractError("sesión ya cerrada")
                event = self._append_event(connection, session_id, kind, payload, recorded_at)
                connection.commit()
                return event

    def end_session(
        self,
        session_id: str,
        *,
        summary: str,
        head_end: str,
        receipt_refs: list[dict[str, str]] | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        session_id = _required_text(session_id, "session_id")
        summary = _required_text(summary, "summary")
        head_end = _required_text(head_end, "head_end")
        receipts = receipt_refs or []
        if not isinstance(receipts, list) or any(not isinstance(item, dict) for item in receipts):
            raise MemoryContractError("receipt_refs debe ser lista de objetos")
        normalized_receipts: list[dict[str, str]] = []
        for item in receipts:
            receipt_id = _required_text(str(item.get("receipt_id", "")), "receipt_id")
            receipt_digest = _source_digest(str(item.get("digest", "")), fallback={})
            normalized_receipts.append(
                {"receipt_id": receipt_id, "digest": receipt_digest, "status": "linked-not-verified"}
            )
        recorded_at = _timestamp(created_at)
        with workspace_lock(self.root, "local-working-memory"):
            with closing(self._connect()) as connection:
                session = connection.execute(
                    "SELECT ended_at FROM sessions WHERE session_id=?", (session_id,)
                ).fetchone()
                if session is None:
                    raise MemoryContractError("session_id no existe")
                if session["ended_at"] is not None:
                    raise MemoryContractError("sesión ya cerrada")
                summary_event = self._append_event(
                    connection,
                    session_id,
                    "summary",
                    {
                        "summary": summary,
                        "receipt_refs": normalized_receipts,
                        "verification": "unverified",
                    },
                    recorded_at,
                )
                end_event = self._append_event(
                    connection,
                    session_id,
                    "end",
                    {"head_end": head_end, "verification": "observation-only"},
                    recorded_at,
                )
                connection.execute(
                    "UPDATE sessions SET ended_at=?, summary=? WHERE session_id=?",
                    (recorded_at, summary, session_id),
                )
                connection.commit()
        return {
            "session_id": session_id,
            "status": "closed",
            "summary_event": summary_event.to_dict(),
            "end_event": end_event.to_dict(),
            "authoritative": False,
            "evidence_status": "observation-only",
        }

    def timeline(self, session_id: str) -> list[SessionEvent]:
        session_id = _required_text(session_id, "session_id")
        with closing(self._connect()) as connection:
            if connection.execute(
                "SELECT 1 FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone() is None:
                raise MemoryContractError("session_id no existe")
            rows = connection.execute(
                "SELECT * FROM session_events WHERE session_id=? ORDER BY sequence",
                (session_id,),
            ).fetchall()
        return [
            SessionEvent(
                session_id=row["session_id"],
                sequence=row["sequence"],
                kind=row["kind"],
                payload=json.loads(row["payload_json"]),
                previous_digest=row["previous_digest"],
                event_digest=row["event_digest"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def verify_session(self, session_id: str) -> dict[str, Any]:
        events = self.timeline(session_id)
        with closing(self._connect()) as connection:
            session = connection.execute(
                "SELECT ended_at,event_count,head_digest FROM sessions WHERE session_id=?",
                (_required_text(session_id, "session_id"),),
            ).fetchone()
        assert session is not None
        previous: str | None = None
        issues: list[str] = []
        for expected_sequence, event in enumerate(events, start=1):
            envelope = {
                "session_id": event.session_id,
                "sequence": event.sequence,
                "kind": event.kind,
                "payload": event.payload,
                "previous_digest": event.previous_digest,
                "created_at": event.created_at,
            }
            if event.sequence != expected_sequence:
                issues.append(f"sequence {event.sequence} no es {expected_sequence}")
            if event.previous_digest != previous:
                issues.append(f"sequence {event.sequence}: previous_digest inválido")
            if event.event_digest != _digest(envelope):
                issues.append(f"sequence {event.sequence}: event_digest inválido")
            previous = event.event_digest
        if session["event_count"] != len(events):
            issues.append(
                f"event_count terminal {session['event_count']} no coincide con {len(events)}"
            )
        if session["head_digest"] != previous:
            issues.append("head_digest terminal no coincide con la cadena observada")
        kinds = [event.kind for event in events]
        if not kinds or kinds[0] != "start" or kinds.count("start") != 1:
            issues.append("lifecycle exige exactamente un evento start inicial")
        if session["ended_at"] is None:
            if any(kind in {"summary", "end"} for kind in kinds):
                issues.append("sesión abierta no puede contener summary/end")
        elif (
            len(kinds) < 3
            or kinds[-2:] != ["summary", "end"]
            or kinds.count("summary") != 1
            or kinds.count("end") != 1
        ):
            issues.append("sesión cerrada exige lifecycle start/.../summary/end")
        return {
            "session_id": session_id,
            "status": "valid" if not issues else "invalid",
            "events": len(events),
            "head_digest": previous,
            "issues": issues,
            "authoritative": False,
            "evidence_status": "observation-only",
        }


__all__ = [
    "CLAIM_BOUNDARY", "ConflictCandidate", "LocalWorkingMemory", "MemoryContractError",
    "MemoryIntegrityError", "MemoryProvider", "MemoryRecord", "PendingConflictError",
    "SessionEvent",
]
