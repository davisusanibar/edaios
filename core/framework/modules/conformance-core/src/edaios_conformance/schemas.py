"""Versioned contracts and a fail-closed JSON Schema subset validator.

The published schemas are interoperable JSON Schema documents.  The local
validator deliberately implements only the keywords used by those documents;
an unknown assertion keyword is rejected instead of being ignored.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from hashlib import sha256
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping


class SchemaError(ValueError):
    """A schema is unsupported, missing or internally inconsistent."""


class ValidationError(ValueError):
    """A document does not satisfy its declared conformance contract."""

    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__("; ".join(issues))


_ANNOTATIONS = {
    "$schema", "$id", "title", "description", "default", "examples",
    "deprecated", "readOnly", "writeOnly",
}
_ASSERTIONS = {
    "type", "required", "properties", "additionalProperties", "enum",
    "const", "pattern", "minLength", "maxLength", "minimum", "maximum",
    "minItems", "maxItems", "uniqueItems", "items", "format", "allOf",
    "minProperties", "maxProperties",
}
_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return sha256(canonical_json(value)).hexdigest()


def read_json(path: str | Path) -> dict[str, Any]:
    candidate = Path(path)
    try:
        value = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError([f"{candidate}: JSON no legible: {exc}"]) from exc
    if not isinstance(value, dict):
        raise ValidationError([f"{candidate}: la raiz debe ser un objeto"])
    return value


class SchemaRegistry:
    """Load and enforce the schemas distributed with Core."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = (
            Path(root).resolve()
            if root is not None
            else Path(str(files("edaios_conformance").joinpath("resources/schemas")))
        )

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(path.stem for path in self.root.glob("*.json")))

    def load(self, name: str) -> dict[str, Any]:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            raise SchemaError(f"nombre de schema invalido: {name!r}")
        path = self.root / f"{name}.json"
        if not path.is_file():
            raise SchemaError(f"schema no registrado: {name}")
        value = read_json(path)
        self._check_schema(value, f"schema:{name}")
        return value

    def validate(self, name: str, document: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(document, Mapping):
            raise ValidationError(["$: el documento debe ser un objeto"])
        value = dict(document)
        issues: list[str] = []
        self._validate_node(self.load(name), value, "$", issues)
        self._validate_semantics(name, value, issues)
        if issues:
            raise ValidationError(issues)
        return value

    def validate_file(self, name: str, path: str | Path) -> dict[str, Any]:
        return self.validate(name, read_json(path))

    def _check_schema(self, schema: Any, location: str) -> None:
        if not isinstance(schema, dict):
            raise SchemaError(f"{location}: schema debe ser objeto")
        for keyword, value in schema.items():
            if keyword.startswith("x-") or keyword in _ANNOTATIONS:
                continue
            if keyword not in _ASSERTIONS:
                raise SchemaError(f"{location}: keyword no soportado: {keyword}")
            if keyword == "properties":
                if not isinstance(value, dict):
                    raise SchemaError(f"{location}.properties debe ser objeto")
                for child, child_schema in value.items():
                    self._check_schema(child_schema, f"{location}.properties.{child}")
            elif keyword == "items":
                self._check_schema(value, f"{location}.items")
            elif keyword == "allOf":
                if not isinstance(value, list) or not value:
                    raise SchemaError(f"{location}.allOf debe ser lista no vacia")
                for index, child_schema in enumerate(value):
                    self._check_schema(child_schema, f"{location}.allOf[{index}]")

    def _validate_node(
        self, schema: dict[str, Any], value: Any, location: str, issues: list[str]
    ) -> None:
        expected = schema.get("type")
        if expected is not None:
            allowed = [expected] if isinstance(expected, str) else expected
            if not isinstance(allowed, list) or not allowed:
                issues.append(f"{location}: type invalido en schema")
                return
            matches = False
            for type_name in allowed:
                python_type = _TYPES.get(type_name)
                if python_type is None:
                    issues.append(f"{location}: type no soportado: {type_name}")
                    return
                if isinstance(value, python_type):
                    if type_name in {"integer", "number"} and isinstance(value, bool):
                        continue
                    matches = True
                    break
            if not matches:
                issues.append(f"{location}: se esperaba {allowed}, recibido {type(value).__name__}")
                return

        if "enum" in schema and value not in schema["enum"]:
            issues.append(f"{location}: valor fuera de enum {schema['enum']}")
        if "const" in schema and value != schema["const"]:
            issues.append(f"{location}: debe ser {schema['const']!r}")
        for child_schema in schema.get("allOf", []):
            self._validate_node(child_schema, value, location, issues)

        if isinstance(value, dict):
            required = schema.get("required", [])
            if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
                issues.append(f"{location}: required invalido en schema")
                return
            for key in required:
                if key not in value:
                    issues.append(f"{location}.{key}: propiedad obligatoria ausente")
            properties = schema.get("properties", {})
            additional = schema.get("additionalProperties", True)
            if additional not in {True, False}:
                issues.append(f"{location}: additionalProperties debe ser boolean")
            for key, child in value.items():
                if key in properties:
                    self._validate_node(properties[key], child, f"{location}.{key}", issues)
                elif additional is False:
                    issues.append(f"{location}.{key}: propiedad no admitida")
            if len(value) < schema.get("minProperties", 0):
                issues.append(f"{location}: menos propiedades que minProperties")
            if "maxProperties" in schema and len(value) > schema["maxProperties"]:
                issues.append(f"{location}: mas propiedades que maxProperties")

        if isinstance(value, list):
            if len(value) < schema.get("minItems", 0):
                issues.append(f"{location}: menos elementos que minItems")
            if "maxItems" in schema and len(value) > schema["maxItems"]:
                issues.append(f"{location}: mas elementos que maxItems")
            if schema.get("uniqueItems"):
                fingerprints = [canonical_json(item) for item in value]
                if len(fingerprints) != len(set(fingerprints)):
                    issues.append(f"{location}: elementos duplicados")
            item_schema = schema.get("items")
            if item_schema:
                for index, item in enumerate(value):
                    self._validate_node(item_schema, item, f"{location}[{index}]", issues)

        if isinstance(value, str):
            if len(value) < schema.get("minLength", 0):
                issues.append(f"{location}: longitud menor que minLength")
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                issues.append(f"{location}: longitud mayor que maxLength")
            if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
                issues.append(f"{location}: no cumple pattern")
            if schema.get("format") == "date-time":
                try:
                    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        raise ValueError("timezone ausente")
                except ValueError:
                    issues.append(f"{location}: date-time invalido o sin timezone")
            elif schema.get("format") not in {None, "date-time"}:
                issues.append(f"{location}: format no soportado: {schema['format']}")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                issues.append(f"{location}: menor que minimum")
            if "maximum" in schema and value > schema["maximum"]:
                issues.append(f"{location}: mayor que maximum")

    @staticmethod
    def _validate_semantics(name: str, value: dict[str, Any], issues: list[str]) -> None:
        if name == "authority-registry":
            actor_ids = [row["actor_id"] for row in value.get("actors", []) if "actor_id" in row]
            if len(actor_ids) != len(set(actor_ids)):
                issues.append("$.actors: actor_id duplicado")
        elif name == "policy-profile":
            control_ids = [row["id"] for row in value.get("controls", []) if "id" in row]
            if len(control_ids) != len(set(control_ids)):
                issues.append("$.controls: id de control duplicado")
            if value.get("id") == value.get("parent"):
                issues.append("$.parent: un policy profile no puede heredarse a si mismo")
        elif name == "delegation-grant":
            start = value.get("valid_from")
            end = value.get("valid_until")
            if start and end:
                try:
                    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    if end_dt <= start_dt:
                        issues.append("$.valid_until: debe ser posterior a valid_from")
                except (AttributeError, ValueError):
                    # The structural format issue was already reported above.
                    pass
            if value.get("grantor_actor_id") == value.get("grantee_actor_id"):
                issues.append("$.grantee_actor_id: self-delegation no admitida")
        elif name == "approval-receipt":
            if value.get("actor", {}).get("type") != "human":
                issues.append("$.actor.type: solo una persona puede aprobar")
        elif name == "evidence-receipt":
            approval = value.get("approval", {})
            if approval.get("required") and not approval.get("roles"):
                issues.append("$.approval.roles: obligatorio cuando approval es requerido")
            paths = [row["path"] for row in value.get("evidence", []) if "path" in row]
            if len(paths) != len(set(paths)):
                issues.append("$.evidence: path duplicado")
        elif name == "exception-record":
            if value.get("status") == "approved" and not value.get("approver_actor_id"):
                issues.append("$.approver_actor_id: obligatorio para excepcion aprobada")
            if str(value.get("control", "")).startswith("foundation"):
                issues.append("$.control: Foundation no es exceptuable")
        elif name == "outcome":
            if value.get("status") == "verified" and not value.get("evidence"):
                issues.append("$.evidence: outcome verificado requiere evidencia")
        elif name in {"cli-output", "memory-cli-output"}:
            status = value.get("status")
            if status == "ok":
                if "result" not in value:
                    issues.append("$.result: obligatorio cuando status=ok")
                if "error" in value:
                    issues.append("$.error: prohibido cuando status=ok")
            elif status == "blocked":
                if "error" not in value:
                    issues.append("$.error: obligatorio cuando status=blocked")
                if "result" in value:
                    issues.append("$.result: prohibido cuando status=blocked")
        elif name == "federation-mounts":
            mounts = value.get("mounts", [])
            for field in ("namespace", "path", "attachment"):
                values = [row.get(field) for row in mounts if isinstance(row, dict)]
                if len(values) != len(set(values)):
                    issues.append(f"$.mounts: {field} duplicado")
        elif name == "core-release-candidate":
            kinds = [
                row.get("kind")
                for row in value.get("artifacts", {}).get("items", [])
                if isinstance(row, dict)
            ]
            if len(kinds) != len(set(kinds)):
                issues.append("$.artifacts.items: kind duplicado")
        elif name == "core-release-state":
            status = value.get("status")
            candidate = value.get("active_candidate")
            publication = value.get("publication")
            if status == "baseline" and candidate is not None:
                issues.append("$.active_candidate: baseline no admite candidato activo")
            if status == "candidate" and not isinstance(candidate, dict):
                issues.append("$.active_candidate: candidate exige contratos explícitos")
            if status == "sealed" and publication != "sealed":
                issues.append("$.publication: estado sealed exige publicación sealed")
        elif name == "git-cutover-receipt":
            checks = [
                row.get("id")
                for row in value.get("required_checks", [])
                if isinstance(row, dict)
            ]
            evidence = [
                row.get("kind")
                for row in value.get("provider_evidence", [])
                if isinstance(row, dict)
            ]
            subjects = [
                row.get("kind")
                for row in value.get("attestation_publication", {}).get(
                    "subjects", []
                )
                if isinstance(row, dict)
            ]
            if len(checks) != len(set(checks)):
                issues.append("$.required_checks: id duplicado")
            if len(evidence) != len(set(evidence)):
                issues.append("$.provider_evidence: kind duplicado")
            if set(subjects) != {"approval-receipt", "evidence-receipt"}:
                issues.append(
                    "$.attestation_publication.subjects: debe publicar ambos receipts locales"
                )


__all__ = [
    "SchemaError", "SchemaRegistry", "ValidationError", "canonical_digest",
    "canonical_json", "read_json",
]
