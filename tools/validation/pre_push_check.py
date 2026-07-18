#!/usr/bin/env python3
"""Verifica cada revision que Git anuncia al pre-push, en un worktree limpio."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

ZERO = "0" * 40


def main() -> int:
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    rows = [line.split() for line in sys.stdin.read().splitlines() if line.strip()]
    if not rows:
        print("[pre-push] FAIL: Git no anunció ninguna ref")
        return 1
    for row in rows:
        if len(row) != 4:
            print(f"[pre-push] FAIL: ref malformada: {row}")
            return 1
        _local_ref, local_oid, _remote_ref, _remote_oid = row
        if local_oid == ZERO:
            continue
        try:
            subprocess.run(["git", "cat-file", "-e", f"{local_oid}^{{commit}}"], cwd=root, check=True)
        except subprocess.CalledProcessError:
            print(f"[pre-push] FAIL: objeto local inexistente: {local_oid}")
            return 1
        with tempfile.TemporaryDirectory(prefix="edaios-pre-push-") as temp_name:
            temp = Path(temp_name)
            try:
                subprocess.run(["git", "worktree", "add", "--detach", str(temp), local_oid], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                env = os.environ.copy()
                env["EDAIOS_GATE_ROOT"] = str(temp)
                result = subprocess.run(
                    [sys.executable, str(root / "scripts/run-gates.py"), "--scope", "pre-push"],
                    cwd=temp, env=env,
                )
                if result.returncode:
                    print(f"[pre-push] FAIL: gates rojos para {local_oid}")
                    return result.returncode
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(temp)], cwd=root, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("[pre-push] OK: todas las revisiones anunciadas verificadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
