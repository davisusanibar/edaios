"""API de solo lectura sobre Knowledge Objects en Git."""
from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from edaios_core.knowledge import (
    discover_knowledge_objects,
    discover_mounted_knowledge_objects,
    ko_body,
    provenance_block,
    looks_like_program_root,
    AICONTEXT_SCHEMA_VERSION,
    CHANNEL_BY_STATE,
    FederationError,
    KnowledgeCollisionError,
    KnowledgeMount,
    normalize_mounts,
)

__version__ = "3.1.0"

REPRESENTATION_KINDS = ("human", "aicontext", "catalog")


class SDKError(Exception):
    """Base de errores del SDK."""


class InvalidRoot(SDKError):
    """La ruta no es una raíz de programa EDAIOS."""


class KONotFound(SDKError):
    """No existe un KO con ese id."""


class RepresentationNotAvailable(SDKError):
    """El kind de representación no está soportado."""


class InvalidMount(SDKError):
    """Un mount federado no cumple el contrato explícito."""


class KOCollision(SDKError):
    """Dos KOs reclaman la misma identidad dentro de la vista."""


class InvalidKnowledge(SDKError):
    """El corpus local contiene rutas o Knowledge Objects inválidos."""


def _mounts_fingerprint(mounts) -> str:
    return json.dumps(
        mounts, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )


def _mounts_document_snapshot(path: str | Path) -> tuple[Path, str]:
    raw_path = Path(path).expanduser()
    if raw_path.is_symlink():
        raise InvalidMount("federation mounts symlink no admitido")
    try:
        resolved = raw_path.resolve(strict=True)
    except OSError as exc:
        raise InvalidMount(
            f"federation mounts no resoluble: {raw_path}"
        ) from exc
    if not resolved.is_file():
        raise InvalidMount(f"federation mounts no es archivo: {resolved}")
    try:
        digest = sha256(resolved.read_bytes()).hexdigest()
    except OSError as exc:
        raise InvalidMount(
            f"federation mounts no legible: {resolved}"
        ) from exc
    return resolved, digest


def _validate_stable_mounts_document(
    path: str | Path,
) -> tuple[Path, str, list[dict]]:
    from edaios_conformance import validate_federation_mounts

    before_path, before_digest = _mounts_document_snapshot(path)
    try:
        mounts = validate_federation_mounts(before_path)
    except (OSError, ValueError) as exc:
        raise InvalidMount(str(exc)) from exc
    after_path, after_digest = _mounts_document_snapshot(before_path)
    if before_path != after_path or before_digest != after_digest:
        raise InvalidMount("federation mounts cambió durante la validación")
    return after_path, after_digest, mounts


@dataclass(frozen=True)
class KnowledgeObjectRef:
    id: str
    titulo: str
    tipo: str
    version: str
    estado: str
    autoridad: str
    source: str
    namespace: str | None = None
    local_id: str | None = None
    mount_authority: str | None = None
    mount_owner_actor_id: str | None = None


@dataclass(frozen=True)
class KnowledgeObject:
    id: str
    titulo: str
    tipo: str
    version: str
    estado: str
    autoridad: str
    source: str
    idioma: str
    deriva_de: str
    content: str
    namespace: str | None = None
    local_id: str | None = None
    mount_authority: str | None = None
    mount_owner_actor_id: str | None = None

    def ref(self) -> KnowledgeObjectRef:
        return KnowledgeObjectRef(
            self.id, self.titulo, self.tipo, self.version,
            self.estado, self.autoridad, self.source, self.namespace,
            self.local_id, self.mount_authority, self.mount_owner_actor_id)


class KnowledgeClient:
    """Cliente de solo lectura sobre los Knowledge Objects de un programa EDAIOS."""

    def __init__(self, root: str | Path | None = "."):
        self.mounts: tuple[KnowledgeMount, ...] | None = None
        self._mounts_document: Path | None = None
        self._mounts_document_sha256: str | None = None
        self._governed_mounts_fingerprint: str | None = None
        raw_root = Path(root or ".").expanduser()
        if raw_root.is_symlink():
            raise InvalidRoot(f"La raíz de programa no puede ser symlink: {raw_root}")
        try:
            resolved = raw_root.resolve(strict=True)
        except OSError as exc:
            raise InvalidRoot(f"Raíz de programa no resoluble: {raw_root}") from exc
        if not looks_like_program_root(resolved):
            raise InvalidRoot(f"No es una raíz de programa EDAIOS: {resolved}")
        self.root = resolved

    @classmethod
    def from_mounts(cls, mounts_document: str | Path) -> "KnowledgeClient":
        """Consume un documento FederationMount gobernado y verificado."""
        if not isinstance(mounts_document, (str, Path)):
            raise InvalidMount(
                "from_mounts exige la ruta a federation-mounts.json gobernado"
            )
        document, document_sha256, mounts = _validate_stable_mounts_document(
            mounts_document
        )
        self = cls._from_validated_mounts(mounts)
        self._mounts_document = document
        self._mounts_document_sha256 = document_sha256
        self._governed_mounts_fingerprint = _mounts_fingerprint(mounts)
        self._revalidate_governed_mounts()
        return self

    @classmethod
    def _from_validated_mounts(cls, mounts) -> "KnowledgeClient":
        """Construye desde la salida de validate_federation_mounts (uso interno)."""
        self = cls.__new__(cls)
        try:
            self.mounts = normalize_mounts(mounts)
        except KnowledgeCollisionError as exc:
            raise KOCollision(str(exc)) from exc
        except FederationError as exc:
            raise InvalidMount(str(exc)) from exc
        self.root = None
        self._mounts_document = None
        self._mounts_document_sha256 = None
        self._governed_mounts_fingerprint = None
        return self

    # --- internos ---
    def _entries(self):
        if self.mounts is not None:
            try:
                yield from discover_mounted_knowledge_objects(self.mounts)
            except KnowledgeCollisionError as exc:
                raise KOCollision(str(exc)) from exc
            except FederationError as exc:
                raise InvalidMount(str(exc)) from exc
            return
        assert self.root is not None
        try:
            yield from discover_knowledge_objects(self.root)
        except FederationError as exc:
            raise InvalidKnowledge(str(exc)) from exc

    def _index(self) -> dict[str, tuple[Path, dict]]:
        idx: dict[str, tuple[Path, dict]] = {}
        for path, meta in self._entries():
            kid = meta.get("global_id") or meta.get("id", "")
            if kid:
                if kid in idx:
                    raise KOCollision(
                        f"identidad duplicada {kid}: {idx[kid][0]} y {path}"
                    )
                idx[kid] = (path, meta)
        return idx

    def _verify_federated_snapshot(self) -> None:
        if self.mounts is None:
            return
        from edaios_core.knowledge import corpus_digest

        for mount in self.mounts:
            try:
                observed_digest = corpus_digest(mount)
            except FederationError as exc:
                raise InvalidMount(str(exc)) from exc
            if observed_digest != mount.corpus_sha256:
                raise InvalidMount(
                    f"{mount.namespace}: corpus cambió durante la lectura final"
                )

    def _revalidate_governed_mounts(self) -> None:
        if self._mounts_document is None:
            self._verify_federated_snapshot()
            return
        document, document_sha256, mounts = _validate_stable_mounts_document(
            self._mounts_document
        )
        if (
            document != self._mounts_document
            or document_sha256 != self._mounts_document_sha256
            or _mounts_fingerprint(mounts)
            != self._governed_mounts_fingerprint
        ):
            raise InvalidMount(
                "federation mounts o su autoridad cambiaron; reconstruya el cliente"
            )

    @contextmanager
    def _governed_operation(self):
        self._revalidate_governed_mounts()
        try:
            yield
        except BaseException:
            raise
        else:
            self._revalidate_governed_mounts()

    def _source(self, meta: dict, path: Path) -> str:
        if self.mounts is not None:
            return f"{meta['namespace']}:{meta['source']}"
        assert self.root is not None
        return str(path.relative_to(self.root))

    def _to_ref(self, meta: dict, path: Path) -> KnowledgeObjectRef:
        return KnowledgeObjectRef(
            id=meta.get("global_id") or meta.get("id", ""),
            titulo=meta.get("titulo", ""),
            tipo=meta.get("tipo", ""),
            version=meta.get("version", ""),
            estado=meta.get("estado", ""),
            autoridad=meta.get("autoridad", ""),
            source=self._source(meta, path),
            namespace=meta.get("namespace"),
            local_id=meta.get("local_id"),
            mount_authority=meta.get("mount_authority"),
            mount_owner_actor_id=meta.get("mount_owner_actor_id"),
        )

    def _to_ko(self, meta: dict, path: Path) -> KnowledgeObject:
        raw = path.read_text(encoding="utf-8", errors="strict")
        value = KnowledgeObject(
            id=meta.get("global_id") or meta.get("id", ""),
            titulo=meta.get("titulo", ""),
            tipo=meta.get("tipo", ""),
            version=meta.get("version", ""),
            estado=meta.get("estado", ""),
            autoridad=meta.get("autoridad", ""),
            source=self._source(meta, path),
            idioma=meta.get("idioma", "es"),
            deriva_de=meta.get("deriva_de", ""),
            content=ko_body(raw),
            namespace=meta.get("namespace"),
            local_id=meta.get("local_id"),
            mount_authority=meta.get("mount_authority"),
            mount_owner_actor_id=meta.get("mount_owner_actor_id"),
        )
        self._verify_federated_snapshot()
        return value

    # --- API pública (contrato §2 de la spec) ---
    def list_kos(self, estado: str | None = "Ratificado", autoridad: str | None = None,
                 tipo: str | None = None, include_states: list[str] | None = None) -> list[KnowledgeObjectRef]:
        with self._governed_operation():
            states = (
                set(include_states)
                if include_states
                else ({estado} if estado else None)
            )
            refs: list[KnowledgeObjectRef] = []
            for path, meta in self._entries():
                if states is not None and meta.get("estado") not in states:
                    continue
                if autoridad is not None and meta.get("autoridad") != autoridad:
                    continue
                if tipo is not None and meta.get("tipo") != tipo:
                    continue
                refs.append(self._to_ref(meta, path))
            refs.sort(key=lambda r: (r.autoridad, r.id))
            return refs

    def iter_kos(self, **filters):
        with self._governed_operation():
            values = [
                self.get_ko(ref.id) for ref in self.list_kos(**filters)
            ]
            return iter(values)

    def get_ko(self, ko_id: str) -> KnowledgeObject:
        with self._governed_operation():
            entry = self._index().get(ko_id)
            if entry is None:
                raise KONotFound(ko_id)
            path, meta = entry
            return self._to_ko(meta, path)

    def get_representation(self, ko_id: str, kind: str = "human"):
        with self._governed_operation():
            if kind not in REPRESENTATION_KINDS:
                raise RepresentationNotAvailable(kind)
            entry = self._index().get(ko_id)
            if entry is None:
                raise KONotFound(ko_id)
            path, meta = entry
            raw = path.read_text(encoding="utf-8", errors="strict")
            rel = self._source(meta, path)
            channel = CHANNEL_BY_STATE[meta["estado"]]
            ko_id = meta.get("global_id") or meta.get("id", "")

            if kind == "human":
                provenance_meta = dict(meta)
                provenance_meta["id"] = ko_id
                return provenance_block(provenance_meta, rel) + raw

            if kind == "aicontext":
                return {
                    "schema_version": AICONTEXT_SCHEMA_VERSION,
                    "ko_id": ko_id,
                    "titulo": meta.get("titulo", ""),
                    "tipo": meta.get("tipo", ""),
                    "version": meta.get("version", ""),
                    "estado": meta.get("estado", ""),
                    "autoridad": meta.get("autoridad", ""),
                    "idioma": meta.get("idioma", "es"),
                    "deriva_de": meta.get("deriva_de", ""),
                    "source": rel,
                    "commit": None,
                    "snapshot": "working-tree-unsealed",
                    "channel": channel,
                    "content": ko_body(raw),
                    "namespace": meta.get("namespace"),
                    "local_id": meta.get("local_id"),
                }

            # kind == "catalog"
            return {
                "ko_id": ko_id, "titulo": meta.get("titulo", ""),
                "channel": channel, "source": rel,
                "namespace": meta.get("namespace"),
                "local_id": meta.get("local_id"),
            }

    def search(self, text: str) -> list[KnowledgeObjectRef]:
        with self._governed_operation():
            needle = text.lower()
            hits: list[KnowledgeObjectRef] = []
            for path, meta in self._entries():
                raw = path.read_text(encoding="utf-8", errors="strict")
                if (
                    needle in meta.get("titulo", "").lower()
                    or needle in raw.lower()
                ):
                    hits.append(self._to_ref(meta, path))
            hits.sort(key=lambda r: (r.autoridad, r.id))
            return hits


# Superficie aditiva: no cambia la semántica de ``KnowledgeClient.search``.
from .derived_index import (  # noqa: E402  (las clases base ya están definidas)
    DerivedKnowledgeIndex,
    IndexContractError,
    IndexIntegrityError,
    IndexedKnowledgeResult,
    IndexStaleError,
)


__all__ = [
    "DerivedKnowledgeIndex", "IndexContractError", "IndexIntegrityError", "IndexedKnowledgeResult",
    "IndexStaleError", "InvalidKnowledge", "InvalidMount", "InvalidRoot",
    "KOCollision", "KONotFound", "KnowledgeClient", "KnowledgeObject",
    "KnowledgeObjectRef", "RepresentationNotAvailable", "SDKError",
]
