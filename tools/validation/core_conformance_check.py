#!/usr/bin/env python3
"""Validate the installed Core conformance surface without consumer authority."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_SCHEMAS = {
    "approval-receipt",
    "authority-registry",
    "cli-output",
    "core-release-candidate",
    "core-release-state",
    "core-release-verification-report",
    "delegation-grant",
    "evidence-receipt",
    "exception-record",
    "federation-mounts",
    "git-cutover-receipt",
    "git-cutover-target",
    "initiative-manifest",
    "memory-cli-output",
    "memory-conflict-candidate",
    "memory-record",
    "memory-session-event",
    "outcome",
    "policy-profile",
    "sensitivity-profile",
    "agent-setup-receipt",
}
EXPECTED_PROFILES = {"core-release", "initiative-adoption", "federation"}
TEMPLATE_SCHEMAS = {
    "edaios.initiative.json": "initiative-manifest",
    "authority-registry.json": "authority-registry",
    "initiative-policy.json": "policy-profile",
    "sensitivity-t0.json": "sensitivity-profile",
    "federation-mounts.json": "federation-mounts",
}
PUBLIC_POLICIES = {
    "compatibility-policy.json": "compatibility-policy.json",
    "security-policy.json": "security-policy.json",
    "review-policy.json": "review-policy.json",
    "sensitivity-profiles.json": "sensitivity-policy.json",
}


def validate_control_pointers(root, controls) -> None:
    """Un control declarado resuelve a implementacion y prueba existentes.

    Fail-closed (FR-003, specs/012; linaje feature 009 FR-004). Formas
    admitidas: ruta de archivo o directorio del repo, o referencia de modulo
    `pkg.mod:attr` resoluble bajo los source roots empaquetados.
    """
    module_roots = sorted((root / "core/framework/modules").glob("*/src")) + sorted(
        (root / "core/framework/extensions").glob("*/src")
    )

    def _pointer_resolves(target: str) -> bool:
        if ":" in target and "/" not in target:
            module = target.split(":", 1)[0].replace(".", "/")
            return any(
                (base / f"{module}.py").is_file() or (base / module / "__init__.py").is_file()
                for base in module_roots
            )
        candidate = root / target
        return candidate.is_file() or candidate.is_dir()

    for row in controls:
        if not isinstance(row, dict):
            raise ConformanceCheckError("control-registry: fila invalida")
        for pointer in ("implementation", "tests"):
            target = str(row.get(pointer, ""))
            if not target or not _pointer_resolves(target):
                raise ConformanceCheckError(
                    f"control {row.get('id')}: {pointer} no resoluble: {target!r}"
                )


class ConformanceCheckError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConformanceCheckError(f"{path}: JSON no legible: {exc}") from exc
    if not isinstance(value, dict):
        raise ConformanceCheckError(f"{path}: la raiz debe ser objeto")
    return value


def _install_source_roots(root: Path) -> None:
    module_root = root / "core/framework/modules"
    sources = [
        module_root / "ess-core/src",
        module_root / "conformance-core/src",
        module_root / "harness-core/src",
    ]
    for source in reversed(sources):
        if not source.is_dir():
            raise ConformanceCheckError(f"source root ausente: {source}")
        sys.path.insert(0, str(source))


def check(root: Path, profile: str) -> dict[str, Any]:
    _install_source_roots(root)
    from edaios_conformance import (  # pylint: disable=import-outside-toplevel
        ProfileRegistry,
        SchemaRegistry,
        ValidationError,
    )
    from edaios_core_harness import CoreHarness  # pylint: disable=import-outside-toplevel

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if version != "3.1.0":
        raise ConformanceCheckError(f"VERSION inesperada: {version!r}")

    schema_registry = SchemaRegistry()
    names = set(schema_registry.names())
    if names != EXPECTED_SCHEMAS:
        raise ConformanceCheckError(
            f"schemas publicados difieren: expected={sorted(EXPECTED_SCHEMAS)} actual={sorted(names)}"
        )
    examples = root / "core/framework/modules/conformance-core/src/edaios_conformance/resources/examples"
    valid_bundle = _read_json(examples / "t0.valid.json")
    invalid_bundle = _read_json(examples / "t0.invalid.json")
    if set(valid_bundle) != EXPECTED_SCHEMAS or set(invalid_bundle) != EXPECTED_SCHEMAS:
        raise ConformanceCheckError("fixtures T0 no cubren exactamente los schemas publicados")
    for name in sorted(EXPECTED_SCHEMAS):
        schema_registry.validate(name, valid_bundle[name])
        try:
            schema_registry.validate(name, invalid_bundle[name])
        except ValidationError:
            pass
        else:
            raise ConformanceCheckError(f"fixture invalida fue aceptada: {name}")

    profile_registry = ProfileRegistry()
    profile_report = profile_registry.validate_registry()
    if set(profile_report["profiles"]) != EXPECTED_PROFILES:
        raise ConformanceCheckError("registry empaquetado no contiene los perfiles requeridos")
    if profile not in EXPECTED_PROFILES:
        raise ConformanceCheckError(f"perfil no admitido: {profile}")
    resolved = profile_registry.resolve(profile)

    public_root = root / "core/framework/core/profiles"
    public_registry = _read_json(public_root / "validation-profiles.json")
    public_rows = public_registry.get("profiles")
    if not isinstance(public_rows, list):
        raise ConformanceCheckError("validation-profiles.json: profiles debe ser lista")
    public_ids = {row.get("id") for row in public_rows if isinstance(row, dict)}
    if public_ids != EXPECTED_PROFILES or len(public_rows) != len(EXPECTED_PROFILES):
        raise ConformanceCheckError("registry publico no contiene exactamente tres perfiles")
    packaged_profiles = root / "core/framework/modules/conformance-core/src/edaios_conformance/resources/profiles"
    for profile_id in sorted(EXPECTED_PROFILES):
        public = _read_json(public_root / f"{profile_id}.profile.json")
        packaged = _read_json(packaged_profiles / f"{profile_id}.profile.json")
        if public != packaged:
            raise ConformanceCheckError(f"perfil publico/empaquetado deriva: {profile_id}")
    public_controls = _read_json(public_root / "control-registry.json")
    packaged_controls = _read_json(
        root / "core/framework/modules/conformance-core/src/edaios_conformance/resources/control-registry.json"
    )
    if public_controls != packaged_controls:
        raise ConformanceCheckError("control-registry publico/empaquetado deriva")
    if {row.get("id") for row in public_controls.get("controls", [])} != set(profile_report["controls"]):
        raise ConformanceCheckError("control-registry no cubre exactamente los perfiles")
    validate_control_pointers(root, public_controls.get("controls", []))

    template_root = root / "core/framework/core/templates/initiative"
    for filename, schema_name in TEMPLATE_SCHEMAS.items():
        schema_registry.validate_file(schema_name, template_root / filename)

    packaged_policies = root / "core/framework/modules/conformance-core/src/edaios_conformance/resources/policies"
    for public_name, packaged_name in PUBLIC_POLICIES.items():
        if _read_json(public_root / public_name) != _read_json(packaged_policies / packaged_name):
            raise ConformanceCheckError(f"policy publica/empaquetada deriva: {public_name}")

    grammar = _read_json(
        root / "core/framework/modules/conformance-core/src/edaios_conformance/resources/artifact-grammar.json"
    )
    if grammar.get("version") != version or grammar.get("schema") != "edaios.artifact-grammar/v1":
        raise ConformanceCheckError("artifact grammar ausente, incompatible o con version derivada")

    harness = CoreHarness().validate()
    if harness.get("harnesses") != 12 or harness.get("enforced") != 12:
        raise ConformanceCheckError("los doce harnesses no estan enforced")

    return {
        "version": version,
        "profile": profile,
        "profile_chain": resolved["chain"],
        "controls": len(resolved["controls"]),
        "schemas": len(names),
        "templates": len(TEMPLATE_SCHEMAS),
        "harnesses": harness["harnesses"],
        "boundary": "conformidad local; no adopcion, firma, publicacion u outcome",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--profile",
        choices=sorted(EXPECTED_PROFILES),
        default="core-release",
    )
    args = parser.parse_args()
    try:
        report = check(Path(args.root).resolve(), args.profile)
    except (ConformanceCheckError, OSError, ValueError) as exc:
        print(f"CORE CONFORMANCE — FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "CORE CONFORMANCE — OK "
        f"version={report['version']} profile={report['profile']} "
        f"chain={','.join(report['profile_chain'])} controls={report['controls']} "
        f"schemas={report['schemas']} templates={report['templates']} "
        f"harnesses={report['harnesses']}"
    )
    print(f"Boundary: {report['boundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
