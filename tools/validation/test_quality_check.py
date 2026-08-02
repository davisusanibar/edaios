#!/usr/bin/env python3
"""Falla cerrado ante tests sin aserciones o con aserciones tautológicas.

Motivación (RFC-0003, specs/015): los agentes pueden escribir cientos de
pruebas que no demuestran casi nada. Contrato: todo método `test_*` contiene
al menos una aserción real; `assertTrue(<constante verdadera>)` y
`assertEqual(x, x)` con AST idéntico son tautologías y fallan.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

TESTS_DIR = Path("core/framework/tests")
ASSERT_PREFIXES = ("assert", "fail")


def _is_assertion_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr.startswith(ASSERT_PREFIXES)
    )


def _is_constant_truth(call: ast.Call) -> bool:
    if not (isinstance(call.func, ast.Attribute) and call.func.attr in {"assertTrue", "assertFalse"}):
        return False
    if not call.args:
        return False
    argument = call.args[0]
    return isinstance(argument, ast.Constant)


def _is_tautology(call: ast.Call) -> bool:
    if not (
        isinstance(call.func, ast.Attribute)
        and call.func.attr in {"assertEqual", "assertIs", "assertNotEqual", "assertIsNot"}
        and len(call.args) >= 2
    ):
        return False
    left, right = call.args[0], call.args[1]
    return ast.dump(left) == ast.dump(right)


def check_file(path: Path, errors: list[str]) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        checked += 1
        assertions = [child for child in ast.walk(node) if _is_assertion_call(child)]
        if not assertions:
            errors.append(f"{path.name}:{node.lineno} {node.name}: sin aserciones")
            continue
        for call in assertions:
            if _is_constant_truth(call):
                errors.append(
                    f"{path.name}:{call.lineno} {node.name}: aserción constante"
                )
            elif _is_tautology(call):
                errors.append(
                    f"{path.name}:{call.lineno} {node.name}: aserción tautológica (x == x)"
                )
    return checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    tests = sorted((root / TESTS_DIR).glob("test_*.py"))
    if not tests:
        print("[test-quality] FAIL: no hay tests que verificar")
        return 1
    errors: list[str] = []
    checked = 0
    for path in tests:
        checked += check_file(path, errors)
    for error in errors:
        print(f"[FAIL] {error}")
    if errors:
        return 1
    print(f"[test-quality] OK: {checked} tests con aserciones reales en {len(tests)} archivos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
