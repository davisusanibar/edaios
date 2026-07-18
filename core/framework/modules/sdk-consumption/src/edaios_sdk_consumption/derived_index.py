"""Índice reemplazable de Knowledge Objects; Git sigue siendo la autoridad."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
from contextlib import closing
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable

from edaios_core.io import workspace_lock
from edaios_core.knowledge import CHANNEL_BY_STATE


INDEX_SCHEMA = "edaios.derived-knowledge-index/v1"
INDEX_RESULT_SCHEMA = "edaios.indexed-knowledge-result/v1"
CANONICAL_CHANNELS = ("normative",)
KNOWN_CHANNELS = frozenset(CHANNEL_BY_STATE.values())
CLAIM_BOUNDARY = (
    "índice derivado y regenerable; cada resultado conserva la autoridad de su fuente Git"
)


class IndexContractError(ValueError):
    """Configuración o consulta fuera del contrato del índice."""


class IndexStaleError(IndexContractError):
    """El corpus cambió después del último rebuild."""


class IndexIntegrityError(IndexContractError):
    """La proyección SQLite no coincide con el snapshot que declara."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + sha256(_canonical(value)).hexdigest()


def _channels(values: Iterable[str] | None) -> tuple[str, ...]:
    selected = tuple(sorted(set(values or CANONICAL_CHANNELS)))
    if not selected or any(value not in KNOWN_CHANNELS for value in selected):
        raise IndexContractError("channels contiene un canal desconocido o está vacío")
    return selected


def _safe_index_path(root: str | Path, value: str | Path) -> tuple[Path, Path]:
    raw_root = Path(root).expanduser()
    if raw_root.is_symlink():
        raise IndexContractError("index root no puede ser symlink")
    try:
        root_path = raw_root.resolve(strict=True)
    except OSError as exc:
        raise IndexContractError("index root no resoluble") from exc
    candidate = Path(value).expanduser()
    candidate = candidate if candidate.is_absolute() else root_path / candidate
    if ".." in candidate.parts:
        raise IndexContractError("path traversal no admitido")
    try:
        resolved = candidate.resolve(strict=False)
        relative = resolved.relative_to(root_path)
    except (OSError, ValueError) as exc:
        raise IndexContractError("index debe permanecer dentro del root") from exc
    if not relative.parts or relative.parts[0] != ".edaios":
        raise IndexContractError("index solo puede vivir bajo .edaios/")
    cursor = root_path
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise IndexContractError(f"symlink no admitido en index: {cursor}")
    return root_path, resolved


@dataclass(frozen=True)
class IndexedKnowledgeResult:
    ko_id: str
    title: str
    authority: str
    state: str
    channel: str
    source: str
    source_digest: str
    namespace: str | None
    score: float | None
    authoritative: bool = False
    source_authoritative: bool = True
    representation: str = "derived-index-hit"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": INDEX_RESULT_SCHEMA,
            **asdict(self),
            "claim_boundary": CLAIM_BOUNDARY,
        }


class DerivedKnowledgeIndex:
    """Snapshot FTS5/fallback ligado a la huella del corpus consumido."""

    def __init__(
        self,
        client: Any,
        *,
        index_root: str | Path | None = None,
        database: str | Path = ".edaios/index/knowledge.sqlite3",
        force_fallback: bool = False,
    ) -> None:
        if not hasattr(client, "list_kos") or not hasattr(client, "get_ko"):
            raise IndexContractError("client no cumple KnowledgeClient")
        if index_root is None:
            index_root = getattr(client, "root", None)
        if index_root is None:
            raise IndexContractError("una vista federada exige index_root explícito")
        self.client = client
        self.root, self.database = _safe_index_path(index_root, database)
        self.force_fallback = bool(force_fallback)

    def _mounts_digest(self) -> str:
        mounts = getattr(self.client, "mounts", None)
        if mounts is None:
            return _digest({"mode": "local", "root": str(getattr(self.client, "root", ""))})
        return _digest(
            [
                {
                    "namespace": mount.namespace,
                    "path": str(mount.path),
                    "authority_layer": mount.authority_layer,
                    "owner_actor_id": mount.owner_actor_id,
                    "corpus_sha256": mount.corpus_sha256,
                }
                for mount in mounts
            ]
        )

    def _snapshot(self, channels: tuple[str, ...]) -> tuple[list[dict[str, Any]], str, str]:
        rows: list[dict[str, Any]] = []
        refs = self.client.list_kos(estado=None)
        for ref in refs:
            channel = CHANNEL_BY_STATE[ref.estado]
            if channel not in channels:
                continue
            ko = self.client.get_ko(ref.id)
            source_digest = _digest(
                {
                    "id": ko.id,
                    "title": ko.titulo,
                    "type": ko.tipo,
                    "version": ko.version,
                    "state": ko.estado,
                    "authority": ko.autoridad,
                    "source": ko.source,
                    "content": ko.content,
                    "namespace": ko.namespace,
                }
            )
            rows.append(
                {
                    "ko_id": ko.id,
                    "title": ko.titulo,
                    "content": ko.content,
                    "authority": ko.autoridad,
                    "state": ko.estado,
                    "channel": channel,
                    "source": ko.source,
                    "source_digest": source_digest,
                    "namespace": ko.namespace,
                }
            )
        rows.sort(key=lambda row: (row["authority"], row["ko_id"]))
        return rows, _digest(rows), self._mounts_digest()

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        try:
            descriptor = os.open(path, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def rebuild(self, *, include_channels: Iterable[str] | None = None) -> dict[str, Any]:
        channels = _channels(include_channels)
        records, corpus_digest, mounts_digest = self._snapshot(channels)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with workspace_lock(self.root, "derived-knowledge-index"):
            descriptor, name = tempfile.mkstemp(
                prefix=f".{self.database.name}.", suffix=".tmp", dir=self.database.parent
            )
            os.close(descriptor)
            temporary = Path(name)
            try:
                with closing(sqlite3.connect(temporary)) as connection:
                    connection.execute(
                        "CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
                    )
                    connection.execute(
                        """CREATE TABLE documents(
                        ko_id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL,
                        authority TEXT NOT NULL, state TEXT NOT NULL, channel TEXT NOT NULL,
                        source TEXT NOT NULL, source_digest TEXT NOT NULL, namespace TEXT
                        )"""
                    )
                    mode = "fallback-like"
                    if not self.force_fallback:
                        try:
                            connection.execute(
                                "CREATE VIRTUAL TABLE documents_fts USING "
                                "fts5(ko_id UNINDEXED, title, content)"
                            )
                            mode = "fts5"
                        except sqlite3.OperationalError:
                            mode = "fallback-like"
                    connection.executemany(
                        "INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?)",
                        [
                            (
                                row["ko_id"], row["title"], row["content"], row["authority"],
                                row["state"], row["channel"], row["source"],
                                row["source_digest"], row["namespace"],
                            )
                            for row in records
                        ],
                    )
                    if mode == "fts5":
                        connection.executemany(
                            "INSERT INTO documents_fts VALUES(?,?,?)",
                            [(row["ko_id"], row["title"], row["content"]) for row in records],
                        )
                    metadata = {
                        "schema": INDEX_SCHEMA,
                        "corpus_digest": corpus_digest,
                        "mounts_digest": mounts_digest,
                        "documents_digest": corpus_digest,
                        "channels": json.dumps(channels, separators=(",", ":")),
                        "search_mode": mode,
                        "authoritative": "false",
                        "rebuildable": "true",
                    }
                    connection.executemany(
                        "INSERT INTO metadata VALUES(?,?)", sorted(metadata.items())
                    )
                    connection.commit()
                os.replace(temporary, self.database)
                self._fsync_directory(self.database.parent)
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        return {
            "schema": INDEX_SCHEMA,
            "status": "rebuilt",
            "documents": len(records),
            "channels": list(channels),
            "corpus_digest": corpus_digest,
            "mounts_digest": mounts_digest,
            "search_mode": mode,
            "authoritative": False,
            "rebuildable": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def _open_readonly(self) -> sqlite3.Connection:
        if self.database.is_symlink() or not self.database.is_file():
            raise IndexContractError("índice ausente; ejecute rebuild")
        try:
            connection = sqlite3.connect(f"file:{self.database}?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            connection.execute("BEGIN")
            return connection
        except sqlite3.Error as exc:
            raise IndexContractError("índice ilegible") from exc

    @staticmethod
    def _stored_snapshot(
        connection: sqlite3.Connection, *, search_mode: str
    ) -> tuple[list[dict[str, Any]], str]:
        try:
            rows = [
                dict(row)
                for row in connection.execute(
                    "SELECT ko_id,title,content,authority,state,channel,source,"
                    "source_digest,namespace FROM documents ORDER BY authority,ko_id"
                )
            ]
            if search_mode == "fts5":
                observed_fts = [
                    tuple(row)
                    for row in connection.execute(
                        "SELECT ko_id,title,content FROM documents_fts ORDER BY ko_id"
                    )
                ]
                expected_fts = sorted(
                    (row["ko_id"], row["title"], row["content"]) for row in rows
                )
                if observed_fts != expected_fts:
                    raise IndexIntegrityError("tabla FTS no coincide con documents")
            elif search_mode != "fallback-like":
                raise IndexIntegrityError("search_mode de índice no soportado")
        except sqlite3.Error as exc:
            raise IndexIntegrityError("tablas derivadas ilegibles") from exc
        return rows, _digest(rows)

    def _validate_connection(
        self, connection: sqlite3.Connection
    ) -> tuple[dict[str, str], tuple[str, ...], list[dict[str, Any]], str, str]:
        try:
            metadata = dict(connection.execute("SELECT key,value FROM metadata"))
        except sqlite3.Error as exc:
            raise IndexContractError("metadata de índice ilegible") from exc
        if metadata.get("schema") != INDEX_SCHEMA:
            raise IndexContractError("schema de índice no soportado")
        try:
            channels = _channels(json.loads(metadata["channels"]))
        except (KeyError, json.JSONDecodeError, TypeError) as exc:
            raise IndexIntegrityError("channels de índice inválidos") from exc
        stored_rows, stored_digest = self._stored_snapshot(
            connection, search_mode=metadata.get("search_mode", "")
        )
        if metadata.get("documents_digest") != stored_digest:
            raise IndexIntegrityError("documents fue manipulado; ejecute rebuild")
        records, corpus_digest, mounts_digest = self._snapshot(channels)
        snapshot_is_current = (
            metadata.get("corpus_digest") == corpus_digest
            and metadata.get("mounts_digest") == mounts_digest
        )
        if snapshot_is_current and stored_rows != records:
            raise IndexIntegrityError("documents no coincide con el corpus canónico")
        return metadata, channels, records, corpus_digest, mounts_digest

    def status(self) -> dict[str, Any]:
        with closing(self._open_readonly()) as connection:
            metadata, channels, records, corpus_digest, mounts_digest = (
                self._validate_connection(connection)
            )
        stale = (
            metadata.get("corpus_digest") != corpus_digest
            or metadata.get("mounts_digest") != mounts_digest
        )
        return {
            "schema": INDEX_SCHEMA,
            "status": "stale" if stale else "ready",
            "documents": len(records),
            "channels": list(channels),
            "search_mode": metadata.get("search_mode"),
            "expected_corpus_digest": metadata.get("corpus_digest"),
            "observed_corpus_digest": corpus_digest,
            "expected_mounts_digest": metadata.get("mounts_digest"),
            "observed_mounts_digest": mounts_digest,
            "authoritative": False,
            "rebuildable": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def search(
        self,
        query: str,
        *,
        include_channels: Iterable[str] | None = None,
        limit: int = 10,
    ) -> list[IndexedKnowledgeResult]:
        if not isinstance(query, str) or not query.strip():
            raise IndexContractError("query no puede estar vacío")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise IndexContractError("limit debe estar entre 1 y 100")
        requested = _channels(include_channels)
        placeholders = ",".join("?" for _ in requested)
        with closing(self._open_readonly()) as connection:
            metadata, built_channels, _records, corpus_digest, mounts_digest = (
                self._validate_connection(connection)
            )
            if (
                metadata.get("corpus_digest") != corpus_digest
                or metadata.get("mounts_digest") != mounts_digest
            ):
                raise IndexStaleError("índice stale; ejecute rebuild antes de consultar")
            if not set(requested) <= set(built_channels):
                raise IndexContractError(
                    "el índice no contiene los canales solicitados; rebuild con opt-in explícito"
                )
            if metadata["search_mode"] == "fts5":
                tokens = re.findall(r"[\w-]+", query, flags=re.UNICODE)
                if not tokens:
                    return []
                expression = " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)
                rows = connection.execute(
                    f"""SELECT d.*, bm25(documents_fts) AS score
                    FROM documents_fts f JOIN documents d ON d.ko_id=f.ko_id
                    WHERE documents_fts MATCH ? AND d.channel IN ({placeholders})
                    ORDER BY score, d.authority, d.ko_id LIMIT ?""",
                    [expression, *requested, limit],
                ).fetchall()
            else:
                pattern = "%" + query.lower() + "%"
                rows = connection.execute(
                    f"""SELECT d.*, NULL AS score FROM documents d
                    WHERE (lower(title) LIKE ? OR lower(content) LIKE ?)
                      AND d.channel IN ({placeholders})
                    ORDER BY d.authority, d.ko_id LIMIT ?""",
                    [pattern, pattern, *requested, limit],
                ).fetchall()
        return [
            IndexedKnowledgeResult(
                ko_id=row["ko_id"], title=row["title"], authority=row["authority"],
                state=row["state"], channel=row["channel"], source=row["source"],
                source_digest=row["source_digest"], namespace=row["namespace"],
                score=float(row["score"]) if row["score"] is not None else None,
            )
            for row in rows
        ]


__all__ = [
    "CANONICAL_CHANNELS", "DerivedKnowledgeIndex", "IndexContractError",
    "IndexIntegrityError", "IndexedKnowledgeResult", "IndexStaleError",
]
