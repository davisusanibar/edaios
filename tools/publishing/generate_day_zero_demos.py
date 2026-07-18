#!/usr/bin/env python3
"""Genera la guía offline del baseline portable de EDAIOS Core.

El JSON conserva la narrativa. Arquitectura de información, catálogo ADR y
evidencia se leen de sus fuentes Markdown y se contrastan antes de renderizar.
El HTML es derivado determinista; no se edita a mano.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


OS_CONFIG = Path("docs/demos/edaios-operating-system.config.json")
OS_OUTPUT = Path("docs/demos/edaios-operating-system.html")
INFORMATION_ARCHITECTURE = Path("docs/information-architecture.md")
ADR_CATALOG = Path("governance/ADR_CATALOG.md")
RFC_CATALOG = Path("governance/RFC_CATALOG.md")
VERSION_FILE = Path("VERSION")
FEATURE_HANDOFF = Path(".specify/feature.json")
GATE_REGISTRY = Path(".specify/gates.json")
RELEASE_STATE = Path(".specify/release.json")
EXPECTED_NAV = (
    "quick-start", "cycle", "governance", "spec-kit", "architecture", "evidence", "glossary"
)
EXPECTED_STAGE_IDS = (
    "intention", "specification", "decision", "construction", "verdict", "publication", "value"
)


class DemoContractError(ValueError):
    """La fuente no satisface el contrato de la guía."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DemoContractError(message)


def text(value: Any, label: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{label} debe ser texto no vacío")
    return value.strip()


def mapping(value: Any, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} debe ser un objeto")
    return value


def sequence(value: Any, label: str, minimum: int = 1) -> list[Any]:
    require(isinstance(value, list) and len(value) >= minimum,
            f"{label} debe contener al menos {minimum} elemento(s)")
    return value


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise DemoContractError(f"fuente inexistente: {path}") from exc


def load_json(path: Path) -> dict[str, Any]:
    try:
        return mapping(json.loads(load_text(path)), str(path))
    except json.JSONDecodeError as exc:
        raise DemoContractError(f"JSON inválido en {path}: {exc}") from exc


def cells(line: str) -> list[str]:
    return [cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")]


def markdown_table(source: str, headers: tuple[str, ...], label: str) -> list[dict[str, str]]:
    lines = source.splitlines()
    index = next((i for i, line in enumerate(lines) if tuple(cells(line)) == headers), None)
    require(index is not None, f"{label}: headers no encontrados")
    require(index + 1 < len(lines), f"{label}: falta separador")
    separator = cells(lines[index + 1])
    require(len(separator) == len(headers) and
            all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator),
            f"{label}: separador inválido")
    rows: list[dict[str, str]] = []
    for line in lines[index + 2:]:
        if not line.lstrip().startswith("|"):
            break
        row = cells(line)
        require(len(row) == len(headers), f"{label}: fila inválida")
        rows.append(dict(zip(headers, row)))
    require(rows, f"{label}: tabla vacía")
    return rows


def catalog_counts(source: str) -> dict[str, int]:
    match = re.search(
        r"\*\*Total:\*\*\s*(\d+)\s*·\s*\*\*Aceptados:\*\*\s*(\d+)\s*·\s*"
        r"\*\*Propuestos:\*\*\s*(\d+)\s*·\s*\*\*Derogados:\*\*\s*(\d+)", source
    )
    require(match is not None, "ADR Catalog: resumen ausente")
    return dict(zip(("total", "accepted", "proposed", "deprecated"), map(int, match.groups())))


def rfc_counts(source: str) -> dict[str, int]:
    match = re.search(
        r"\*\*Total:\*\*\s*(\d+)\s*·\s*\*\*Ratificados:\*\*\s*(\d+)\s*·\s*"
        r"\*\*Propuestos:\*\*\s*(\d+)", source
    )
    require(match is not None, "RFC Catalog: resumen ausente")
    return dict(zip(("total", "ratified", "proposed"), map(int, match.groups())))


def frontmatter(source: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", source)
    require(match is not None, f"spec: falta {key}")
    return match.group(1).strip().strip('"')


def canonical_views(root: Path, data: dict[str, Any]) -> dict[str, Any]:
    ia_source = load_text(root / INFORMATION_ARCHITECTURE)
    adr_source = load_text(root / ADR_CATALOG)
    rfc_source = load_text(root / RFC_CATALOG)
    version = load_text(root / VERSION_FILE).strip()
    release_state = load_json(root / RELEASE_STATE)
    require(release_state.get("schema") == "edaios.core-release-state/v2",
            "release state: se requiere edaios.core-release-state/v2")
    require(release_state.get("component") == "edaios-core",
            "release state: componente distinto de edaios-core")
    require(release_state.get("version") == version,
            "release state: versión distinta de VERSION")
    require(release_state.get("status") == "baseline",
            "release state: el estado debe permanecer baseline")
    require(release_state.get("active_candidate") is None,
            "release state: el baseline portable no puede inferir candidato")
    require(release_state.get("publication") == "not-claimed",
            "release state: la publicación debe permanecer not-claimed")
    require(release_state.get("governing_adr") == "ADR-0013",
            "release state: ADR-0013 debe gobernar la genealogía portable")
    release_genealogy = mapping(release_state.get("genealogy"),
                                "release state.genealogy")
    require(release_genealogy == {
        "kind": "single-root",
        "root_derivation": "unique-reachable-root",
        "canonical_branch": "main",
    }, "release state: contrato portable de raíz única inválido")

    handoff = load_json(root / FEATURE_HANDOFF)
    require(handoff.get("schema") in {"edaios.feature-handoff/v2", "edaios.feature-handoff/v3"},
            "handoff: schema no soportado")
    lineage: dict[str, dict[str, str]] = {}
    idle = handoff.get("schema") == "edaios.feature-handoff/v3" and handoff.get("active_feature") is None
    for key in ("baseline_feature", "last_closed_feature", "active_feature"):
        pointer = mapping(handoff.get(key) or handoff.get("last_closed_feature"), f"handoff.{key}")
        lineage[key] = {
            "id": text(pointer.get("id"), f"handoff.{key}.id"),
            "path": text(pointer.get("feature_directory"),
                         f"handoff.{key}.feature_directory").rstrip("/"),
        }

    installed = mapping(data.get("baseline", {}).get("installed"), "baseline.installed")
    feature = mapping(installed.get("feature"), "baseline.installed.feature")
    active = lineage["active_feature"]
    require(feature.get("id") == active["id"],
            "baseline.installed.feature.id debe derivar de active_feature")
    require(str(feature.get("path", "")).rstrip("/") == active["path"],
            "baseline.installed.feature.path debe derivar de active_feature")
    configured_lineage = mapping(installed.get("lineage"), "baseline.installed.lineage")
    for key, pointer in lineage.items():
        configured = mapping(configured_lineage.get(key), f"baseline.installed.lineage.{key}")
        require(configured.get("id") == pointer["id"] and
                str(configured.get("path", "")).rstrip("/") == pointer["path"],
                f"baseline.installed.lineage.{key} no coincide con el handoff")

    feature_root = root / active["path"]
    evidence_config = mapping(installed.get("evidence"), "baseline.installed.evidence")
    evidence_path = Path(text(evidence_config.get("path"), "baseline.installed.evidence.path"))
    require(not evidence_path.is_absolute() and ".." not in evidence_path.parts,
            "baseline.installed.evidence.path debe ser relativo y seguro")
    evidence_source = load_text(root / evidence_path)

    ia_rows = markdown_table(ia_source, ("Orden", "Pregunta", "Fuente"), "Arquitectura")
    adr_rows = markdown_table(
        adr_source, ("ID", "Título", "Estado", "Owner", "Fecha", "Path"), "ADR Catalog"
    )
    adr = catalog_counts(adr_source)
    observed = {
        "total": len(adr_rows),
        "accepted": sum(row["Estado"] == "Aceptado" for row in adr_rows),
        "proposed": sum(row["Estado"] == "Propuesto" for row in adr_rows),
        "deprecated": sum(row["Estado"] == "Derogado" for row in adr_rows),
    }
    require(adr == observed, f"ADR Catalog: resumen y filas difieren: {adr} != {observed}")
    require(adr["total"] >= 1 and adr["accepted"] == adr["total"] and
            adr["proposed"] == 0,
            f"el release requiere ADR vigentes sin propuestas abiertas: {adr}")
    # La demo muestra la superficie Core vigente; el catálogo completo sigue
    # conservando y validando los ADR archivados.
    visible_ids = {"ADR-0001", "ADR-0003", "ADR-0004", "ADR-0005", "ADR-0006", "ADR-0011", "ADR-0013", "ADR-0014", "ADR-0015"}
    adr_rows = [row for row in adr_rows if row["ID"] in visible_ids]
    adr = {
        "total": len(adr_rows),
        "accepted": sum(row["Estado"] == "Aceptado" for row in adr_rows),
        "proposed": sum(row["Estado"] == "Propuesto" for row in adr_rows),
        "deprecated": sum(row["Estado"] == "Derogado" for row in adr_rows),
    }
    governing_adr = next(
        (row for row in adr_rows if row["ID"] == release_state["governing_adr"]),
        None,
    )
    require(governing_adr is not None and governing_adr["Estado"] == "Aceptado",
            "release state: governing_adr no resuelve a un ADR aceptado")
    decision = mapping(installed.get("decision"), "baseline.installed.decision")
    require(decision.get("id") == release_state["governing_adr"] and
            decision.get("status") == governing_adr["Estado"],
            "baseline.installed.decision no deriva de release.json y ADR Catalog")
    require(decision.get("title") == governing_adr["Título"],
            "baseline.installed.decision.title no deriva de ADR Catalog")
    rfc = rfc_counts(rfc_source)
    require(rfc["ratified"] == rfc["total"] and rfc["proposed"] == 0,
            f"el release requiere RFC resueltos: {rfc}")

    evidence_headers = tuple(
        text(value, "baseline.installed.evidence.headers[]")
        for value in sequence(
            evidence_config.get("headers"), "baseline.installed.evidence.headers", 2
        )
    )
    require(len(evidence_headers) == len(set(evidence_headers)),
            "baseline.installed.evidence.headers contiene duplicados")
    evidence_rows = markdown_table(evidence_source, evidence_headers, "Evidencia")

    spec_source = load_text(feature_root / "spec.md")
    tasks_source = load_text(feature_root / "tasks.md")
    marks = re.findall(r"(?m)^- \[([ xX])\] \[(T\d{3})\]", tasks_source)
    require(marks, "feature: tareas ausentes")
    feature_observed = {
        "id": active["id"],
        "path": active["path"] + "/",
        "status": frontmatter(spec_source, "estado"),
        "phase": frontmatter(spec_source, "fase"),
        "tasks_total": len(marks),
        "tasks_complete": sum(mark.lower() == "x" for mark, _ in marks),
        "pending_ids": [task_id for mark, task_id in marks if mark.lower() != "x"],
    }
    feature_observed["tasks_pending"] = (
        feature_observed["tasks_total"] - feature_observed["tasks_complete"]
    )
    phase = feature_observed["phase"]
    status = feature_observed["status"]
    require(
        (phase == "implemented" and status == "Cerrado")
        or (phase in {"specified", "clarified", "planned", "tasked"}
            and status in {"Borrador", "Propuesto"}),
        f"feature activa con estado/fase incompatibles: {status}/{phase}",
    )
    if phase == "implemented":
        require(not feature_observed["pending_ids"],
                "feature implementada no puede conservar tareas pendientes")

    require(version == data["meta"].get("version"),
            f"versión de guía debe derivar de VERSION, observado {version}")
    configured_sources = {item.get("path") for item in data.get("sources", [])}
    required = {
        INFORMATION_ARCHITECTURE.as_posix(), ADR_CATALOG.as_posix(),
        RFC_CATALOG.as_posix(), FEATURE_HANDOFF.as_posix(), RELEASE_STATE.as_posix(),
        evidence_path.as_posix(), governing_adr["Path"],
    }
    require(required <= configured_sources,
            f"faltan fuentes integradas: {sorted(required - configured_sources)}")

    glossary = mapping(data.get("glossary"), "glossary")
    glossary_sources = {
        source
        for entry in glossary.get("terms", [])
        for source in entry.get("sources", [])
    }
    require(glossary_sources, "glossary: fuentes ausentes")
    unresolved_glossary = sorted(
        source for source in glossary_sources if not (root / source).exists()
    )
    require(not unresolved_glossary,
            f"glossary: fuentes no resolubles: {unresolved_glossary}")

    gate_registry = load_json(root / GATE_REGISTRY)
    registered_gates = sequence(gate_registry.get("gates"), "gates.json.gates", 1)
    gate_notes = {
        item["id"]: item
        for item in sequence(data.get("gates", {}).get("items"), "gates.items", 1)
        if item.get("type") == "executable"
    }
    canonical_gates: list[dict[str, str]] = []
    for gate in registered_gates:
        gate_id = text(gate.get("id"), "gates.json.gates[].id")
        note = gate_notes.get(gate_id, {})
        canonical_gates.append({
            "id": gate_id,
            "type": "executable",
            "command": text(gate.get("command"), f"gates.json.{gate_id}.command"),
            "proves": note.get(
                "proves", "Ejecuta el contrato fail-closed registrado para esta puerta."
            ),
            "does_not_prove": note.get(
                "does_not_prove", "No sustituye aceptación humana ni amplía el claim observado."
            ),
        })
    canonical_gates.extend(
        item for item in data["gates"]["items"] if item.get("type") == "human"
    )

    return {
        "version": version,
        "information": ia_rows,
        "adr": {"counts": adr, "rows": adr_rows},
        "rfc": rfc,
        "feature": feature_observed,
        "lineage": lineage,
        "release": {
            "schema": release_state["schema"],
            "status": release_state["status"],
            "publication": release_state["publication"],
            "governing_adr": release_state["governing_adr"],
            "genealogy": release_genealogy,
        },
        "evidence_path": evidence_path.as_posix(),
        "gates": canonical_gates,
        "evidence": {
            "eyebrow": text(evidence_config.get("eyebrow"), "baseline.installed.evidence.eyebrow"),
            "title": text(evidence_config.get("title"), "baseline.installed.evidence.title"),
            "scope": text(evidence_config.get("scope"), "baseline.installed.evidence.scope"),
            "headers": evidence_headers,
            "rows": evidence_rows,
            "boundary": text(
                evidence_config.get("boundary"), "baseline.installed.evidence.boundary"
            ),
        },
    }


def validate(data: dict[str, Any]) -> None:
    require(data.get("schema") == "edaios.operating-system-demo/v4", "schema OS inválido")
    meta = mapping(data.get("meta"), "meta")
    for key in ("id", "title", "eyebrow", "subtitle", "version", "as_of", "scope",
                "status", "status_title", "status_message", "operating_thesis"):
        text(meta.get(key), f"meta.{key}")
    require(meta.get("status") == "BASELINE INSTALADO", "meta.status inválido")
    navigation = sequence(meta.get("navigation"), "meta.navigation", 7)
    require(tuple(item.get("id") for item in navigation) == EXPECTED_NAV,
            "navegación debe conservar siete vistas")

    baseline = mapping(data.get("baseline"), "baseline")
    installed = mapping(baseline.get("installed"), "baseline.installed")
    growth = mapping(baseline.get("growth_rule"), "baseline.growth_rule")
    checkpoint = mapping(baseline.get("checkpoint"), "baseline.checkpoint")
    require(installed.get("genealogy") == "Foundation + Core", "genealogía inválida")
    require(installed.get("version") == "3.1.0",
            "baseline.installed.version debe identificar Core 3.1.0")
    require(installed.get("status") == "INSTALADO", "Core no está INSTALADO")
    require(installed.get("decision", {}).get("id") == "ADR-0013" and
            installed.get("decision", {}).get("status") == "Aceptado",
            "decisión de genealogía portable ausente")
    feature = mapping(installed.get("feature"), "baseline.installed.feature")
    for key in ("id", "path", "meaning"):
        text(feature.get(key), f"baseline.installed.feature.{key}")
    lineage = mapping(installed.get("lineage"), "baseline.installed.lineage")
    for key in ("baseline_feature", "last_closed_feature", "active_feature"):
        pointer = mapping(lineage.get(key), f"baseline.installed.lineage.{key}")
        text(pointer.get("id"), f"baseline.installed.lineage.{key}.id")
        text(pointer.get("path"), f"baseline.installed.lineage.{key}.path")
    evidence = mapping(installed.get("evidence"), "baseline.installed.evidence")
    for key in ("path", "eyebrow", "title", "scope", "boundary"):
        text(evidence.get(key), f"baseline.installed.evidence.{key}")
    headers = sequence(evidence.get("headers"), "baseline.installed.evidence.headers", 2)
    require(all(isinstance(item, str) and item.strip() for item in headers),
            "baseline.installed.evidence.headers inválidos")
    require(growth.get("status") == "SIN INICIATIVA INSTALADA",
            "el crecimiento debe conservar explícita la ausencia de iniciativas")
    sequence(growth.get("steps"), "baseline.growth_rule.steps", 4)
    sequence(checkpoint.get("non_equivalences"), "baseline.checkpoint.non_equivalences", 4)

    cycle = mapping(data.get("operating_cycle"), "operating_cycle")
    for key in ("eyebrow", "title", "subtitle", "thesis", "roundtrip", "boundary"):
        text(cycle.get(key), f"operating_cycle.{key}")
    principles = sequence(cycle.get("principles"), "operating_cycle.principles", 3)
    require(len(principles) == 3, "operating_cycle.principles debe contener 3 elementos")
    stages = sequence(cycle.get("stages"), "operating_cycle.stages", 7)
    require(len(stages) == 7, "operating_cycle.stages debe contener 7 etapas")
    require(all(type(stage.get("order")) is int for stage in stages),
            "operating_cycle.stages[].order debe ser entero")
    require(tuple(stage.get("id") for stage in stages) == EXPECTED_STAGE_IDS,
            "Ciclo 1–7 inválido")
    require(tuple(stage.get("order") for stage in stages) == tuple(range(1, 8)),
            "orden del ciclo inválido")
    for index, stage in enumerate(stages, start=1):
        for key in ("id", "label", "title", "description", "question", "input",
                    "control", "output", "claim_boundary"):
            text(stage.get(key), f"operating_cycle.stages[{index}].{key}")
        evidence = sequence(
            stage.get("evidence"), f"operating_cycle.stages[{index}].evidence", 1
        )
        require(all(isinstance(item, str) and item.strip() for item in evidence),
                f"operating_cycle.stages[{index}].evidence inválida")

    scenes = sequence(cycle.get("scenes"), "operating_cycle.scenes", 8)
    require(len(scenes) == 8, "operating_cycle.scenes debe contener 8 escenas")
    require(all(type(scene.get("order")) is int for scene in scenes),
            "operating_cycle.scenes[].order debe ser entero")
    require(all(type(scene.get("stage")) is int for scene in scenes),
            "operating_cycle.scenes[].stage debe ser entero")
    require(tuple(scene.get("order") for scene in scenes) == tuple(range(1, 9)),
            "orden de escenas inválido")
    stage_scene_map = sequence(
        cycle.get("stage_scene_map"), "operating_cycle.stage_scene_map", 8
    )
    require(len(stage_scene_map) == len(scenes),
            "stage_scene_map debe declarar una etapa por escena")
    require(all(type(stage) is int for stage in stage_scene_map),
            "stage_scene_map debe contener enteros")
    require(all(stage in range(1, 8) for stage in stage_scene_map),
            "stage_scene_map contiene una etapa fuera de rango")
    require(set(stage_scene_map) == set(range(1, 8)),
            "stage_scene_map debe cubrir las 7 etapas")
    require(tuple(stage_scene_map) == tuple(scene.get("stage") for scene in scenes),
            "stage_scene_map y scenes[].stage difieren")
    for index, scene in enumerate(scenes, start=1):
        for key in ("title", "detail", "focus", "evidence", "governance",
                    "claim_boundary"):
            text(scene.get(key), f"operating_cycle.scenes[{index}].{key}")
        artifacts = sequence(
            scene.get("artifacts"), f"operating_cycle.scenes[{index}].artifacts", 1
        )
        require(all(isinstance(item, str) and item.strip() for item in artifacts),
                f"operating_cycle.scenes[{index}].artifacts inválidos")
        for moment_index, moment in enumerate(scene.get("gate_story", []), start=1):
            moment = mapping(
                moment,
                f"operating_cycle.scenes[{index}].gate_story[{moment_index}]",
            )
            for key in ("label", "status", "detail"):
                text(
                    moment.get(key),
                    f"operating_cycle.scenes[{index}].gate_story[{moment_index}].{key}",
                )
    sequence(data.get("quick_start", {}).get("steps"), "quick_start.steps", 6)
    sequence(data.get("principles", {}).get("items"), "principles.items", 7)
    sequence(data.get("artifact_model", {}).get("artifacts"), "artifact_model.artifacts", 6)
    sequence(data.get("authority_chain", {}).get("nodes"), "authority_chain.nodes", 5)
    sequence(data.get("governance", {}).get("roles"), "governance.roles", 6)
    sequence(data.get("spec_kit", {}).get("phases"), "spec_kit.phases", 8)
    sequence(data.get("gates", {}).get("items"), "gates.items", 10)
    sequence(data.get("architecture", {}).get("zones"), "architecture.zones", 6)
    sequence(data.get("evidence_chain", {}).get("items"), "evidence_chain.items", 8)
    sequence(data.get("claim_boundaries", {}).get("items"), "claim_boundaries.items", 6)
    sequence(data.get("sources"), "sources", 10)

    glossary = mapping(data.get("glossary"), "glossary")
    for key in ("eyebrow", "title", "subtitle", "source_note"):
        text(glossary.get(key), f"glossary.{key}")
    categories = sequence(glossary.get("categories"), "glossary.categories", 6)
    category_ids = [text(item.get("id"), "glossary.categories[].id") for item in categories]
    require(len(category_ids) == len(set(category_ids)), "glossary: categorías duplicadas")
    require(category_ids[0] == "all", "glossary: primera categoría debe ser all")
    require(all(text(item.get("label"), "glossary.categories[].label") for item in categories),
            "glossary: labels de categoría inválidos")

    guide = sequence(glossary.get("identifier_guide"), "glossary.identifier_guide", 7)
    guide_codes = set()
    for index, item in enumerate(guide, start=1):
        item = mapping(item, f"glossary.identifier_guide[{index}]")
        for key in ("code", "reads", "meaning"):
            text(item.get(key), f"glossary.identifier_guide[{index}].{key}")
        guide_codes.add(item["code"])
    required_codes = {
        "ADR-0010", "ADR-0011", "ADR-0013", "FR-001", "SC-001", "T001",
        "ART-008", "T0", "VAL-004",
    }
    require(required_codes <= guide_codes,
            f"glossary: guía de identificadores incompleta: {sorted(required_codes - guide_codes)}")

    glossary_terms = sequence(glossary.get("terms"), "glossary.terms", 25)
    term_ids: list[str] = []
    term_names: list[str] = []
    allowed_statuses = {"vigente", "parcial", "referencial", "convencion"}
    allowed_categories = set(category_ids) - {"all"}
    for index, entry in enumerate(glossary_terms, start=1):
        entry = mapping(entry, f"glossary.terms[{index}]")
        for key in ("id", "term", "expansion", "category", "status", "definition",
                    "usage", "boundary"):
            text(entry.get(key), f"glossary.terms[{index}].{key}")
        term_ids.append(entry["id"])
        term_names.append(entry["term"].casefold())
        require(entry["category"] in allowed_categories,
                f"glossary.terms[{index}]: categoría inválida {entry['category']!r}")
        require(entry["status"] in allowed_statuses,
                f"glossary.terms[{index}]: status inválido {entry['status']!r}")
        term_sources = sequence(entry.get("sources"), f"glossary.terms[{index}].sources", 1)
        require(all(isinstance(source, str) and source.strip() for source in term_sources),
                f"glossary.terms[{index}]: fuentes inválidas")
    require(len(term_ids) == len(set(term_ids)), "glossary: ids duplicados")
    require(len(term_names) == len(set(term_names)), "glossary: términos duplicados")
    required_terms = {
        "adr", "rfc", "t0", "t1-t3", "fr", "sc", "task", "art", "val", "ko", "kom",
        "spec-kit", "gate", "fail-closed", "owner", "evidence", "value-ledger", "pii",
        "working-memory", "derived-index", "conflict-candidate", "memory-adapter",
    }
    require(required_terms <= set(term_ids),
            f"glossary: vocabulario mínimo ausente: {sorted(required_terms - set(term_ids))}")
    val = next(entry for entry in glossary_terms if entry["id"] == "val")
    require(val["status"] == "referencial" and "No existe hoy un catálogo VAL" in val["boundary"],
            "glossary: VAL debe declarar su límite no materializado")
    sensitivity = next(entry for entry in glossary_terms if entry["id"] == "t1-t3")
    require(sensitivity["status"] == "vigente" and "taxonomía operativa de Core" in sensitivity["boundary"],
            "glossary: T1–T3 debe declarar taxonomía operativa y límite jurídico")


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def items(values: Iterable[Any], class_name: str = "") -> str:
    css = f' class="{esc(class_name)}"' if class_name else ""
    return f"<ul{css}>" + "".join(f"<li>{esc(value)}</li>" for value in values) + "</ul>"


def table(headers: Iterable[str], rows: Iterable[Iterable[Any]], class_name: str = "") -> str:
    css = f' class="{esc(class_name)}"' if class_name else ""
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "".join("<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table{css}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


CSS = r"""
:root{--ink:#151922;--muted:#626b7a;--line:#d9dee8;--paper:#fff;--bg:#f5f7fa;--blue:#1477ed;
--blue-soft:#eaf3ff;--green:#08795c;--green-soft:#e8f7f1;--amber:#d18100;--amber-soft:#fff4df;
--red:#ad342f;--red-soft:#fff0ee;--navy:#202733;--violet:#7258c7;--shadow:0 14px 34px rgba(30,42,65,.08)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.48}button{font:inherit}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #ffb400;outline-offset:3px}
.shell{width:min(1500px,calc(100% - 40px));margin:auto}.topbar{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.96);border-bottom:1px solid var(--line)}.topbar-inner{min-height:78px;display:flex;align-items:center;justify-content:space-between;gap:22px}.brand strong{display:block;color:var(--green);letter-spacing:.08em}.brand small{color:var(--muted)}
.tabs{display:flex;gap:7px;flex-wrap:wrap;background:#e9edf3;border-radius:14px;padding:6px}.tabs a{padding:11px 15px;border-radius:10px;text-decoration:none;font-weight:800}.tabs a[aria-selected=true]{background:var(--blue);color:#fff}.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:10px;z-index:99}
.hero{padding:58px 0 30px}.hero-grid{display:grid;grid-template-columns:1.25fr .75fr;gap:30px;align-items:end}.eyebrow{margin:0;color:var(--green);font-size:.79rem;font-weight:900;letter-spacing:.13em;text-transform:uppercase}h1{font-size:clamp(2.5rem,5vw,5rem);line-height:.98;letter-spacing:-.052em;margin:.2em 0}h2{font-size:clamp(1.55rem,3vw,2.65rem);line-height:1.08;letter-spacing:-.035em;margin:.2em 0 .4em}h3{margin:.2em 0 .45em}.lead{font-size:clamp(1.08rem,2vw,1.4rem);color:var(--muted)}
.hero-note{border-left:5px solid var(--green);background:var(--green-soft);padding:18px;border-radius:0 13px 13px 0}.hero-note b{display:block;margin-bottom:6px}.panel{padding:24px 0 70px;scroll-margin-top:130px}.section-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:28px 0 17px}.section-head p{color:var(--muted);max-width:750px;margin:0}.card{background:#fff;border:1px solid var(--line);border-radius:15px;box-shadow:var(--shadow)}.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.grid-4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.baseline-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.status-card{padding:22px;border-top:5px solid var(--green)}.status-card.installed{border-top-color:var(--blue)}.status-head{display:flex;justify-content:space-between;color:var(--muted);font-weight:850;font-size:.78rem;letter-spacing:.08em}.metric-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}.metric-grid>div{display:grid;grid-template-columns:auto 1fr;gap:2px 8px;background:#f3f6f8;padding:12px;border-radius:10px}.metric-grid b{font-size:2rem;line-height:1;grid-row:1/3}.metric-grid span{font-weight:850}.metric-grid small{color:var(--muted)}.completion{display:flex;gap:8px;flex-wrap:wrap;margin:13px 0}.completion>*{padding:6px 9px;background:var(--green-soft);color:var(--green);border-radius:999px;font-size:.8rem}.completion.work>*{background:var(--blue-soft);color:#075fbf}.callout{padding:13px 15px;border-radius:11px}.callout.green{background:var(--green-soft);border-left:4px solid var(--green)}.callout.amber{background:var(--amber-soft);border-left:4px solid var(--amber)}.checkpoint{padding:20px;margin-top:16px}.checkpoint-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px}.checkpoint-actions>div{padding:12px;background:#f4f6f9;border-radius:10px}
.pill{display:inline-flex;padding:5px 9px;border-radius:999px;background:var(--blue-soft);color:#075fbf;font-size:.75rem;font-weight:900}.pill.green{background:var(--green-soft);color:var(--green)}.step,.principle,.zone,.gate,.source,.role,.authority-node,.phase,.evidence-step{padding:17px}.step code,.gate pre{display:block;background:var(--navy);color:#eaf3ff;padding:10px;border-radius:9px;overflow-wrap:anywhere;white-space:pre-wrap}.stop,.no{color:var(--red)}.artifact-grid details{background:#fff;border:1px solid var(--line);border-radius:12px}.artifact-grid summary{padding:14px;cursor:pointer;font-weight:850}.artifact-grid details>div{padding:14px;border-top:1px solid var(--line)}
.js body[data-active-view="cycle"] .global-hero{display:none}.cycle-banner{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:22px 24px;margin-bottom:34px;background:var(--blue-soft);border:1px solid #b7d6ff;border-radius:16px}.cycle-banner h2{font-size:1.55rem;margin:.1em 0}.cycle-banner p{color:var(--muted);margin:0}.cycle-hero{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:24px;padding-bottom:24px;border-bottom:1px solid var(--line)}.cycle-hero h2{font-size:clamp(2.1rem,4vw,3.75rem)}.cycle-principles{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.cycle-stage-nav{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:10px;margin:24px 0}.cycle-stage{border:1px solid var(--line);border-radius:12px;background:var(--paper);padding:15px 10px;min-height:68px;font-weight:850;color:var(--ink);cursor:pointer;transition:background-color .18s ease,border-color .18s ease,box-shadow .18s ease}.cycle-stage[aria-selected="true"]{background:var(--blue);border-color:var(--blue);color:#fff;box-shadow:0 5px 16px rgba(20,119,237,.2)}.cycle-stage-panels{display:grid;gap:14px}.cycle-stage-panel{padding:22px}.js .cycle-stage-panel:not(.is-active){display:none}.cycle-stage-head{display:grid;grid-template-columns:auto 1fr;gap:8px 18px;align-items:start}.cycle-stage-head .cycle-count{grid-row:1/3;display:inline-grid;place-items:center;min-width:76px;padding:9px;border-radius:10px;background:var(--blue-soft);color:var(--blue);font-weight:900}.cycle-stage-head p{color:var(--muted);margin:0}.cycle-fields{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;margin-top:20px;padding-top:20px;border-top:1px solid var(--line)}.cycle-field b{display:block;color:var(--muted);font-size:.76rem;letter-spacing:.06em;text-transform:uppercase;margin-bottom:5px}.cycle-evidence{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.cycle-boundary{margin-top:14px;padding:11px 13px;border-left:4px solid var(--amber);background:var(--amber-soft);font-size:.9rem}
.guided-demo-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:34px 0 15px}.guided-demo-head p{color:var(--muted);margin:0;max-width:820px}.scene-toolbar{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin:12px 0}.scene-progress{font-weight:900;color:var(--blue);font-family:"SFMono-Regular",monospace}.scene-actions{display:flex;gap:8px;flex-wrap:wrap}.scene-actions button,.demo-start{border:1px solid var(--line);border-radius:10px;background:var(--paper);color:var(--ink);padding:10px 13px;font-weight:800;cursor:pointer}.demo-start{background:var(--blue);border-color:var(--blue);color:#fff}.scene-actions button:disabled{cursor:not-allowed;opacity:.45}.scene-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:14px 0}.scene-button{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;text-align:left;border:1px solid var(--line);border-left:5px solid #b9d6fa;border-radius:11px;background:var(--paper);color:var(--ink);padding:13px;cursor:pointer;transition:background-color .18s ease,border-color .18s ease}.scene-button strong{display:block}.scene-button small{grid-column:2;color:var(--muted)}.scene-button span{grid-row:1/3;display:grid;place-items:center;width:32px;height:32px;border-radius:8px;background:#f0f2f6;font-weight:900}.scene-button[aria-pressed="true"]{border-color:var(--blue);border-left-color:var(--blue);background:var(--blue-soft)}
.scene-panels{display:grid;gap:14px}.scene-panel{padding:22px}.js .scene-panel:not(.is-active){display:none}.scene-panel-head{display:flex;align-items:start;justify-content:space-between;gap:14px}.scene-panel-head p{color:var(--muted);margin:0}.scene-layout{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(280px,.6fr);gap:18px;margin-top:18px}.scene-narrative{display:grid;gap:12px}.scene-narrative>div,.scene-governance{padding:13px;border-radius:10px;background:#f3f5f8}.scene-narrative b,.scene-governance b{display:block;color:var(--green);font-size:.75rem;letter-spacing:.06em;margin-bottom:4px}.scene-governance{background:var(--green-soft)}.scene-claim{padding:13px;border-left:4px solid var(--amber);background:var(--amber-soft)}.gate-story{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:16px}.gate-moment{padding:12px;background:var(--navy);color:#fff;border-radius:10px}.gate-moment b{display:block;color:#9fc7f8;font-size:.74rem}.gate-moment strong{display:block;margin:3px 0}.roundtrip{margin-top:18px;padding:16px;border-left:5px solid var(--green);background:var(--green-soft);border-radius:0 12px 12px 0}
.glossary-intro{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(280px,.7fr);gap:18px;align-items:start}.glossary-intro .lead{margin-bottom:0}.glossary-note{padding:18px;border-left:5px solid var(--green);background:var(--green-soft);border-radius:0 13px 13px 0}.identifier-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px;margin:22px 0 30px}.identifier-card{padding:15px;min-height:150px}.identifier-card code{display:inline-block;background:var(--navy);color:#fff;padding:6px 9px;border-radius:7px;font-weight:850}.identifier-card strong{display:block;margin:12px 0 4px}.identifier-card p{color:var(--muted);margin:0;font-size:.9rem}
.glossary-controls{display:none;grid-template-columns:minmax(260px,1fr) minmax(220px,.45fr) auto;gap:12px;align-items:end;padding:16px;margin:10px 0 14px}.js .glossary-controls{display:grid}.field{display:grid;gap:6px}.field label{font-size:.78rem;font-weight:900;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}.field input,.field select{width:100%;min-height:46px;border:1px solid #b9c2d0;border-radius:10px;background:#fff;color:var(--ink);padding:10px 12px;font:inherit}.field input:focus,.field select:focus{outline:3px solid #ffb400;outline-offset:2px;border-color:var(--blue)}.glossary-clear{min-height:46px;border:1px solid var(--line);border-radius:10px;background:var(--paper);color:var(--ink);padding:10px 14px;font-weight:850;cursor:pointer}.glossary-stats{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:36px;margin-bottom:12px}.glossary-count{font-weight:900;color:var(--blue)}.glossary-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.glossary-term{overflow:hidden;box-shadow:none}.glossary-term[hidden]{display:none}.glossary-term summary{display:grid;grid-template-columns:1fr auto;gap:4px 14px;align-items:center;padding:17px;cursor:pointer;list-style-position:inside}.glossary-term summary::marker{color:var(--blue)}.glossary-term summary strong{font-size:1.08rem}.glossary-term summary small{grid-column:1;color:var(--muted)}.term-status{grid-column:2;grid-row:1/3;justify-self:end;padding:4px 8px;border-radius:999px;background:var(--green-soft);color:var(--green);font-size:.7rem;font-weight:900;text-transform:uppercase;letter-spacing:.04em}.term-status.parcial{background:var(--amber-soft);color:#8b5600}.term-status.referencial,.term-status.convencion{background:#f0edf9;color:var(--violet)}.glossary-body{padding:0 17px 17px;border-top:1px solid var(--line)}.glossary-body p{margin:13px 0}.glossary-body b{color:var(--green)}.glossary-sources{margin:8px 0 0;padding-left:19px;color:var(--muted);font-size:.82rem}.glossary-sources code{overflow-wrap:anywhere}.glossary-empty{padding:24px;text-align:center;background:var(--amber-soft);border:1px dashed var(--amber);border-radius:12px}.glossary-empty[hidden]{display:none}
.table-wrap{overflow:auto;background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}table{border-collapse:collapse;width:100%}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:12px}th{background:#f0f3f7;color:var(--muted);font-size:.75rem;letter-spacing:.07em;text-transform:uppercase}.pass{color:var(--green);font-weight:900}.authority{display:flex;gap:10px;overflow:auto}.authority-node{min-width:220px}.trace{padding:17px;background:var(--navy);color:#fff;border-radius:13px;font-family:monospace}.flow{display:flex;gap:8px;flex-wrap:wrap}.flow span{padding:8px 11px;background:var(--green-soft);border-radius:9px;font-weight:800}.flow i{font-style:normal;color:var(--green);font-weight:900}.boundary{padding:18px;border-left:5px solid var(--amber);background:var(--amber-soft);border-radius:0 12px 12px 0}.footer{border-top:1px solid var(--line);padding:28px 0 40px;color:var(--muted);font-size:.86rem}
@media(max-width:1100px){.cycle-stage-nav{grid-template-columns:repeat(4,minmax(0,1fr))}.cycle-fields,.scene-grid,.gate-story,.identifier-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:980px){.hero-grid,.baseline-grid,.grid-2,.grid-3,.grid-4,.glossary-intro,.glossary-grid{grid-template-columns:1fr}.topbar-inner{align-items:flex-start;flex-direction:column;padding:13px 0}.topbar{position:relative}.section-head{align-items:flex-start;flex-direction:column}}
@media(max-width:700px){.cycle-hero,.cycle-fields,.scene-layout,.cycle-stage-nav,.scene-grid,.gate-story,.identifier-grid,.glossary-controls{grid-template-columns:1fr}.cycle-banner,.guided-demo-head{align-items:flex-start;flex-direction:column}.cycle-principles{justify-content:flex-start}.cycle-stage-head{grid-template-columns:1fr}.cycle-stage-head .cycle-count{grid-row:auto;justify-self:start}.scene-panel-head{flex-direction:column}.glossary-term summary{grid-template-columns:1fr}.term-status{grid-column:1;grid-row:auto;justify-self:start}.glossary-stats{align-items:flex-start;flex-direction:column}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.cycle-stage,.scene-button{transition:none}}
@media print{.topbar{position:relative}.tabs,.scene-actions,.demo-start,.glossary-controls{display:none!important}.panel,.cycle-stage-panel,.scene-panel,.glossary-term[hidden],.glossary-term>div{display:block!important}.card,.table-wrap{box-shadow:none}body{background:#fff}}
"""


def render(data: dict[str, Any], canonical: dict[str, Any]) -> str:
    validate(data)
    meta = data["meta"]
    baseline = data["baseline"]
    installed = baseline["installed"]
    feature = canonical["feature"]
    lineage = canonical["lineage"]
    release = canonical["release"]
    release_genealogy = release["genealogy"]
    adr = canonical["adr"]["counts"]
    rfc = canonical["rfc"]
    adr_accepted_label = "aceptado" if adr["accepted"] == 1 else "aceptados"
    rfc_ratified_label = "ratificado" if rfc["ratified"] == 1 else "ratificados"

    nav = "".join(
        f'<a id="view-tab-{esc(item["id"])}" href="#{esc(item["id"])}" role="tab" '
        f'aria-controls="{esc(item["id"])}" aria-selected="false">'
        f'{esc(item["label"])}</a>'
        for item in meta["navigation"]
    )
    pending_count = feature["tasks_pending"]
    pending_label = f"{pending_count} " + ("pendiente" if pending_count == 1 else "pendientes")
    if feature["pending_ids"]:
        pending_label += " · " + ", ".join(feature["pending_ids"])
    baseline_card = f"""
    <article class="card status-card installed"><div class="status-head"><span>{esc(installed['label'])}</span><strong>{esc(installed['status'])}</strong></div>
    <h2>{esc(installed['genealogy'])}</h2><div class="metric-grid">
    <div><b>{adr['total']}</b><span>ADR</span><small>{adr['accepted']} {adr_accepted_label} · {adr['proposed']} propuestos · {adr['deprecated']} derogados</small></div>
    <div><b>{rfc['total']}</b><span>RFC</span><small>{rfc['ratified']} {rfc_ratified_label} · {rfc['proposed']} propuestos</small></div></div>
    <div class="callout green"><b>{esc(installed['decision']['id'])} · {esc(installed['decision']['status'])}</b><div>{esc(installed['decision']['meaning'])}</div></div>
    <div class="completion" aria-label="Contrato de genealogía portable"><span>{esc(release['schema'])}</span><strong>{esc(release_genealogy['kind'])}</strong><span>{esc(release_genealogy['root_derivation'])}</span><span>branch {esc(release_genealogy['canonical_branch'])}</span><span>{esc(release['publication'])}</span></div>
    <p><b>CAMBIO DE NORMALIZACIÓN</b> · <code>{esc(feature['path'])}</code></p>
    <div class="completion work"><strong>{feature['tasks_complete']}/{feature['tasks_total']} tareas completadas</strong><span>{esc(pending_label)}</span><span>fase {esc(feature['phase'])}</span><span>{esc(feature['status'])}</span></div>
    <p><b>{esc(feature['id'])}</b> · {esc(installed['feature']['meaning'])}</p>
    <div class="completion" aria-label="Genealogía de features"><span>Baseline · {esc(lineage['baseline_feature']['path'])}</span><span>Última cerrada · {esc(lineage['last_closed_feature']['path'])}</span><strong>Foco activo · {esc(lineage['active_feature']['path'])}</strong></div></article>"""
    growth = baseline["growth_rule"]
    growth_card = f"""
    <article class="card status-card"><div class="status-head"><span>{esc(growth['label'])}</span><strong>{esc(growth['status'])}</strong></div>
    <h2>{esc(growth['title'])}</h2><p>{esc(growth['activation_condition'])}</p>{items(growth['steps'])}
    <div class="callout green"><b>LÍMITE</b><div>{esc(growth['boundary'])}</div></div></article>"""
    checkpoint = baseline["checkpoint"]
    checkpoint_html = f"""
    <article class="card checkpoint"><p class="eyebrow">CHECKPOINT HUMANO</p><h3>{esc(checkpoint['question'])}</h3>
    <div class="checkpoint-actions"><div><b>NO</b><p>{esc(checkpoint['no'])}</p></div><div><b>SÍ</b><p>{esc(checkpoint['yes'])}</p></div></div>
    {items(checkpoint['non_equivalences'])}</article>"""

    quick = data["quick_start"]
    quick_cards = "".join(
        f'<article class="card step"><span class="pill">{esc(step["id"])}</span><p class="eyebrow">{esc(step["label"])}</p><h3>{esc(step["title"])}</h3><p>{esc(step["detail"])}</p><code>{esc(step["command"])}</code><p>✓ {esc(step["result"])}</p><small class="stop">DETENER SI: {esc(step["stop_if"])}</small></article>'
        for step in quick["steps"]
    )
    artifact_model = data["artifact_model"]
    artifact_cards = "".join(
        f'<details><summary><span class="pill green">{esc(item["action"])}</span> {esc(item["artifact"])}</summary><div><p><b>Cuándo:</b> {esc(item["when"])}</p><p><b>Persona:</b> {esc(item["person"])}</p><p><b>Sistema:</b> {esc(item["system"])}</p><p><b>Evidencia:</b> {esc(item["evidence"])}</p><p class="no"><b>NO:</b> {esc(item["prohibition"])}</p></div></details>'
        for item in artifact_model["artifacts"]
    )
    principle_cards = "".join(
        f'<article class="card principle"><span class="pill green">{esc(item["id"])}</span><h3>{esc(item["title"])}</h3><p>{esc(item["rule"])}</p><small><b>Lectura T0:</b> {esc(item["t0_reading"])}</small><br><small><b>Verifica:</b> {esc(item["verification"])}</small></article>'
        for item in data["principles"]["items"]
    )

    cycle = data["operating_cycle"]
    cycle_buttons = "".join(
        f'<button type="button" id="cycle-stage-tab-{stage["order"]}" '
        f'class="cycle-stage" data-cycle-stage="{stage["order"]}" role="tab" '
        f'aria-controls="cycle-stage-panel-{stage["order"]}" '
        f'aria-selected="{str(stage["order"] == 1).lower()}">'
        f'{stage["order"]}. {esc(stage["label"])}</button>'
        for stage in cycle["stages"]
    )
    cycle_panels = "".join(
        f'<article id="cycle-stage-panel-{stage["order"]}" '
        f'class="card cycle-stage-panel{" is-active" if stage["order"] == 1 else ""}" '
        f'data-cycle-stage-panel="{stage["order"]}" role="tabpanel" '
        f'aria-labelledby="cycle-stage-tab-{stage["order"]}">'
        f'<div class="cycle-stage-head"><span class="cycle-count">'
        f'{stage["order"]:02d} / 07</span><div><p class="eyebrow">'
        f'ETAPA {esc(stage["label"].upper())}</p><h3>{esc(stage["title"])}</h3>'
        f'<p>{esc(stage["description"])}</p></div></div>'
        f'<div class="cycle-fields"><div class="cycle-field"><b>Pregunta</b>'
        f'{esc(stage["question"])}</div><div class="cycle-field"><b>Entrada</b>'
        f'{esc(stage["input"])}</div><div class="cycle-field"><b>Control</b>'
        f'{esc(stage["control"])}</div><div class="cycle-field"><b>Salida</b>'
        f'{esc(stage["output"])}</div></div><div class="cycle-evidence">'
        + "".join(f'<span class="pill">{esc(item)}</span>' for item in stage["evidence"])
        + f'</div><div class="cycle-boundary"><b>LÍMITE DEL CLAIM:</b> '
        f'{esc(stage["claim_boundary"])}</div></article>'
        for stage in cycle["stages"]
    )
    scene_buttons = "".join(
        f'<button type="button" class="scene-button" data-cycle-scene="{scene["order"]}" '
        f'data-cycle-scene-stage="{scene["stage"]}" '
        f'aria-controls="cycle-scene-panel-{scene["order"]}" '
        f'aria-pressed="{str(scene["order"] == 1).lower()}" '
        f'aria-current="{"step" if scene["order"] == 1 else "false"}" '
        f'aria-label="Escena {scene["order"]} de 8: {esc(scene["title"])}">'
        f'<span>{scene["order"]}</span><strong>{esc(scene["title"])}</strong>'
        f'<small>{esc(scene["detail"])}</small></button>'
        for scene in cycle["scenes"]
    )

    def render_scene_panel(scene: dict[str, Any]) -> str:
        gate_story = ""
        if scene.get("gate_story"):
            gate_story = (
                '<div class="gate-story" aria-label="Relato fail-closed didáctico">'
                + "".join(
                    f'<div class="gate-moment"><b>{esc(moment["label"])}</b>'
                    f'<strong>{esc(moment["status"])}</strong>'
                    f'<small>{esc(moment["detail"])}</small></div>'
                    for moment in scene["gate_story"]
                )
                + "</div>"
            )
        return (
            f'<article id="cycle-scene-panel-{scene["order"]}" '
            f'class="card scene-panel{" is-active" if scene["order"] == 1 else ""}" '
            f'data-cycle-scene-panel="{scene["order"]}" '
            f'aria-label="Escena {scene["order"]} de 8: {esc(scene["title"])}">'
            f'<div class="scene-panel-head"><div><p class="eyebrow">'
            f'ESCENA {scene["order"]:02d} · ETAPA {scene["stage"]}</p>'
            f'<h3>{esc(scene["title"])}</h3><p>{esc(scene["detail"])}</p></div>'
            f'<span class="pill green">'
            f'{esc(cycle["stages"][scene["stage"] - 1]["label"])}</span></div>'
            f'<div class="scene-layout"><div class="scene-narrative">'
            f'<div><b>FOCO</b>{esc(scene["focus"])}</div>'
            f'<div><b>EVIDENCIA ESPERADA</b>{esc(scene["evidence"])}</div>'
            f'<div class="scene-governance"><b>GOBIERNO</b>'
            f'{esc(scene["governance"])}</div></div><aside>'
            f'<div class="scene-claim"><b>LÍMITE DEL CLAIM</b>'
            f'<p>{esc(scene["claim_boundary"])}</p></div><div class="cycle-evidence">'
            + "".join(
                f'<span class="pill">{esc(item)}</span>' for item in scene["artifacts"]
            )
            + f'</div></aside></div>{gate_story}</article>'
        )

    scene_panels = "".join(render_scene_panel(scene) for scene in cycle["scenes"])

    adr_table = table(
        ("ID", "Título", "Estado", "Owner", "Fecha", "Path"),
        ((row["ID"], row["Título"], row["Estado"], row["Owner"], row["Fecha"], row["Path"])
         for row in canonical["adr"]["rows"]),
    )
    authority = data["authority_chain"]
    authority_cards = "".join(
        f'<article class="card authority-node"><span class="pill">{node["order"]:02d}</span><h3>{esc(node["label"])}</h3><p>{esc(node["owns"])}</p><small><b>Autoridad:</b> {esc(node["human_authority"])}</small><br><small><b>Cambia vía:</b> {esc(node["may_change_via"])}</small></article>'
        for node in authority["nodes"]
    )
    governance = data["governance"]
    routes = "".join(
        f'<article class="card role"><span class="pill">{esc(route["id"])}</span><h3>{esc(route["label"])}</h3><p>{esc(route["trigger"])}</p><small>{esc(route["path"])}</small></article>'
        for route in governance["triage"]["routes"]
    )
    dimensions = table(
        ("Dimensión", "RFC", "ADR"),
        ((row["dimension"], row["rfc"], row["adr"])
         for row in governance["rfc_vs_adr"]["dimensions"]),
    )
    roles = "".join(
        f'<article class="card role"><h3>{esc(role["role"])}</h3><p>{esc(role["decides"])}</p><small class="no">No delega: {esc(role["cannot_delegate_to_system"])}</small></article>'
        for role in governance["roles"]
    )

    lifecycle = data["lifecycle"]
    lifecycle_cards = "".join(
        f'<article class="card phase"><span class="pill">{item["order"]:02d}</span><h3>{esc(item["label"])}</h3><p>{esc(item["question"])}</p><small><b>Salida:</b> {esc(item["output"])}</small></article>'
        for item in lifecycle["steps"]
    )
    spec_kit = data["spec_kit"]
    phase_cards = "".join(
        f'<article class="card phase"><span class="pill green">{phase["order"]:02d} · {esc(phase["verb"])}</span><h3>{esc(phase["label"])}</h3><p><b>Entrada:</b> {esc(phase["input"])}</p><p><b>Salida:</b> {esc(phase["output"])}</p><small class="no"><b>Bloquea:</b> {esc(phase["blocking_rule"])}</small></article>'
        for phase in spec_kit["phases"]
    )

    ia_table = table(
        ("Orden", "Pregunta", "Fuente"),
        ((row["Orden"], row["Pregunta"], row["Fuente"]) for row in canonical["information"]),
    )
    architecture = data["architecture"]
    zones = "".join(
        f'<article class="card zone"><span class="pill green">{esc(zone["order"])} · {esc(zone["label"])}</span><h3>{esc(zone["id"])}</h3><code>{esc(zone["path"])}</code><p>{esc(zone["keeps"])}</p><small class="no"><b>NO contiene:</b> {esc(zone["must_not_contain"])}</small></article>'
        for zone in architecture["zones"]
    )
    runtime_flow = '<div class="flow">' + '<i>→</i>'.join(
        f'<span>{esc(step)}</span>' for step in architecture["runtime_flow"]
    ) + '</div>'

    evidence = canonical["evidence"]
    evidence_table = table(
        evidence["headers"],
        (tuple(row[header] for header in evidence["headers"])
         for row in evidence["rows"]),
    )
    gate_cards = "".join(
        f'<article class="card gate"><span class="pill">{esc(gate["type"])}</span><h3>{esc(gate["id"])}</h3><pre>{esc(gate["command"])}</pre><p><b>Demuestra:</b> {esc(gate["proves"])}</p><small class="no"><b>NO demuestra:</b> {esc(gate["does_not_prove"])}</small></article>'
        for gate in canonical["gates"]
    )
    evidence_chain = "".join(
        f'<article class="card evidence-step"><span class="pill">{item["order"]:02d}</span><h3>{esc(item["label"])}</h3><p>{esc(item["proof"])}</p><small>{esc(item["answers"])}</small></article>'
        for item in data["evidence_chain"]["items"]
    )
    claims = "".join(
        f'<article class="callout amber"><b>{esc(item["status"])}</b><p>{esc(item["claim"])}</p><small>{esc(item["boundary"])}</small></article>'
        for item in data["claim_boundaries"]["items"]
    )
    sources = "".join(
        f'<article class="card source"><span class="pill">{esc(source["id"])}</span><h3>{esc(source["title"])}</h3><code>{esc(source["path"])}</code><p>{esc(source["supports"])}</p></article>'
        for source in data["sources"]
    )

    glossary = data["glossary"]
    category_labels = {
        category["id"]: category["label"] for category in glossary["categories"]
    }
    glossary_options = "".join(
        f'<option value="{esc(category["id"])}">{esc(category["label"])}</option>'
        for category in glossary["categories"]
    )
    identifier_cards = "".join(
        f'<article class="card identifier-card"><code>{esc(item["code"])}</code>'
        f'<strong>{esc(item["reads"])}</strong><p>{esc(item["meaning"])}</p></article>'
        for item in glossary["identifier_guide"]
    )
    status_labels = {
        "vigente": "Vigente",
        "parcial": "Contrato parcial",
        "referencial": "Referencia no materializada",
        "convencion": "Convención externa",
    }

    def glossary_search_text(entry: dict[str, Any]) -> str:
        return " ".join((
            entry["term"],
            entry["expansion"],
            entry["definition"],
            entry["usage"],
            entry["boundary"],
            category_labels[entry["category"]],
        ))

    glossary_cards = "".join(
        f'<details class="card glossary-term" open data-glossary-term="{esc(entry["id"])}" '
        f'data-glossary-category="{esc(entry["category"])}" '
        f'data-glossary-search="{esc(glossary_search_text(entry))}">'
        f'<summary id="glossary-summary-{esc(entry["id"])}">'
        f'<strong>{esc(entry["term"])}</strong><small>{esc(entry["expansion"])}</small>'
        f'<span class="term-status {esc(entry["status"])}">'
        f'{esc(status_labels[entry["status"]])}</span></summary><div class="glossary-body">'
        f'<p><b>En simple:</b> {esc(entry["definition"])}</p>'
        f'<p><b>En EDAIOS:</b> {esc(entry["usage"])}</p>'
        f'<p><b>Límite:</b> {esc(entry["boundary"])}</p><b>Fuente local de uso o autoridad:</b>'
        f'<ul class="glossary-sources">'
        + "".join(f'<li><code>{esc(source)}</code></li>' for source in entry["sources"])
        + '</ul></div></details>'
        for entry in glossary["terms"]
    )
    glossary_controls = f"""<div class="card glossary-controls" aria-label="Controles del glosario">
      <div class="field"><label for="glossary-search">Buscar término o significado</label><input id="glossary-search" type="search" autocomplete="off" placeholder="Ej.: ADR, tarea, conocimiento…" data-glossary-search-input></div>
      <div class="field"><label for="glossary-category">Categoría</label><select id="glossary-category" data-glossary-category-select>{glossary_options}</select></div>
      <button type="button" class="glossary-clear" data-glossary-clear>Limpiar</button>
    </div>"""

    panels = f"""
    <section id="quick-start" class="panel" data-panel="quick-start" role="tabpanel" aria-labelledby="view-tab-quick-start"><div class="baseline-grid">{baseline_card}{growth_card}</div>{checkpoint_html}
    <div class="section-head"><div><p class="eyebrow">RECORRIDO DE ENTRADA</p><h2>{esc(quick['title'])}</h2></div><p>{esc(quick['subtitle'])}</p></div><div class="grid-3">{quick_cards}</div>
    <div class="section-head"><div><p class="eyebrow">QUÉ HEREDAS Y QUÉ CREAS</p><h2>{esc(artifact_model['title'])}</h2></div></div><div class="grid-2 artifact-grid">{artifact_cards}</div>
    <div class="section-head"><div><p class="eyebrow">CONSTITUCIÓN</p><h2>{esc(data['principles']['title'])}</h2></div><p>{esc(data['principles']['subtitle'])}</p></div><div class="grid-3">{principle_cards}</div></section>
    <section id="cycle" class="panel" data-panel="cycle" role="tabpanel" aria-labelledby="view-tab-cycle"><div id="operating-cycle">
    <div class="cycle-banner"><div><p class="eyebrow">{esc(cycle['eyebrow'])}</p><h2>{esc(cycle['title'])}</h2><p>{esc(cycle['subtitle'])}</p></div><button type="button" class="demo-start" data-cycle-action="start">Iniciar demo · 1–8</button></div>
    <div class="cycle-hero"><div><p class="eyebrow">EDAIOS · OPERATING SYSTEM DEL CONOCIMIENTO</p><h2>{esc(meta['title'])}</h2><p class="lead">{esc(cycle['thesis'])}</p></div><div class="cycle-principles">{''.join(f'<span class="pill">{esc(item)}</span>' for item in cycle['principles'])}</div></div>
    <div class="cycle-stage-nav" role="tablist" aria-label="Etapas del Operating System">{cycle_buttons}</div>
    <div class="cycle-stage-panels">{cycle_panels}</div>
    <div class="guided-demo-head"><div><p class="eyebrow">RUTA COMPLETA</p><h2>Ocho escenas, siete etapas</h2><p>Cada escena ilumina la parte del sistema que toma el control. Git conserva; las vistas derivan; el aprendizaje vuelve al inicio.</p></div></div>
    <div class="scene-toolbar"><span class="scene-progress" data-cycle-progress aria-live="polite" aria-atomic="true">01 / 08</span><div class="scene-actions"><button type="button" data-cycle-action="previous" disabled>Anterior</button><button type="button" data-cycle-action="next">Siguiente</button><button type="button" data-cycle-action="restart">Reiniciar</button></div></div>
    <div class="scene-grid" aria-label="Escenas del recorrido">{scene_buttons}</div>
    <div class="scene-panels">{scene_panels}</div>
    <div class="roundtrip"><b>ROUNDTRIP</b><p>{esc(cycle['roundtrip'])}</p></div>
    <div class="callout amber" style="margin-top:14px"><b>FRONTERA DE LA DEMO</b><div>{esc(cycle['boundary'])}</div></div>
    </div></section>
    <section id="governance" class="panel" data-panel="governance" role="tabpanel" aria-labelledby="view-tab-governance"><div class="section-head"><div><p class="eyebrow">CATÁLOGO VIGENTE</p><h2>{adr['accepted']} ADR {adr_accepted_label} · {rfc['ratified']} RFC {rfc_ratified_label}</h2></div><p>Conteos y filas leídos de los ledgers canónicos.</p></div>{adr_table}
    <div class="section-head"><div><p class="eyebrow">AUTORIDAD</p><h2>{esc(authority['title'])}</h2></div><p>{esc(authority['conflict_rule'])}</p></div><div class="authority">{authority_cards}</div>
    <div class="section-head"><div><p class="eyebrow">TRIAGE</p><h2>{esc(governance['title'])}</h2></div></div><div class="grid-2">{routes}</div>
    <div class="section-head"><div><p class="eyebrow">RFC VS ADR</p><h2>{esc(governance['rfc_vs_adr']['headline'])}</h2></div></div>{dimensions}
    <div class="section-head"><div><p class="eyebrow">RESPONSABILIDAD</p><h2>Los sistemas verifican; las personas deciden</h2></div></div><div class="grid-2">{roles}</div></section>
    <section id="spec-kit" class="panel" data-panel="spec-kit" role="tabpanel" aria-labelledby="view-tab-spec-kit"><div class="section-head"><div><p class="eyebrow">CICLO COMPLETO</p><h2>{esc(lifecycle['title'])}</h2></div><p>{esc(lifecycle['subtitle'])}</p></div><div class="grid-4">{lifecycle_cards}</div>
    <div class="section-head"><div><p class="eyebrow">OCHO FASES</p><h2>{esc(spec_kit['title'])}</h2></div><p>{esc(spec_kit['phase_rule'])}</p></div><div class="grid-4">{phase_cards}</div><div class="section-head"><div><p class="eyebrow">TRAZABILIDAD</p><h2>Del intent al outcome</h2></div></div><div class="trace">{esc(spec_kit['traceability']['chain'])}</div></section>
    <section id="architecture" class="panel" data-panel="architecture" role="tabpanel" aria-labelledby="view-tab-architecture"><div class="section-head"><div><p class="eyebrow">ARQUITECTURA DE INFORMACIÓN</p><h2>Dónde responder cada pregunta</h2></div><p>Tabla leída de {esc(INFORMATION_ARCHITECTURE)}</p></div>{ia_table}
    <div class="section-head"><div><p class="eyebrow">FOUNDATION → CORE</p><h2>{esc(architecture['title'])}</h2></div><p>{esc(architecture['dependency_rule'])}</p></div><div class="grid-3">{zones}</div><div class="section-head"><div><p class="eyebrow">DIRECCIÓN</p><h2>Una sola dirección de autoridad</h2></div></div>{runtime_flow}<div class="section-head"><div><p class="eyebrow">FUERA DE LA BASE</p><h2>Lo que deberá ingresar por necesidad real</h2></div></div><article class="card zone">{items(architecture['out_of_scope_t0'])}</article></section>
    <section id="evidence" class="panel" data-panel="evidence" role="tabpanel" aria-labelledby="view-tab-evidence"><div class="section-head"><div><p class="eyebrow">{esc(evidence['eyebrow'])}</p><h2>{esc(evidence['title'])}</h2></div><p>{esc(evidence['scope'])}</p></div>{evidence_table}<div class="boundary"><b>LÍMITE DE LA EVIDENCIA</b><p>{esc(evidence['boundary'])}</p></div>
    <div class="section-head"><div><p class="eyebrow">FAIL CLOSED</p><h2>{esc(data['gates']['title'])}</h2></div><p>{esc(data['gates']['subtitle'])}</p></div><div class="grid-3">{gate_cards}</div><div class="section-head"><div><p class="eyebrow">CADENA</p><h2>{esc(data['evidence_chain']['title'])}</h2></div></div><div class="grid-3">{evidence_chain}</div><div class="section-head"><div><p class="eyebrow">FRONTERAS</p><h2>{esc(data['claim_boundaries']['title'])}</h2></div></div><div class="grid-2">{claims}</div><div class="section-head"><div><p class="eyebrow">FUENTES</p><h2>La guía apunta al conocimiento de origen</h2></div></div><div class="grid-3">{sources}</div></section>
    <section id="glossary" class="panel" data-panel="glossary" role="tabpanel" aria-labelledby="view-tab-glossary"><div class="glossary-intro"><div><p class="eyebrow">{esc(glossary['eyebrow'])}</p><h2>{esc(glossary['title'])}</h2><p class="lead">{esc(glossary['subtitle'])}</p></div><aside class="glossary-note"><b>LECTURA SOURCE-FIRST</b><p>{esc(glossary['source_note'])}</p></aside></div>
    <div class="section-head"><div><p class="eyebrow">CÓMO LEER LOS CÓDIGOS</p><h2>Prefijo, número y contexto</h2></div><p>FR-001, SC-001 y T001 viven dentro de una feature. T001 es una tarea; T0 es sensibilidad.</p></div><div class="identifier-grid">{identifier_cards}</div>
    {glossary_controls}<noscript><div class="callout amber"><b>Sin JavaScript</b><div>Todos los términos permanecen desplegados para lectura; búsqueda y filtros requieren JavaScript local.</div></div></noscript>
    <div class="glossary-stats"><span class="glossary-count" data-glossary-count role="status" aria-live="polite" aria-atomic="true">{len(glossary['terms'])} términos</span><small>Abre cualquier término para ver uso, límite y fuente.</small></div>
    <div class="glossary-empty" data-glossary-empty hidden><b>No encontramos términos con esos filtros.</b><p>Prueba otra palabra o limpia la categoría.</p></div><div class="glossary-grid" data-glossary-grid>{glossary_cards}</div></section>
    """

    config_json = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(meta['title'])} · Core {esc(meta['version'])}</title><style>{CSS}</style></head><body>
    <a class="skip" href="#main">Saltar al contenido</a><header class="topbar"><div class="shell topbar-inner"><div class="brand"><strong>EDAIOS</strong><small>{esc(meta['eyebrow'])}</small></div><nav class="tabs" role="tablist" aria-label="Vistas">{nav}</nav><div class="brand"><strong>{esc(meta['status'])}</strong><small>v{esc(meta['version'])} · {esc(meta['as_of'])}</small></div></div></header>
    <main id="main" class="shell"><section class="hero global-hero"><div class="hero-grid"><div><p class="eyebrow">{esc(meta['eyebrow'])}</p><h1>{esc(meta['title'])}</h1><p class="lead">{esc(meta['subtitle'])}</p></div><div class="hero-note"><b>{esc(meta['status_title'])}</b>{esc(meta['status_message'])}</div></div><div class="callout green"><b>TESIS OPERATIVA</b><div>{esc(meta['operating_thesis'])}</div></div></section>{panels}</main>
    <footer class="footer"><div class="shell"><strong>Core {esc(meta['version'])} · {esc(meta['status'].lower())} · vista regenerable.</strong> Fuentes: <code>{esc(OS_CONFIG)}</code>, <code>{esc(INFORMATION_ARCHITECTURE)}</code>, <code>{esc(ADR_CATALOG)}</code>, <code>{esc(FEATURE_HANDOFF)}</code>, <code>{esc(RELEASE_STATE)}</code> y <code>{esc(canonical['evidence_path'])}</code>. La raíz única se deriva después del commit; el baseline instalado no prueba ancla externa, tag, release público, adopción ni producción.</div></footer>
    <script id="demo-config" type="application/json">{config_json}</script><script>(function(){{
      document.documentElement.classList.add('js');
      const config=JSON.parse(document.getElementById('demo-config').textContent);
      const stageSceneMap=config.operating_cycle.stage_scene_map.map(Number);
      const tabs=[...document.querySelectorAll('.tabs [role="tab"]')];
      const panels=[...document.querySelectorAll('[data-panel]')];
      const validViews=new Set(panels.map(panel=>panel.dataset.panel));
      function activateView(id,focus){{
        if(!validViews.has(id)) id='quick-start';
        tabs.forEach(tab=>{{
          const active=tab.hash==='#'+id;
          tab.setAttribute('aria-selected',String(active));
          tab.tabIndex=active?0:-1;
          if(active&&focus) tab.focus();
        }});
        panels.forEach(panel=>panel.hidden=panel.dataset.panel!==id);
        document.body.dataset.activeView=id;
      }}
      function viewFromHash(){{activateView(location.hash.slice(1)||'quick-start',false)}}
      tabs.forEach((tab,index)=>{{
        tab.addEventListener('click',()=>activateView(tab.hash.slice(1),false));
        tab.addEventListener('keydown',event=>{{
          let next=index;
          if(event.key==='ArrowRight') next=(index+1)%tabs.length;
          if(event.key==='ArrowLeft') next=(index-1+tabs.length)%tabs.length;
          if(event.key==='Home') next=0;
          if(event.key==='End') next=tabs.length-1;
          if(next!==index){{
            event.preventDefault();
            location.hash=tabs[next].hash;
            activateView(tabs[next].hash.slice(1),true);
          }}
        }});
      }});

      const glossaryTerms=[...document.querySelectorAll('[data-glossary-term]')];
      const glossarySearch=document.querySelector('[data-glossary-search-input]');
      const glossaryCategory=document.querySelector('[data-glossary-category-select]');
      const glossaryCount=document.querySelector('[data-glossary-count]');
      const glossaryEmpty=document.querySelector('[data-glossary-empty]');
      const glossaryClear=document.querySelector('[data-glossary-clear]');
      function normalizeGlossary(value){{
        return String(value||'').normalize('NFD')
          .replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es').trim();
      }}
      function filterGlossary(){{
        const query=normalizeGlossary(glossarySearch.value);
        const category=glossaryCategory.value;
        let visible=0;
        glossaryTerms.forEach(term=>{{
          const matchesText=!query||normalizeGlossary(term.dataset.glossarySearch).includes(query);
          const matchesCategory=category==='all'||term.dataset.glossaryCategory===category;
          const matches=matchesText&&matchesCategory;
          term.hidden=!matches;
          if(matches) visible+=1;
        }});
        glossaryCount.textContent=visible+' '+(visible===1?'término':'términos');
        glossaryEmpty.hidden=visible!==0;
        document.body.dataset.glossaryResults=String(visible);
      }}
      if(glossaryTerms.length&&glossarySearch&&glossaryCategory&&glossaryCount&&
          glossaryEmpty&&glossaryClear){{
        glossaryTerms.forEach(term=>{{term.open=false}});
        glossarySearch.addEventListener('input',filterGlossary);
        glossaryCategory.addEventListener('change',filterGlossary);
        glossaryClear.addEventListener('click',()=>{{
          glossarySearch.value='';
          glossaryCategory.value='all';
          filterGlossary();
          glossarySearch.focus();
        }});
        filterGlossary();
      }}

      const stageButtons=[...document.querySelectorAll('[data-cycle-stage]')];
      const stagePanels=[...document.querySelectorAll('[data-cycle-stage-panel]')];
      const sceneButtons=[...document.querySelectorAll('[data-cycle-scene]')];
      const scenePanels=[...document.querySelectorAll('[data-cycle-scene-panel]')];
      const progress=document.querySelector('[data-cycle-progress]');
      const previous=document.querySelector('[data-cycle-action="previous"]');
      const next=document.querySelector('[data-cycle-action="next"]');

      function selectScene(order,focusTarget){{
        const selected=Math.max(1,Math.min(sceneButtons.length,Number(order)||1));
        const sceneButton=sceneButtons.find(
          button=>Number(button.dataset.cycleScene)===selected
        );
        const stage=stageSceneMap[selected-1];
        const stageButton=stageButtons.find(
          button=>Number(button.dataset.cycleStage)===stage
        );
        stageButtons.forEach(button=>{{
          const active=button===stageButton;
          button.setAttribute('aria-selected',String(active));
          button.tabIndex=active?0:-1;
        }});
        stagePanels.forEach(panel=>{{
          const active=Number(panel.dataset.cycleStagePanel)===stage;
          panel.classList.toggle('is-active',active);
          panel.setAttribute('aria-hidden',String(!active));
        }});
        sceneButtons.forEach(button=>{{
          const active=button===sceneButton;
          button.setAttribute('aria-pressed',String(active));
          button.setAttribute('aria-current',active?'step':'false');
        }});
        scenePanels.forEach(panel=>{{
          const active=Number(panel.dataset.cycleScenePanel)===selected;
          panel.classList.toggle('is-active',active);
          panel.setAttribute('aria-hidden',String(!active));
        }});
        progress.textContent=String(selected).padStart(2,'0')+' / '+
          String(sceneButtons.length).padStart(2,'0');
        previous.disabled=selected===1;
        next.disabled=selected===sceneButtons.length;
        document.body.dataset.cycleScene=String(selected);
        document.body.dataset.cycleStage=String(stage);
        if(focusTarget==='scene') sceneButton.focus();
        if(focusTarget==='stage') stageButton.focus();
      }}
      function firstSceneForStage(stage){{
        return stageSceneMap.findIndex(candidate=>candidate===stage)+1;
      }}
      function sceneForStage(stage){{
        const current=Number(document.body.dataset.cycleScene||1);
        return stageSceneMap[current-1]===stage?current:firstSceneForStage(stage);
      }}

      stageButtons.forEach((button,index)=>{{
        button.addEventListener('click',()=>{{
          const stage=Number(button.dataset.cycleStage);
          selectScene(sceneForStage(stage),'stage');
        }});
        button.addEventListener('keydown',event=>{{
          let nextIndex=index;
          if(event.key==='ArrowRight') nextIndex=(index+1)%stageButtons.length;
          if(event.key==='ArrowLeft') nextIndex=(index-1+stageButtons.length)%stageButtons.length;
          if(event.key==='Home') nextIndex=0;
          if(event.key==='End') nextIndex=stageButtons.length-1;
          if(nextIndex!==index){{
            event.preventDefault();
            const stage=Number(stageButtons[nextIndex].dataset.cycleStage);
            selectScene(sceneForStage(stage),'stage');
          }}
        }});
      }});
      sceneButtons.forEach((button,index)=>{{
        button.addEventListener('click',()=>selectScene(Number(button.dataset.cycleScene),'scene'));
        button.addEventListener('keydown',event=>{{
          let nextIndex=index;
          if(event.key==='ArrowRight') nextIndex=Math.min(sceneButtons.length-1,index+1);
          if(event.key==='ArrowLeft') nextIndex=Math.max(0,index-1);
          if(event.key==='ArrowDown') nextIndex=Math.min(sceneButtons.length-1,index+4);
          if(event.key==='ArrowUp') nextIndex=Math.max(0,index-4);
          if(event.key==='Home') nextIndex=0;
          if(event.key==='End') nextIndex=sceneButtons.length-1;
          if(nextIndex!==index){{
            event.preventDefault();
            selectScene(nextIndex+1,'scene');
          }}
        }});
      }});
      document.querySelectorAll('[data-cycle-action]').forEach(button=>{{
        button.addEventListener('click',()=>{{
          const action=button.dataset.cycleAction;
          const current=Number(document.body.dataset.cycleScene||1);
          if(action==='start'){{
            location.hash='cycle';
            activateView('cycle',false);
            selectScene(1,'stage');
            document.getElementById('operating-cycle').scrollIntoView({{
              block:'start',
              behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'
            }});
          }}
          if(action==='restart') selectScene(1,'scene');
          if(action==='previous') selectScene(current-1,false);
          if(action==='next') selectScene(current+1,false);
        }});
      }});
      document.addEventListener('keydown',event=>{{
        if(event.key==='Escape'&&document.body.dataset.activeView==='cycle'){{
          selectScene(1,'scene');
        }}
      }});
      addEventListener('hashchange',viewFromHash);
      selectScene(1,false);
      viewFromHash();
      document.body.dataset.demoReady='true';
    }})();</script></body></html>\n"""


def rendered(root: Path) -> str:
    data = load_json(root / OS_CONFIG)
    validate(data)
    return render(data, canonical_views(root, data))


def write(root: Path, check: bool) -> int:
    content = rendered(root)
    destination = root / OS_OUTPUT
    if check:
        if not destination.exists() or destination.read_text(encoding="utf-8") != content:
            print(f"ERROR: derivado fuera de sincronía: {OS_OUTPUT}", file=sys.stderr)
            return 1
        print("core-base demo: 1/1 sincronizada; fuentes y handoff canónicos contrastados")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8", newline="\n")
    print(f"generated {OS_OUTPUT}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="raíz del repositorio")
    parser.add_argument("--check", action="store_true", help="falla si el HTML tiene drift")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return write(Path(args.root).resolve(), args.check)
    except DemoContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
