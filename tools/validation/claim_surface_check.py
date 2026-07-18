#!/usr/bin/env python3
"""Valida que cada claim Core resuelva a artefactos, pruebas y límites."""

from __future__ import annotations

import json
import io
import re
import sys
import unittest
from pathlib import Path


ALLOWED_MATURITY = {
    "absent", "illustrative", "contracted", "enforced",
    "configuration-tested", "runtime-tested", "operational",
}
ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SOURCE_ROOTS = (
    "core/framework/modules/ess-core/src",
    "core/framework/modules/harness-core/src",
    "core/framework/modules/ekg-core/src",
    "core/framework/modules/query-engine/src",
    "core/framework/modules/sdk-consumption/src",
    "core/framework/modules/conformance-core/src",
    "core/framework/modules/supply-chain-core/src",
    "core/framework/extensions/sdd-adapter/src",
    "core/framework/extensions/memory-adapter/src",
)


def inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _flatten(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def _discover(root: Path) -> tuple[dict[str, unittest.TestCase], list[str]]:
    errors: list[str] = []
    for relative in reversed(SOURCE_ROOTS):
        source = root / relative
        if source.is_dir():
            sys.path.insert(0, str(source))
    tests_root = root / "core/framework/tests"
    if not tests_root.is_dir():
        return {}, ["directorio de tests ausente"]
    try:
        suite = unittest.defaultTestLoader.discover(str(tests_root))
    except (ImportError, OSError) as exc:
        return {}, [f"unittest discovery falló: {exc}"]
    by_marker: dict[str, unittest.TestCase] = {}
    for case in _flatten(suite):
        marker = case.id().rsplit(".", 1)[-1]
        if marker in by_marker:
            errors.append(f"test marker ambiguo: {marker}")
        else:
            by_marker[marker] = case
    return by_marker, errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "core/framework/core/profiles/claim-surface.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"claim surface ilegible: {exc}"]
    if data.get("schema") != "edaios.claim-surface/v1":
        errors.append("schema de claim surface no soportado")
    if data.get("version") != (root / "VERSION").read_text(encoding="utf-8").strip():
        errors.append("claim surface no coincide con VERSION")
    rows = data.get("claims")
    if not isinstance(rows, list) or not rows:
        return errors + ["claims debe ser una lista no vacía"]
    discovered, discovery_errors = _discover(root)
    errors.extend(discovery_errors)
    seen: set[str] = set()
    for index, row in enumerate(rows):
        label = f"claims[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label}: debe ser objeto")
            continue
        claim_id = row.get("id")
        if not isinstance(claim_id, str) or not ID.fullmatch(claim_id):
            errors.append(f"{label}: id inválido")
        elif claim_id in seen:
            errors.append(f"{label}: id duplicado {claim_id}")
        else:
            seen.add(claim_id)
        maturity = row.get("maturity")
        if maturity not in ALLOWED_MATURITY:
            errors.append(f"{claim_id}: maturity inválida {maturity!r}")
        for field in ("claim", "boundary"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{claim_id}: {field} obligatorio")
        artifacts = row.get("artifacts")
        tests = row.get("tests")
        test_markers = row.get("test_markers")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"{claim_id}: artifacts obligatorio")
            artifacts = []
        if not isinstance(tests, list):
            errors.append(f"{claim_id}: tests debe ser lista")
            tests = []
        if maturity == "enforced" and not tests:
            errors.append(f"{claim_id}: enforced exige pruebas")
        if maturity == "enforced" and (
            not isinstance(test_markers, list)
            or not test_markers
            or any(not isinstance(marker, str) or not marker for marker in test_markers)
        ):
            errors.append(f"{claim_id}: enforced exige test_markers explícitos")
            test_markers = []
        elif not isinstance(test_markers, list):
            test_markers = []
        for kind, paths in (("artifact", artifacts), ("test", tests)):
            for value in paths:
                candidate = root / str(value)
                if not inside(root, candidate) or not candidate.is_file():
                    errors.append(f"{claim_id}: {kind} no resoluble {value}")
        for marker in test_markers:
            case = discovered.get(marker)
            if case is None:
                errors.append(f"{claim_id}: test marker no descubierto {marker}")
                continue
            source_names = {Path(str(value)).stem for value in tests}
            if case.id().split(".", 1)[0] not in source_names:
                errors.append(
                    f"{claim_id}: marker {marker} no pertenece a tests declarados"
                )
    references = data.get("documentation_references")
    if not isinstance(references, list) or not references:
        errors.append("documentation_references debe ser lista no vacía")
    else:
        for index, row in enumerate(references):
            if not isinstance(row, dict):
                errors.append(f"documentation_references[{index}] inválida")
                continue
            source = root / str(row.get("source", ""))
            target = root / str(row.get("target", ""))
            if not inside(root, source) or not source.is_file():
                errors.append(f"referencia documental sin source: {row.get('source')}")
            if not inside(root, target) or not target.is_file():
                errors.append(f"referencia documental sin target: {row.get('target')}")
            elif source.is_file():
                target_name = target.name
                if target_name not in source.read_text(encoding="utf-8"):
                    errors.append(
                        f"{row.get('source')}: no menciona target {target_name}"
                    )
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    for error in errors:
        print(f"[FAIL] {error}")
    if errors:
        return 1
    discovered, discovery_errors = _discover(root)
    if discovery_errors:
        for error in discovery_errors:
            print(f"[FAIL] {error}")
        return 1
    data = json.loads(
        (root / "core/framework/core/profiles/claim-surface.json").read_text(
            encoding="utf-8"
        )
    )
    required_markers = sorted(
        {
            marker
            for row in data["claims"]
            if row.get("maturity") == "enforced"
            for marker in row.get("test_markers", [])
        }
    )
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(
        unittest.TestSuite(discovered[marker] for marker in required_markers)
    )
    if not result.wasSuccessful() or result.testsRun != len(required_markers):
        print("[FAIL] tests exigidos por claim surface no pasaron")
        print(stream.getvalue())
        return 1
    enforced = sum(row["maturity"] == "enforced" for row in data["claims"])
    absent = sum(row["maturity"] == "absent" for row in data["claims"])
    print(
        f"[claim-surface] OK: {len(data['claims'])} claims · "
        f"{enforced} enforced · {absent} absent · "
        f"{result.testsRun} tests ejecutados"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
