#!/usr/bin/env python3
"""Compila la Constitución operativa desde fuentes Foundation verificadas."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / ".specify/memory/constitution.src.json"
OUTPUT = ROOT / ".specify/memory/constitution.md"


def render() -> str:
    recipe = json.loads(SOURCE.read_text(encoding="utf-8"))
    digest = hashlib.sha256()
    lines = ["# Constitución operativa EDAIOS", "", recipe["preamble"], ""]
    for article in recipe["articles"]:
        path = ROOT / article["source"]
        body = path.read_text(encoding="utf-8")
        if article["contains"].casefold() not in body.casefold():
            raise ValueError(f"{article['id']}: deriva en {article['source']}")
        digest.update(article["source"].encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
        lines += [
            f"## {article['id']}. {article['title']}",
            "",
            article["rule"],
            "",
            f"Fuente: `{article['source']}`.",
            "",
        ]
    lines += ["## Restricciones", ""]
    lines += [f"- {item}" for item in recipe["restrictions"]]
    lines += [
        "",
        f"**Versión:** {recipe['version']} · **Estado:** {recipe['state']} · "
        f"**Autoridad:** {recipe['authority']} · "
        f"**Huella:** `sha256:{digest.hexdigest()}` · derivado, no editar.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    try:
        expected = render()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[constitution] FAIL: {exc}")
        return 1
    if "--check" in sys.argv:
        actual = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if actual != expected:
            print("[constitution] FAIL: proyección desactualizada")
            return 1
        print("[constitution] OK")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8")
    print("[constitution] OK: proyección regenerada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
