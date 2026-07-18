"""Descubrimiento read-only de Knowledge Objects sin publicador ni CLI."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Iterator

FIELDS = {
    "id", "tipo", "titulo", "version", "estado", "autoridad", "idioma",
    "owner", "deriva_de",
}
CHANNEL_BY_STATE = {
    "Borrador": "draft",
    "Propuesto": "review",
    "Ratificado": "normative",
    "Derogado": "superseded",
}
AICONTEXT_SCHEMA_VERSION = "edaios.aicontext/v1"
NAMESPACE_PATTERN = r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9-]*)+"
NAMESPACE_RE = re.compile(rf"^{NAMESPACE_PATTERN}$")
KO_ID_RE = re.compile(
    r"^(?:KO-[A-Z0-9][A-Z0-9-]*|ART-[0-9]{3}|PAT-[0-9]{3}|PLB-[0-9]{3})$"
)
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
AUTHORITY_LAYERS = frozenset({"Foundation", "Framework", "Core", "Consumer"})


class FederationError(ValueError):
    """Un mount federado no puede resolverse de forma inequívoca."""


class KnowledgeCollisionError(FederationError):
    """Dos objetos reclaman la misma identidad global."""


@dataclass(frozen=True)
class KnowledgeMount:
    """Corpus Git explícito que participa en una vista federada derivada.

    ``path`` puede apuntar a una raíz de programa EDAIOS o directamente al
    directorio que contiene Knowledge Objects. El namespace es parte de la
    identidad global. ``authority_layer`` se comprueba contra cada KO y
    ``owner_actor_id`` debe resolver a un actor activo del attachment; son
    dimensiones distintas y ninguna se infiere del corpus.
    """

    namespace: str
    path: Path
    authority_layer: str
    owner_actor_id: str
    allowed_owner_actor_ids: tuple[str, ...]
    authorized_root: Path | None = None
    corpus_sha256: str | None = None

    @classmethod
    def from_value(cls, value: "KnowledgeMount | dict[str, object]") -> "KnowledgeMount":
        if isinstance(value, cls):
            candidate = value
        elif isinstance(value, dict):
            missing = {
                "namespace", "path", "authority_layer", "owner_actor_id",
                "allowed_owner_actor_ids", "authorized_root", "corpus_sha256",
            } - set(value)
            if missing:
                raise FederationError(
                    f"mount incompleto; faltan {', '.join(sorted(missing))}"
                )
            candidate = cls(
                namespace=str(value["namespace"]),
                path=Path(str(value["path"])),
                authority_layer=str(value["authority_layer"]),
                owner_actor_id=str(value["owner_actor_id"]),
                allowed_owner_actor_ids=tuple(
                    str(item) for item in value["allowed_owner_actor_ids"]
                ),
                authorized_root=(
                    Path(str(value["authorized_root"]))
                    if value.get("authorized_root") is not None
                    else None
                ),
                corpus_sha256=(
                    str(value["corpus_sha256"])
                    if value.get("corpus_sha256") is not None
                    else None
                ),
            )
        else:
            raise FederationError("mount debe ser KnowledgeMount u objeto")

        namespace = candidate.namespace.strip()
        authority_layer = candidate.authority_layer.strip()
        owner_actor_id = candidate.owner_actor_id.strip()
        allowed_owner_actor_ids = tuple(
            sorted({item.strip() for item in candidate.allowed_owner_actor_ids if item.strip()})
        )
        if not NAMESPACE_RE.fullmatch(namespace):
            raise FederationError(f"namespace inválido: {namespace!r}")
        if authority_layer != "Consumer":
            raise FederationError(
                f"{namespace}: authority_layer debe ser Consumer en una iniciativa"
            )
        if not owner_actor_id:
            raise FederationError(f"{namespace}: owner_actor_id es obligatorio")
        if owner_actor_id not in allowed_owner_actor_ids:
            raise FederationError(
                f"{namespace}: owner_actor_id no pertenece a owners activos"
            )
        if candidate.authorized_root is None:
            raise FederationError(f"{namespace}: authorized_root es obligatorio")
        corpus_sha256 = candidate.corpus_sha256
        if (
            corpus_sha256 is not None
            and re.fullmatch(r"[0-9a-f]{64}", corpus_sha256) is None
        ):
            raise FederationError(f"{namespace}: corpus_sha256 invalido")
        authorized_root = candidate.authorized_root
        path = resolve_authorized_path(
            candidate.path,
            authorized_root,
            expected="directory",
            label=f"{namespace}: mount",
        )
        return cls(
            namespace=namespace,
            path=path,
            authority_layer=authority_layer,
            owner_actor_id=owner_actor_id,
            allowed_owner_actor_ids=allowed_owner_actor_ids,
            authorized_root=Path(authorized_root).expanduser().resolve(strict=True),
            corpus_sha256=corpus_sha256,
        )


def _lexical_absolute(value: str | Path, *, label: str) -> Path:
    raw = Path(value).expanduser()
    if ".." in raw.parts:
        raise FederationError(f"{label}: path traversal no permitido: {raw}")
    return raw if raw.is_absolute() else Path.cwd() / raw


def resolve_authorized_path(
    value: str | Path,
    authorized_root: str | Path,
    *,
    expected: str | None = None,
    label: str = "mount",
) -> Path:
    """Resuelve una ruta sin permitir traversal, symlinks ni escape del root.

    El root es una frontera confiable declarada por un attachment gobernado. Un
    mount no puede autoautorizar su propio path omitiendo esta frontera.
    """
    candidate = _lexical_absolute(value, label=label)
    root = _lexical_absolute(authorized_root, label=f"{label} root autorizado")
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise FederationError(
            f"{label}: ruta fuera del root autorizado: {candidate}"
        ) from exc

    if root.is_symlink():
        raise FederationError(f"{label}: root autorizado symlink no permitido: {root}")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise FederationError(f"{label}: symlink no permitido: {cursor}")

    try:
        resolved_root = root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise FederationError(f"{label}: ruta no resoluble: {candidate}") from exc
    if not resolved_root.is_dir():
        raise FederationError(
            f"{label}: root autorizado no es directorio: {resolved_root}"
        )
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise FederationError(
            f"{label}: ruta resuelta fuera del root autorizado: {resolved}"
        ) from exc
    if expected == "directory" and not resolved.is_dir():
        raise FederationError(f"{label}: no es directorio: {resolved}")
    if expected == "file" and not resolved.is_file():
        raise FederationError(f"{label}: no es archivo: {resolved}")
    return resolved


def _iter_mount_entries(
    mount: KnowledgeMount,
    root: str | Path,
) -> Iterator[Path]:
    """Recorre archivos regulares sin seguir ni ocultar symlinks."""
    authorized_root = mount.authorized_root or mount.path
    start = resolve_authorized_path(
        root,
        authorized_root,
        expected="directory",
        label=f"{mount.namespace}: corpus",
    )

    def visit(directory: Path) -> Iterator[Path]:
        try:
            entries = sorted(directory.iterdir())
        except OSError as exc:
            raise FederationError(
                f"{mount.namespace}: corpus no legible: {directory}"
            ) from exc
        for entry in entries:
            resolved = resolve_authorized_path(
                entry,
                authorized_root,
                label=f"{mount.namespace}: corpus",
            )
            if resolved.is_dir():
                yield from visit(resolved)
            elif resolved.is_file():
                yield resolved

    yield from visit(start)


def iter_mount_files(
    mount: KnowledgeMount,
    root: str | Path,
    *,
    suffix: str,
) -> Iterator[Path]:
    """Recorre un corpus sin seguir ni ignorar silenciosamente symlinks."""
    for path in _iter_mount_entries(mount, root):
        if path.suffix == suffix:
            yield path


def corpus_digest(mount: KnowledgeMount, root: str | Path | None = None) -> str:
    """Liga paths y bytes del corpus a una huella determinista fail-closed."""
    corpus = mount.path if root is None else Path(root)
    digest = sha256(b"edaios.corpus-digest/v1\0")
    for path in _iter_mount_entries(mount, corpus):
        content = path.read_bytes()
        row = {
            "path": path.relative_to(corpus).as_posix(),
            "sha256": sha256(content).hexdigest(),
            "size": len(content),
        }
        digest.update(
            json.dumps(
                row, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def normalize_mounts(
    mounts: list[KnowledgeMount | dict[str, object]]
    | tuple[KnowledgeMount | dict[str, object], ...],
    *,
    minimum: int = 2,
) -> tuple[KnowledgeMount, ...]:
    """Normaliza mounts y rechaza aliases o namespaces duplicados."""
    if not mounts or len(mounts) < minimum:
        raise FederationError(
            f"la vista exige al menos {minimum} mounts gobernados explícitos"
        )
    normalized = tuple(KnowledgeMount.from_value(value) for value in mounts)
    namespaces: set[str] = set()
    paths: set[Path] = set()
    for mount in normalized:
        if mount.namespace in namespaces:
            raise KnowledgeCollisionError(
                f"namespace federado duplicado: {mount.namespace}"
            )
        if mount.path in paths:
            raise KnowledgeCollisionError(
                f"un mismo corpus no puede montarse dos veces: {mount.path}"
            )
        namespaces.add(mount.namespace)
        paths.add(mount.path)
    return normalized


def global_identity(namespace: str, local_id: str) -> str:
    if not local_id or ":" in local_id:
        raise FederationError(f"id local inválido para {namespace}: {local_id!r}")
    return f"{namespace}:{local_id}"


def _knowledge_root(mount: KnowledgeMount) -> Path:
    foundation = mount.path / "core" / "foundation"
    if foundation.exists() or foundation.is_symlink():
        return resolve_authorized_path(
            foundation,
            mount.authorized_root or mount.path,
            expected="directory",
            label=f"{mount.namespace}: Foundation",
        )
    return mount.path


def looks_like_program_root(root: Path) -> bool:
    try:
        resolve_authorized_path(
            root / "README.md", root, expected="file", label="program README"
        )
        resolve_authorized_path(
            root / "core" / "foundation",
            root,
            expected="directory",
            label="program Foundation",
        )
        resolve_authorized_path(
            root / "governance" / "ADR_CATALOG.md",
            root,
            expected="file",
            label="program ADR catalog",
        )
    except FederationError:
        return False
    return True


def _iter_local_files(root: Path, *, suffix: str) -> Iterator[Path]:
    """Recorre el corpus local sin seguir symlinks ni ocultar errores."""
    if root.is_symlink():
        raise FederationError(f"corpus local symlink no permitido: {root}")
    if not root.is_dir():
        raise FederationError(f"corpus local no resoluble: {root}")

    def visit(directory: Path) -> Iterator[Path]:
        try:
            entries = sorted(directory.iterdir())
        except OSError as exc:
            raise FederationError(f"corpus local no legible: {directory}") from exc
        for entry in entries:
            if entry.is_symlink():
                raise FederationError(f"corpus local contiene symlink: {entry}")
            if entry.is_dir():
                yield from visit(entry)
            elif entry.is_file() and entry.suffix == suffix:
                yield entry

    yield from visit(root)


def has_front_matter(raw: str) -> bool:
    return raw.startswith("---\n")


def split_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---\n", 3)
    if end < 0:
        raise FederationError("front matter truncado: falta delimitador de cierre")
    meta: dict[str, str] = {}
    seen: set[str] = set()
    for line in raw[4:end].splitlines():
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in seen:
            raise FederationError(f"front matter contiene clave duplicada: {key}")
        seen.add(key)
        if key in FIELDS:
            meta[key] = value.strip().strip("'\"")
    return meta, raw[end + 5 :]


def validate_knowledge_object(
    meta: dict[str, str], body: str, *, source: str
) -> None:
    """Valida valores KOM mínimos que un reader puede aplicar sin inferencias."""
    missing = FIELDS - set(meta)
    if missing:
        raise FederationError(
            f"{source}: front matter incompleto; faltan {', '.join(sorted(missing))}"
        )
    empty = sorted(field for field in FIELDS if not meta.get(field, "").strip())
    if empty:
        raise FederationError(
            f"{source}: campos KOM vacíos: {', '.join(empty)}"
        )
    if KO_ID_RE.fullmatch(meta["id"]) is None:
        raise FederationError(f"{source}: id KO no canónico: {meta['id']!r}")
    if SEMVER_RE.fullmatch(meta["version"]) is None:
        raise FederationError(f"{source}: version KO no es SemVer estable")
    if meta["estado"] not in CHANNEL_BY_STATE:
        raise FederationError(f"{source}: estado KO no soportado: {meta['estado']!r}")
    if meta["autoridad"] not in AUTHORITY_LAYERS:
        raise FederationError(
            f"{source}: capa de autoridad KO no soportada: {meta['autoridad']!r}"
        )
    if meta["idioma"] != "es":
        raise FederationError(f"{source}: idioma normativo debe ser 'es'")
    if not body.strip():
        raise FederationError(f"{source}: cuerpo KO vacío")


def discover_knowledge_objects(root: Path) -> Iterator[tuple[Path, dict[str, str]]]:
    authority_candidate = root / "core" / "foundation"
    if not authority_candidate.exists() and not authority_candidate.is_symlink():
        return
    authority = resolve_authorized_path(
        authority_candidate,
        root,
        expected="directory",
        label="Foundation local",
    )
    for path in _iter_local_files(authority, suffix=".md"):
        raw = path.read_text(encoding="utf-8", errors="strict")
        if not has_front_matter(raw):
            continue
        meta, body = split_front_matter(raw)
        validate_knowledge_object(
            meta, body, source=path.relative_to(authority).as_posix()
        )
        yield path, meta


def discover_mounted_knowledge_objects(
    mounts: list[KnowledgeMount | dict[str, object]]
    | tuple[KnowledgeMount | dict[str, object], ...],
) -> Iterator[tuple[Path, dict[str, str]]]:
    """Descubre KOs únicamente desde mounts declarados y con identidad global.

    La función no busca repositorios vecinos ni infiere dominios. Dos KOs con el
    mismo id local son válidos en namespaces distintos; cualquier colisión de
    identidad global, front matter incompleto o autoridad discordante falla.
    """
    seen: dict[str, Path] = {}
    for mount in normalize_mounts(mounts):
        corpus = _knowledge_root(mount)
        if (
            mount.corpus_sha256 is not None
            and corpus_digest(mount) != mount.corpus_sha256
        ):
            raise FederationError(
                f"{mount.namespace}: digest de corpus no coincide antes del consumo"
            )
        for path in iter_mount_files(mount, corpus, suffix=".md"):
            raw = path.read_text(encoding="utf-8", errors="strict")
            if not has_front_matter(raw):
                continue
            meta, body = split_front_matter(raw)
            source = f"{mount.namespace}:{path.relative_to(corpus)}"
            validate_knowledge_object(meta, body, source=source)
            if meta["autoridad"] != mount.authority_layer:
                raise FederationError(
                    f"{mount.namespace}:{meta['id']}: authority layer "
                    f"{meta['autoridad']!r} no coincide con "
                    f"{mount.authority_layer!r}"
                )
            if meta["owner"] not in mount.allowed_owner_actor_ids:
                raise FederationError(
                    f"{mount.namespace}:{meta['id']}: owner {meta['owner']!r} "
                    "no está activo en AuthorityRegistry"
                )
            gid = global_identity(mount.namespace, meta["id"])
            if gid in seen:
                raise KnowledgeCollisionError(
                    f"identidad global duplicada {gid}: {seen[gid]} y {path}"
                )
            seen[gid] = path
            enriched = dict(meta)
            enriched.update(
                {
                    "namespace": mount.namespace,
                    "local_id": meta["id"],
                    "global_id": gid,
                    "mount_authority": mount.authority_layer,
                    "mount_owner_actor_id": mount.owner_actor_id,
                    "mount_root": str(mount.path),
                    "source": path.relative_to(corpus).as_posix(),
                }
            )
            yield path, enriched
        if (
            mount.corpus_sha256 is not None
            and corpus_digest(mount) != mount.corpus_sha256
        ):
            raise FederationError(
                f"{mount.namespace}: corpus cambio durante el consumo"
            )


def discover_knowledge_issues(root: Path) -> Iterator[tuple[Path, frozenset[str]]]:
    """Archivos con front matter presente pero contrato KOM incompleto.

    discover_knowledge_objects no publica estos archivos; este canal los hace
    visibles para que un gate o consumidor los reporte en vez de omitirlos en
    silencio. Cada item es (ruta, campos KOM faltantes).
    """
    authority_candidate = root / "core" / "foundation"
    if not authority_candidate.exists() and not authority_candidate.is_symlink():
        return
    authority = resolve_authorized_path(
        authority_candidate,
        root,
        expected="directory",
        label="Foundation local",
    )
    for path in _iter_local_files(authority, suffix=".md"):
        raw = path.read_text(encoding="utf-8", errors="strict")
        if not has_front_matter(raw):
            continue
        meta, _body = split_front_matter(raw)
        missing = FIELDS - set(meta)
        if missing:
            yield path, frozenset(missing)


def ko_body(raw: str) -> str:
    return split_front_matter(raw)[1]


def provenance_block(meta: dict[str, str], source: str) -> str:
    return (
        "<!-- EDAIOS-PROVENANCE "
        f"id={meta.get('id', '')} version={meta.get('version', '')} "
        f"state={meta.get('estado', '')} source={source} -->\n"
    )
