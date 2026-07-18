from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import socket
import stat
import tempfile


class WorkspaceLockError(RuntimeError):
    """Otro proceso conserva el lock cooperativo de un recurso EDAIOS."""


def resolve_contained_path(root, relative, *, required_prefix=None):
    """Resuelve una ruta bajo root sin traversal, symlinks ni raíz vacía."""
    base = Path(root).expanduser()
    if base.is_symlink():
        raise ValueError("workspace root no puede ser symlink")
    base = base.resolve(strict=True)
    target = Path(relative).expanduser()
    target = target if target.is_absolute() else base / target
    if ".." in target.parts:
        raise ValueError("path traversal no admitido")
    resolved = target.resolve(strict=False)
    rel = resolved.relative_to(base)
    if not rel.parts or (required_prefix and rel.parts[0] != required_prefix):
        raise ValueError("ruta fuera del workspace permitido")
    cursor = base
    for part in rel.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError(f"symlink no admitido: {cursor}")
    return base, resolved


def _fsync_directory(path: Path) -> None:
    """Persiste cambios de nombres cuando el sistema operativo lo permite."""
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_bytes(path, content: bytes) -> Path:
    """Escribe en el mismo filesystem y publica con un unico ``os.replace``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    local = ".edaios" in path.parts
    if local:
        path.parent.chmod(0o700)
    mode = 0o600 if local else 0o644
    try:
        existing_mode = stat.S_IMODE(path.stat().st_mode)
        mode = 0o600 if local else existing_mode
    except OSError:
        pass

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        temporary.unlink(missing_ok=True)
        raise
    return path


def atomic_write_many(entries) -> tuple[Path, ...]:
    """Publica un conjunto de archivos con compensación verificable.

    Cada destino se prepara en su mismo directorio; si una publicación falla,
    los destinos ya reemplazados se restauran byte a byte desde sus backups.
    El llamador debe mantener ``workspace_lock`` durante la operación.
    """
    prepared: list[tuple[Path, Path]] = []
    published: list[tuple[Path, bytes | None]] = []
    try:
        for raw_path, content in entries:
            path = Path(raw_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            previous = path.read_bytes() if path.is_file() and not path.is_symlink() else None
            fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
            temporary = Path(name)
            with os.fdopen(fd, "wb") as handle:
                handle.write(bytes(content))
                handle.flush()
                os.fsync(handle.fileno())
            prepared.append((path, temporary))
            published.append((path, previous))
        for path, temporary in prepared:
            os.replace(temporary, path)
            _fsync_directory(path.parent)
        return tuple(path for path, _ in published)
    except BaseException:
        for path, previous in reversed(published):
            try:
                if previous is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write_bytes(path, previous)
            except OSError:
                pass
        raise
    finally:
        for _path, temporary in prepared:
            temporary.unlink(missing_ok=True)

def write_text(path, content):
    normalized = str(content).rstrip() + "\n"
    return atomic_write_bytes(path, normalized.encode("utf-8"))


def _lock_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.")
    if not safe:
        raise ValueError("el nombre del lock no puede estar vacio")
    return safe


@contextmanager
def workspace_lock(workspace_root, name: str):
    """Exclusion fail-closed entre procesos que cooperan en un workspace.

    El lock no intenta decidir automaticamente si un archivo residual esta
    obsoleto: esa recuperacion requiere confirmar que el PID ya no existe.
    """
    root = Path(workspace_root).resolve()
    lock_dir = root / ".edaios" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_dir.parent.chmod(0o700)
    lock_dir.chmod(0o700)
    lock_path = lock_dir / f"{_lock_name(name)}.lock"
    payload = {
        "schema": "edaios.workspace-lock/v1",
        "resource": name,
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    try:
        fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        try:
            owner = lock_path.read_text(encoding="utf-8").strip()
        except OSError:
            owner = "metadata no disponible"
        raise WorkspaceLockError(
            f"recurso '{name}' ocupado por {lock_path}: {owner}"
        ) from exc

    try:
        raw = (json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_directory(lock_dir)
        yield lock_path
    finally:
        if fd >= 0:
            os.close(fd)
        lock_path.unlink(missing_ok=True)
        _fsync_directory(lock_dir)

def read_text(path):
    return Path(path).read_text(encoding="utf-8")

def read_spec(path):
    path = Path(path)
    text = read_text(path)
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return parse_simple_yaml(text)

_SIMPLE_KEY = re.compile(r"^[A-Za-z_][\w.-]*$")


def _scalar(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_simple_yaml(text):
    """Parser YAML plano (clave: escalar | lista de `- item`), sin dependencias.

    Misma gramatica estricta que la puerta Spec Kit: anidamiento, claves
    invalidas o estructuras fuera de este subconjunto son ValueError — un
    documento que un parser YAML real lee distinto debe FALLAR, no
    interpretarse en silencio.
    """
    data = {}
    active_list = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and active_list:
            current = data.setdefault(active_list, [])
            if not isinstance(current, list):
                raise ValueError(f"{active_list} mezcla escalar y lista")
            current.append(_scalar(stripped[2:]))
            continue
        if raw[:1].isspace():
            raise ValueError(f"estructura anidada no soportada: {stripped[:60]}")
        key, sep, value = raw.partition(":")
        key = key.strip()
        if not sep or not _SIMPLE_KEY.fullmatch(key):
            raise ValueError(f"linea invalida: {stripped[:60]}")
        value = value.strip()
        if value:
            data[key] = _scalar(value)
            active_list = None
        else:
            data[key] = []
            active_list = key
    if not data:
        raise ValueError("documento vacio")
    return data
