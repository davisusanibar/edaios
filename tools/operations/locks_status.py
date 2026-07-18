#!/usr/bin/env python3
"""Diagnóstico read-only de locks cooperativos (.edaios/locks) de un workspace.

Lista cada lock, verifica si su proceso sigue vivo (solo en el mismo host) y
sugiere la limpieza manual. Nunca borra: recuperar un lock es una decisión
humana, coherente con el contrato de workspace_lock.
"""

from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        # Sin permiso para señalar: el proceso existe.
        return True
    return True


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    locks_dir = root / ".edaios" / "locks"
    if not locks_dir.is_dir():
        print(f"[locks] OK: sin directorio de locks en {locks_dir}")
        return 0
    host = socket.gethostname()
    entries = sorted(locks_dir.glob("*.lock"))
    orphans = 0
    for path in entries:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            pid = int(payload["pid"])
            owner_host = str(payload["host"])
            created = str(payload.get("created_at", "?"))
        except (OSError, ValueError, KeyError, TypeError):
            orphans += 1
            print(f"[locks] ILEGIBLE {path.name}: metadata corrupta — confirma y borra manualmente")
            continue
        if owner_host != host:
            print(f"[locks] OTRO-HOST {path.name}: pid={pid} host={owner_host} — no verificable desde {host}")
        elif pid_alive(pid):
            print(f"[locks] VIVO {path.name}: pid={pid} creado {created}")
        else:
            orphans += 1
            print(f"[locks] HUERFANO {path.name}: pid={pid} ya no existe — `rm {path}` si lo confirmas")
    print(f"-- locks: {len(entries)} · huerfanos: {orphans} --")
    return 1 if orphans else 0


if __name__ == "__main__":
    raise SystemExit(main())
