#!/usr/bin/env python3
"""Comprueba catálogos, referencias, features y lock sin conteos congelados."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ADR_ROW = re.compile(
    r"^\|\s*(ADR-[0-9]{4})\s*\|\s*([^|]+?)\s*\|\s*"
    r"(Propuesto|Aceptado|Derogado)\s*\|\s*([^|]+?)\s*\|\s*"
    r"([0-9]{4}-[0-9]{2}-[0-9]{2})\s*\|\s*`([^`]+)`\s*\|$",
    re.MULTILINE,
)
RFC_ROW = re.compile(
    r"^\|\s*(RFC-[0-9]{4})\s*\|\s*([^|]+?)\s*\|\s*"
    r"(Borrador|Propuesto|Ratificado|Rechazado|Derogado)\s*\|\s*"
    r"([^|]+?)\s*\|\s*([^|]+?)\s*\|$",
    re.MULTILINE,
)
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".sh"}
NUMERIC_REF = re.compile(r"\b(ADR|RFC)-([0-9]+)\b")
MALFORMED_RFC = re.compile(r"\bRFC-[0-9]{3}(?![0-9])")


def load_profiles(root: Path, selected: str) -> set[str]:
    path = root / "core/framework/core/profiles/validation-profiles.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "edaios.validation-profile-registry/v1":
        raise ValueError("schema de perfiles no soportado")
    registry_rows = data.get("profiles")
    if not isinstance(registry_rows, list) or not all(isinstance(row, dict) for row in registry_rows):
        raise ValueError("profiles inválidos")
    profile_root = (root / "core/framework/core/profiles").resolve()
    by_id: dict[str, dict[str, object]] = {}
    for registry_row in registry_rows:
        profile_id = str(registry_row.get("id", ""))
        profile_path = (root / str(registry_row.get("path", ""))).resolve()
        try:
            profile_path.relative_to(profile_root)
        except ValueError as exc:
            raise ValueError(f"{profile_id}: path fuera de profiles") from exc
        row = json.loads(profile_path.read_text(encoding="utf-8"))
        if row.get("schema") != "edaios.conformance-profile/v1" or row.get("id") != profile_id:
            raise ValueError(f"{profile_id}: contrato inválido")
        if row.get("remove_controls"):
            raise ValueError(f"{profile_id}: remove_controls prohibido")
        own = row.get("controls")
        if not isinstance(own, list) or not own or len(own) != len(set(own)):
            raise ValueError(f"{profile_id}: controls inválidos")
        by_id[profile_id] = row
    if set(by_id) != {"core-release", "initiative-adoption", "federation"}:
        raise ValueError("registry debe declarar los tres perfiles canónicos")
    if len(by_id) != len(registry_rows):
        raise ValueError("ids de profile duplicados")
    if (
        by_id["core-release"].get("parent") is not None
        or by_id["initiative-adoption"].get("parent") != "core-release"
        or by_id["federation"].get("parent") != "initiative-adoption"
    ):
        raise ValueError("cadena de profiles no es acumulativa")
    active: set[str] = set()
    memo: dict[str, set[str]] = {}

    def resolve(profile_id: str) -> set[str]:
        if profile_id in memo:
            return memo[profile_id]
        if profile_id in active or profile_id not in by_id:
            raise ValueError(f"herencia de profile inválida: {profile_id}")
        active.add(profile_id)
        row = by_id[profile_id]
        own = {str(item) for item in row.get("controls", [])}
        parent = row.get("parent")
        if parent is not None:
            if not isinstance(parent, str):
                raise ValueError(f"{profile_id}: parent inválido")
            inherited = resolve(parent)
            own.update(inherited)
        active.remove(profile_id)
        memo[profile_id] = own
        return own

    return resolve(selected)


def field(text: str, name: str) -> str:
    match = re.search(rf"^\*\*{re.escape(name)}:\*\*\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate_governance(root: Path, errors: list[str]) -> tuple[set[str], set[str]]:
    governance = root / "governance"
    adr_catalog = (governance / "ADR_CATALOG.md").read_text(encoding="utf-8")
    adr_rows = ADR_ROW.findall(adr_catalog)
    adr_ids = [row[0] for row in adr_rows]
    if adr_ids != sorted(adr_ids) or len(adr_ids) != len(set(adr_ids)):
        errors.append(f"catálogo ADR desordenado o duplicado: {adr_ids}")
    state_counts = {
        state: sum(1 for row in adr_rows if row[2] == state)
        for state in ("Aceptado", "Propuesto", "Derogado")
    }
    expected = (
        f"**Total:** {len(adr_rows)} · **Aceptados:** {state_counts['Aceptado']} · "
        f"**Propuestos:** {state_counts['Propuesto']} · **Derogados:** {state_counts['Derogado']}"
    )
    if expected not in adr_catalog:
        errors.append("resumen del catálogo ADR deriva de sus filas")
    for adr_id, _title, state, owner, date, rel in adr_rows:
        path = (root / rel).resolve()
        try:
            path.relative_to(governance.resolve())
        except ValueError:
            errors.append(f"{adr_id}: path fuera de governance")
            continue
        if not path.is_file() or path.name[:8] != adr_id:
            errors.append(f"{adr_id}: archivo único no resoluble")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith(f"# {adr_id} —"):
            errors.append(f"{adr_id}: heading no canónico")
        if field(text, "Estado") != state or field(text, "Owner") != owner or field(text, "Fecha") != date:
            errors.append(f"{adr_id}: catálogo y documento divergen")

    disk_adrs = {path.name[:8] for path in governance.rglob("ADR-[0-9][0-9][0-9][0-9]-*.md")}
    if disk_adrs != set(adr_ids):
        errors.append(f"catálogo ADR no cubre archivos: catálogo={adr_ids}, disco={sorted(disk_adrs)}")

    # Relaciones ADR son tipadas, resolubles y acíclicas. La fuente es el ADR;
    # el catálogo continúa siendo una proyección compilada.
    relation_edges: dict[str, list[str]] = {adr_id: [] for adr_id in adr_ids}
    relation_pattern = re.compile(r"^-\s*(Amends|Supersedes):\s*(.+)$", re.MULTILINE)
    for adr_id, _title, _state, _owner, _date, rel in adr_rows:
        text = (root / rel).read_text(encoding="utf-8")
        for relation, targets_text in relation_pattern.findall(text):
            targets = [item.strip() for item in targets_text.split(",") if item.strip()]
            if not targets:
                errors.append(f"{adr_id}: relación {relation} sin targets")
            for target in targets:
                if not re.fullmatch(r"ADR-[0-9]{4}", target) or target not in set(adr_ids):
                    errors.append(f"{adr_id}: target de relación no resoluble {target}")
                else:
                    relation_edges[adr_id].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"ciclo en relaciones ADR: {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for target in relation_edges[node]:
            visit(target)
        visiting.remove(node)
        visited.add(node)
    for node in relation_edges:
        visit(node)

    rfc_catalog = (governance / "RFC_CATALOG.md").read_text(encoding="utf-8")
    rfc_rows = RFC_ROW.findall(rfc_catalog)
    rfc_ids = [row[0] for row in rfc_rows]
    if rfc_ids != sorted(rfc_ids) or len(rfc_ids) != len(set(rfc_ids)):
        errors.append(f"catálogo RFC desordenado o duplicado: {rfc_ids}")
    ratified = sum(1 for row in rfc_rows if row[2] == "Ratificado")
    proposed = sum(1 for row in rfc_rows if row[2] == "Propuesto")
    if f"**Total:** {len(rfc_rows)}" not in rfc_catalog:
        errors.append("resumen RFC no coincide con total de filas")
    if f"**Ratificados:** {ratified}" not in rfc_catalog or f"**Propuestos:** {proposed}" not in rfc_catalog:
        errors.append("resumen RFC no coincide con estados de filas")
    for rfc_id, _question, state, owner, resolution in rfc_rows:
        matches = list(governance.glob(f"{rfc_id}-*.md"))
        if len(matches) != 1:
            errors.append(f"{rfc_id}: archivo único no resoluble")
            continue
        text = matches[0].read_text(encoding="utf-8")
        if not text.startswith(f"# {rfc_id} —"):
            errors.append(f"{rfc_id}: heading no canónico")
        if field(text, "Estado") != state or field(text, "Owner") != owner:
            errors.append(f"{rfc_id}: catálogo y documento divergen")
        decisions = set(re.findall(r"ADR-[0-9]{4}", resolution))
        if state == "Ratificado" and (not decisions or not decisions.issubset(set(adr_ids))):
            errors.append(f"{rfc_id}: resolución no apunta a ADR aceptado")
        for decision in decisions:
            row = next((item for item in adr_rows if item[0] == decision), None)
            if row is None or row[2] != "Aceptado":
                errors.append(f"{rfc_id}: resolved_by no aceptado {decision}")
    disk_rfcs = {path.name[:8] for path in governance.glob("RFC-[0-9][0-9][0-9][0-9]-*.md")}
    if disk_rfcs != set(rfc_ids):
        errors.append(f"catálogo RFC no cubre archivos: catálogo={rfc_ids}, disco={sorted(disk_rfcs)}")
    return set(adr_ids), set(rfc_ids)


def validate_references(root: Path, known: set[str], errors: list[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if MALFORMED_RFC.search(text):
            errors.append(f"RFC de tres dígitos: {path.relative_to(root)}")
        for kind, digits in NUMERIC_REF.findall(text):
            ref = f"{kind}-{digits}"
            if len(digits) != 4:
                errors.append(f"referencia mal formada {ref}: {path.relative_to(root)}")
            elif ref not in known:
                errors.append(f"referencia no resoluble {ref}: {path.relative_to(root)}")


def validate_features(root: Path, errors: list[str]) -> int:
    count = 0
    specs = root / "specs"
    for spec_path in sorted(specs.rglob("spec.md")):
        feature = spec_path.parent
        count += 1
        spec_path = feature / "spec.md"
        tasks_path = feature / "tasks.md"
        if not spec_path.is_file() or not tasks_path.is_file():
            errors.append(f"{feature.name}: spec/tasks no resolubles")
            continue
        spec = spec_path.read_text(encoding="utf-8")
        tasks = tasks_path.read_text(encoding="utf-8")
        requirements = set(re.findall(r"\bFR-[0-9]{3}\b", spec))
        covered = set(re.findall(r"\bFR-[0-9]{3}\b", tasks))
        if not requirements or requirements - covered:
            errors.append(
                f"{feature.name}: FR sin cobertura {sorted(requirements - covered)}"
            )
        unknown = covered - requirements
        if unknown:
            errors.append(f"{feature.name}: tareas refieren FR inexistentes {sorted(unknown)}")
    return count


def validate_program_surface(root: Path, errors: list[str]) -> None:
    """La superficie diaria no puede contradecir el handoff canónico (FR-004, specs/011).

    Contrato determinista: CURRENT_STATE.md cita el directorio literal de la
    última feature cerrada y la VERSION vigente; toda ruta de feature mencionada
    resuelve; y una feature reclamada como cerrada tiene `estado: Cerrado` en su
    spec. La narrativa autorada restante es territorio humano.
    """
    surface_path = root / "program-office/context/CURRENT_STATE.md"
    text = surface_path.read_text(encoding="utf-8")
    handoff = json.loads((root / ".specify/feature.json").read_text(encoding="utf-8"))
    last_closed = handoff.get("last_closed_feature") or {}
    directory = str(last_closed.get("feature_directory", "")).rstrip("/")
    if not directory:
        errors.append("handoff canónico sin last_closed_feature resoluble")
    elif directory not in text:
        errors.append(f"superficie diaria no cita la última feature cerrada del handoff: {directory}")
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if version not in text:
        errors.append(f"superficie diaria no cita la VERSION vigente: {version}")
    for mention in set(re.findall(r"\bspecs/(?:archive/)?[0-9]{3}-[a-z0-9-]+", text)):
        if not (root / mention / "spec.md").is_file():
            errors.append(f"superficie diaria menciona feature no resoluble: {mention}")
    # Reclamo de cierre: el adjetivo "cerrad*" debe seguir al número dentro de
    # la misma cláusula (sin puntuación intermedia); así "feature 009 cerrada;
    # feature 010 propuesta" solo reclama el cierre de 009.
    closure_claim = re.compile(
        r"\bfeatures?\s+([0-9]{3})\b[^.,;:\n]{0,40}?\bcerrad", re.IGNORECASE
    )
    for number in closure_claim.findall(text):
        candidates = sorted(root.glob(f"specs/{number}-*/spec.md")) or sorted(
            root.glob(f"specs/archive/{number}-*/spec.md")
        )
        if len(candidates) != 1:
            errors.append(f"superficie diaria reclama cierre de feature no resoluble: {number}")
            continue
        spec_text = candidates[0].read_text(encoding="utf-8")
        state = re.search(r"^estado:\s*(.+)$", spec_text, re.MULTILINE)
        if state is None or state.group(1).strip() != "Cerrado":
            errors.append(
                f"superficie diaria reclama como cerrada una feature no cerrada: {number}"
            )


def validate_component_graph(root: Path, accepted_adrs: set[str], errors: list[str]) -> str:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        errors.append(f"VERSION no semver: {version!r}")
    lock = json.loads((root / "edaios.lock.json").read_text(encoding="utf-8"))
    repositories = json.loads((root / "repositories.json").read_text(encoding="utf-8"))
    if lock.get("version") != version or repositories.get("version") != version:
        errors.append("VERSION, lock y repositories divergen")
    if lock.get("component_authority") != "ADR-0006":
        errors.append("lock component_authority debe resolver a ADR-0006")
    if lock.get("release_authority") != "ADR-0013":
        errors.append("lock release_authority debe resolver a ADR-0013")
    for field in ("component_authority", "release_authority"):
        if lock.get(field) not in accepted_adrs:
            errors.append(f"lock {field} no resuelve a ADR aceptado")
    components = lock.get("components", [])
    if len(components) != 1 or any(
        components[0].get(key) != value
        for key, value in {
            "id": "edaios-core", "role": "core", "version": version,
            "source_path": "core", "depends_on": [],
        }.items()
    ):
        errors.append("lock debe declarar solo edaios-core sin dependencias")
    modules = repositories.get("modules", [])
    if len(modules) != 1:
        errors.append("repositories debe declarar exactamente un módulo Core")
    elif (
        modules[0].get("id") != "edaios-core"
        or modules[0].get("path") != "core"
        or modules[0].get("required") is not True
        or modules[0].get("version") != version
    ):
        errors.append("módulo Core diverge de VERSION/topología")
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--profile", default="core-release",
        choices=("core-release", "initiative-adoption", "federation"),
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    try:
        load_profiles(root, args.profile)
        adr_ids, rfc_ids = validate_governance(root, errors)
        validate_references(root, adr_ids | rfc_ids, errors)
        features = validate_features(root, errors)
        validate_program_surface(root, errors)
        version = validate_component_graph(root, adr_ids, errors)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f"contrato de trazabilidad ilegible: {exc}")
        features = 0
        version = "?"
        adr_ids, rfc_ids = set(), set()
    for error in errors:
        print(f"[FAIL] {error}")
    if errors:
        return 1
    print(
        f"[traceability] OK: profile={args.profile} · Core {version} · "
        f"{len(adr_ids)} ADR · {len(rfc_ids)} RFC · {features} features"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
