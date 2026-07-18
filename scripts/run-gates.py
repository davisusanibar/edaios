#!/usr/bin/env python3
"""Ejecuta gates por scope desde el registro canónico, sin shell implícito."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path


ROOT = Path(os.environ.get("EDAIOS_GATE_ROOT", Path(__file__).resolve().parents[1])).resolve()
REQUIRED_SCOPES = {
    "FND-PROJECTION", "CATALOG-PROJECTION", "AGENT-PARITY", "SDD-CONTRACT",
    "KOM", "MONOREPO-STRUCTURE", "TRACEABILITY", "BASELINE-SURFACE",
    "CORE-CONFORMANCE", "CLAIM-SURFACE", "CORE-DISTRIBUTION",
    "CORE-RELEASE-SEAL", "CORE-BASE-DEMO", "TEST",
}


def _scopes(value):
    if isinstance(value, str):
        return {part.strip() for part in value.split(",") if part.strip()}
    if isinstance(value, list):
        return {str(part).strip() for part in value if str(part).strip()}
    return set()


def _load_gates():
    try:
        registry = json.loads((ROOT / ".specify/gates.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"registro de gates ilegible: {exc}") from exc
    if registry.get("schema") != "edaios.sdd.gates/v1":
        raise ValueError("schema de gates no soportado")
    gates = registry.get("gates")
    if not isinstance(gates, list) or not gates:
        raise ValueError("gates debe ser una lista no vacia")
    ids = set()
    for gate in gates:
        if not isinstance(gate, dict) or not gate.get("id") or not gate.get("command"):
            raise ValueError("gate sin id o command")
        gate_id = str(gate["id"])
        if gate_id in ids:
            raise ValueError(f"gate duplicado: {gate_id}")
        ids.add(gate_id)
        if not _scopes(gate.get("scope")):
            raise ValueError(f"{gate_id}: scope vacio")
    missing = sorted(REQUIRED_SCOPES - ids)
    if missing:
        raise ValueError(f"gates obligatorios ausentes: {missing}")
    for gate in gates:
        if str(gate["id"]) in REQUIRED_SCOPES and not {"pre-push", "ci"}.issubset(_scopes(gate.get("scope"))):
            raise ValueError(f"{gate['id']}: scope pre-push,ci obligatorio")
    return gates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True)
    args = parser.parse_args()
    try:
        gates = _load_gates()
    except ValueError as exc:
        print(f"[gates] FAIL: {exc}")
        return 1
    selected = [gate for gate in gates if args.scope in _scopes(gate.get("scope"))]
    if not selected:
        print(f"[gates] FAIL: sin gates para scope {args.scope}")
        return 1

    for gate in selected:
        gate_id = str(gate["id"])
        command = shlex.split(str(gate["command"]))
        if not command:
            print(f"[gates] FAIL: {gate_id} sin comando")
            return 1
        print(f"== {gate_id} ==", flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            print(f"[gates] FAIL: {gate_id} exit={result.returncode}")
            return result.returncode
    print(f"EDAIOS Gates — OK ({len(selected)} gates scope {args.scope})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
