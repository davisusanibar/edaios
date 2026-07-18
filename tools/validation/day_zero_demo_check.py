#!/usr/bin/env python3
"""Verifica la guía source-first del baseline Core 3.1.0 portable, offline."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_SOURCES = {
    "docs/information-architecture.md",
    "governance/ADR_CATALOG.md",
    "governance/RFC_CATALOG.md",
    ".specify/feature.json",
    ".specify/release.json",
}
EXPECTED_STAGE_SCENE_MAP = [1, 2, 3, 4, 5, 6, 6, 7]
EXPECTED_ACTIONS = {"start", "previous", "next", "restart"}
EXPECTED_NAV = [
    "quick-start", "cycle", "governance", "spec-kit", "architecture", "evidence", "glossary"
]
REQUIRED_GLOSSARY_TERMS = {
    "adr", "rfc", "t0", "t1-t3", "fr", "sc", "task", "art", "val", "ko", "kom",
    "spec-kit", "gate", "fail-closed", "owner", "evidence", "value-ledger", "pii",
    "working-memory", "derived-index", "conflict-candidate", "memory-adapter",
}
REQUIRED_GLOSSARY_CODES = {
    "ADR-0010", "ADR-0011", "ADR-0013", "FR-001", "SC-001", "T001",
    "ART-008", "T0", "VAL-004",
}


def task_counts(path: Path) -> tuple[int, int, int, list[str]]:
    text = path.read_text(encoding="utf-8")
    states = re.findall(r"^- \[([ xX])\] \[(T\d{3})\]", text, re.MULTILINE)
    complete = sum(state.lower() == "x" for state, _ in states)
    total = len(states)
    pending_ids = [task_id for state, task_id in states if state.lower() != "x"]
    return total, complete, total - complete, pending_ids


def frontmatter(source: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", source)
    return match.group(1).strip().strip('"') if match else None


def table_row_count(source: str, headers: list[str]) -> int:
    expected = [cell.strip() for cell in headers]
    lines = source.splitlines()
    index = next(
        (
            position
            for position, line in enumerate(lines)
            if line.lstrip().startswith("|")
            and [cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")]
            == expected
        ),
        None,
    )
    if index is None or index + 1 >= len(lines):
        return 0
    count = 0
    for line in lines[index + 2:]:
        if not line.lstrip().startswith("|"):
            break
        count += 1
    return count


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []
    registered_gates: dict[str | None, str | None] = {}
    task_summary = (0, 0, 0)
    feature_state = ""
    feature_phase = ""
    evidence_config: dict[str, object] = {}
    adr_ids: list[str] = []
    rfc_ids: list[str] = []
    expected = {
        root / "docs/demos/README.md",
        root / "docs/demos/edaios-operating-system.config.json",
        root / "docs/demos/edaios-operating-system.html",
        root / "docs/demos/edaios-core-quickstart.html",
    }
    actual = set((root / "docs/demos").glob("*"))
    extra = sorted(str(path.relative_to(root)) for path in actual - expected)
    missing = sorted(str(path.relative_to(root)) for path in expected - actual)
    if extra:
        errors.append("vistas extra: " + ", ".join(extra))
    if missing:
        errors.append("archivos de guía ausentes: " + ", ".join(missing))

    result = subprocess.run(
        [sys.executable, "tools/publishing/generate_day_zero_demos.py", "--check"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        errors.append("drift config→HTML: " + result.stdout.strip())

    try:
        config_path = root / "docs/demos/edaios-operating-system.config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        if data.get("schema") != "edaios.operating-system-demo/v4":
            errors.append("schema de guía Core inválido")
        meta = data["meta"]
        if meta.get("version") != "3.1.0":
            errors.append("la guía no declara Core 3.1.0")
        if meta.get("status") != "BASELINE INSTALADO":
            errors.append("la guía no muestra Core como BASELINE INSTALADO")
        navigation = [item.get("id") for item in meta.get("navigation", [])]
        if navigation != EXPECTED_NAV:
            errors.append(f"navegación de siete vistas inválida: {navigation}")

        installed = data["baseline"]["installed"]
        if installed.get("genealogy") != "Foundation + Core":
            errors.append("genealogía visible distinta de Foundation + Core")
        if installed.get("version") != "3.1.0":
            errors.append("el baseline visible no identifica Core 3.1.0")
        if installed.get("status") != "INSTALADO":
            errors.append("el baseline visible no está INSTALADO")
        release_state = json.loads(
            (root / ".specify/release.json").read_text(encoding="utf-8")
        )
        expected_release_genealogy = {
            "kind": "single-root",
            "root_derivation": "unique-reachable-root",
            "canonical_branch": "main",
        }
        if release_state.get("schema") != "edaios.core-release-state/v2":
            errors.append("release state portable no usa schema v2")
        if release_state.get("version") != "3.1.0":
            errors.append("release state portable no identifica Core 3.1.0")
        if release_state.get("status") != "baseline":
            errors.append("release state portable no permanece en baseline")
        if release_state.get("genealogy") != expected_release_genealogy:
            errors.append(
                "genealogía portable inválida: "
                f"{release_state.get('genealogy')}"
            )
        if release_state.get("active_candidate") is not None:
            errors.append("release state portable infiere un candidato")
        if release_state.get("publication") != "not-claimed":
            errors.append("release state portable infiere publicación")
        if release_state.get("governing_adr") != "ADR-0013":
            errors.append("release state portable no está gobernado por ADR-0013")
        decision = installed.get("decision", {})
        if (
            decision.get("id") != release_state.get("governing_adr")
            or decision.get("status") != "Aceptado"
        ):
            errors.append("autoridad del baseline no resuelve a ADR-0013 Aceptado")
        growth = data["baseline"]["growth_rule"]
        if growth.get("status") != "SIN INICIATIVA INSTALADA":
            errors.append("la guía no declara la ausencia de iniciativas instaladas")

        handoff = json.loads((root / ".specify/feature.json").read_text(encoding="utf-8"))
        if handoff.get("schema") not in {"edaios.feature-handoff/v2", "edaios.feature-handoff/v3"}:
            errors.append("handoff canónico no usa un schema soportado")
        idle = handoff.get("schema") == "edaios.feature-handoff/v3" and handoff.get("active_feature") is None
        expected_lineage = {
            key: ({"id": handoff[key]["id"], "path": str(handoff[key]["feature_directory"]).rstrip("/") + "/"}
                  if handoff.get(key) is not None else None)
            for key in ("baseline_feature", "last_closed_feature", "active_feature")
        }
        visible_lineage = installed.get("lineage", {})
        if idle:
            expected_lineage["active_feature"] = expected_lineage["last_closed_feature"]
        if visible_lineage != expected_lineage:
            errors.append(
                "genealogía visible no deriva del handoff: "
                f"guía={visible_lineage} handoff={expected_lineage}"
            )
        expected_ids = {
            key: (handoff[key]["id"] if handoff.get(key) is not None else None)
            for key in ("baseline_feature", "last_closed_feature", "active_feature")
        }
        if not idle and {key: value.get("id") for key, value in expected_lineage.items()} != expected_ids:
            errors.append(f"handoff no coincide con sus punteros: {expected_lineage}")

        feature = installed.get("feature", {})
        active = expected_lineage["last_closed_feature"] if idle else expected_lineage["active_feature"]
        if feature.get("id") != active["id"] or feature.get("path") != active["path"]:
            errors.append("feature visible no coincide con active_feature")
        feature_root = root / active["path"]
        spec_text = (feature_root / "spec.md").read_text(encoding="utf-8")
        state = frontmatter(spec_text, "estado")
        phase = frontmatter(spec_text, "fase")
        feature_state = state or ""
        feature_phase = phase or ""
        compatible = (
            (state == "Cerrado" and phase == "implemented")
            or (
                state in {"Borrador", "Propuesto"}
                and phase in {"specified", "clarified", "planned", "tasked"}
            )
        )
        if not compatible:
            errors.append(f"feature activa con estado/fase incompatibles: {state}/{phase}")

        total, complete, pending, pending_ids = task_counts(feature_root / "tasks.md")
        task_summary = (total, complete, pending)
        if total == 0:
            errors.append("la feature activa no declara tareas")
        if phase == "implemented" and pending_ids:
            errors.append(f"feature implementada conserva pendientes: {pending_ids}")

        cycle = data["operating_cycle"]
        stages = cycle.get("stages", [])
        scenes = cycle.get("scenes", [])
        stage_scene_map = cycle.get("stage_scene_map")
        if [stage.get("order") for stage in stages] != list(range(1, 8)):
            errors.append("el ciclo no conserva las siete etapas consecutivas")
        if [scene.get("order") for scene in scenes] != list(range(1, 9)):
            errors.append("la ruta no conserva las ocho escenas consecutivas")
        if stage_scene_map != EXPECTED_STAGE_SCENE_MAP:
            errors.append(f"mapa etapa-escena inválido: {stage_scene_map}")
        scene_stages = [scene.get("stage") for scene in scenes]
        if stage_scene_map != scene_stages:
            errors.append(
                "stage_scene_map no coincide con scenes[].stage: "
                f"mapa={stage_scene_map} escenas={scene_stages}"
            )
        if set(stage_scene_map or []) != set(range(1, 8)):
            errors.append("el mapa etapa-escena no cubre las siete etapas")

        catalog = (root / "governance/ADR_CATALOG.md").read_text(encoding="utf-8")
        adr_ids = re.findall(r"^\| (ADR-\d{4}) \|", catalog, re.MULTILINE)
        expected_adrs = [f"ADR-{index:04d}" for index in range(1, len(adr_ids) + 1)]
        if adr_ids != expected_adrs:
            errors.append(f"la guía no puede derivar el catálogo ADR vigente: {adr_ids}")
        rfc_catalog = (root / "governance/RFC_CATALOG.md").read_text(encoding="utf-8")
        rfc_ids = re.findall(r"^\| (RFC-\d{4}) \|", rfc_catalog, re.MULTILINE)
        expected_rfcs = [f"RFC-{index:04d}" for index in range(1, len(rfc_ids) + 1)]
        if rfc_ids != expected_rfcs or not rfc_ids:
            errors.append(f"la guía no puede derivar el catálogo RFC vigente: {rfc_ids}")

        source_paths = {str(row["path"]) for row in data.get("sources", [])}
        evidence_config = installed.get("evidence", {})
        evidence_path = str(evidence_config.get("path", ""))
        missing_integrations = sorted((REQUIRED_SOURCES | {evidence_path}) - source_paths)
        if missing_integrations:
            errors.append(
                "fuentes integradas ausentes: " + ", ".join(missing_integrations)
            )
        unresolved = sorted(path for path in source_paths if not (root / path).exists())
        if unresolved:
            errors.append("fuentes no resolubles: " + ", ".join(unresolved))

        evidence_file = root / evidence_path
        evidence_text = evidence_file.read_text(encoding="utf-8")
        evidence_headers = evidence_config.get("headers", [])
        if (
            not isinstance(evidence_headers, list)
            or len(evidence_headers) < 2
            or table_row_count(evidence_text, evidence_headers) == 0
        ):
            errors.append("registro de evidencia configurado no contiene una tabla verificable")
        for key in ("eyebrow", "title", "scope", "boundary"):
            if not str(evidence_config.get(key, "")).strip():
                errors.append(f"metadata de evidencia ausente: {key}")

        gate_registry = json.loads(
            (root / ".specify/gates.json").read_text(encoding="utf-8")
        )
        registered_gates = {
            row.get("id"): row.get("command") for row in gate_registry.get("gates", [])
        }
        configured_gate_notes = {
            row.get("id"): row.get("command")
            for row in data.get("gates", {}).get("items", [])
            if row.get("type") == "executable"
        }
        stale_gate_notes = sorted(set(configured_gate_notes) - set(registered_gates))
        drifted_commands = sorted(
            gate_id for gate_id, command in configured_gate_notes.items()
            if registered_gates.get(gate_id) != command
        )
        if stale_gate_notes or drifted_commands:
            errors.append(
                "notas de gates contradicen .specify/gates.json: "
                f"extras={stale_gate_notes} comandos={drifted_commands}"
            )

        glossary = data.get("glossary", {})
        categories = [item.get("id") for item in glossary.get("categories", [])]
        if not categories or categories[0] != "all" or len(categories) != len(set(categories)):
            errors.append(f"categorías de glosario inválidas: {categories}")
        guide_codes = {item.get("code") for item in glossary.get("identifier_guide", [])}
        missing_codes = sorted(REQUIRED_GLOSSARY_CODES - guide_codes)
        if missing_codes:
            errors.append("guía de identificadores incompleta: " + ", ".join(missing_codes))
        glossary_terms = glossary.get("terms", [])
        glossary_ids = [entry.get("id") for entry in glossary_terms]
        if len(glossary_ids) < 25 or len(glossary_ids) != len(set(glossary_ids)):
            errors.append(
                f"inventario de glosario inválido: total={len(glossary_ids)} "
                f"únicos={len(set(glossary_ids))}"
            )
        missing_terms = sorted(REQUIRED_GLOSSARY_TERMS - set(glossary_ids))
        if missing_terms:
            errors.append("términos obligatorios ausentes: " + ", ".join(missing_terms))
        glossary_source_paths = {
            source for entry in glossary_terms for source in entry.get("sources", [])
        }
        unresolved_glossary = sorted(
            path for path in glossary_source_paths if not (root / path).exists()
        )
        if unresolved_glossary:
            errors.append(
                "fuentes del glosario no resolubles: " + ", ".join(unresolved_glossary)
            )
        by_id = {entry.get("id"): entry for entry in glossary_terms}
        val = by_id.get("val", {})
        if val.get("status") != "referencial" or "No existe hoy un catálogo VAL" not in val.get("boundary", ""):
            errors.append("VAL no está acotado como referencia no materializada")
        sensitivity = by_id.get("t1-t3", {})
        if sensitivity.get("status") != "vigente" or "taxonomía operativa de Core" not in sensitivity.get("boundary", ""):
            errors.append("T1–T3 no declara su taxonomía operativa y límite")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"config de guía inválido: {exc}")

    retired_tokens = (
        "Fl" + "ink",
        "Ma" + "ven",
        "m" + "vn",
    )
    forbidden_notice = (
        "Esta " + "vista es una propuesta, no el " + "cut" + "over."
    )
    for path in expected:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix in {".html", ".json"} and re.search(
            r"(?:src|href)=[\"']https?://", text, re.IGNORECASE
        ):
            errors.append(f"asset externo en {path.relative_to(root)}")
        if forbidden_notice in text:
            errors.append(f"alerta de propuesta obsoleta en {path.relative_to(root)}")
        if any(token.lower() in text.lower() for token in retired_tokens):
            errors.append(f"consumer o runtime retirado en {path.relative_to(root)}")

    html_path = root / "docs/demos/edaios-operating-system.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        registry_ids = list(registered_gates)
        rendered_gate_ids = re.findall(
            r'<article class="card gate"><span class="pill">executable</span><h3>([^<]+)</h3>',
            html,
        )
        if rendered_gate_ids != registry_ids:
            errors.append(
                "gates ejecutables HTML no derivan del registry: "
                f"html={rendered_gate_ids} registry={registry_ids}"
            )
        total, complete, pending = task_summary
        pending_label = f"{pending} " + ("pendiente" if pending == 1 else "pendientes")
        for phrase in (
            f"{complete}/{total} tareas completadas",
            pending_label,
            f"fase {feature_phase}",
            feature_state,
            "BASELINE INSTALADO",
            "Core 3.1.0",
            "SIN INICIATIVA INSTALADA",
            "ADR-0013",
            "edaios.core-release-state/v2",
            "single-root",
            "unique-reachable-root",
            ".specify/release.json",
            "capacidad vNext acumulada",
            "no existe una rama vNext",
            "El adapter Engram está incluido",
            "el runtime Engram no está instalado",
            str(evidence_config.get("title")),
            "specs/archive/004-core-multi-initiative-scale",
            "specs/archive/007-agent-working-memory-and-derived-index",
            "specs/archive/008-core-baseline-normalization",
        ):
            if phrase not in html:
                errors.append(f"estado del baseline ausente del HTML: {phrase}")
        adr_count = len([adr for adr in adr_ids if adr in {"ADR-0001", "ADR-0003", "ADR-0004", "ADR-0005", "ADR-0006", "ADR-0011", "ADR-0013", "ADR-0014", "ADR-0015"}])
        rfc_count = len(rfc_ids)
        adr_label = "aceptado" if adr_count == 1 else "aceptados"
        rfc_label = "ratificado" if rfc_count == 1 else "ratificados"
        for pattern, label in (
            (rf"<b>{adr_count}</b><span>ADR</span>", f"{adr_count} ADR derivados"),
            (rf"<b>{rfc_count}</b><span>RFC</span>", f"{rfc_count} RFC derivados"),
            (
                rf"<h2>{adr_count} ADR {adr_label} · {rfc_count} RFC {rfc_label}</h2>",
                "catálogo vigente",
            ),
        ):
            if not re.search(pattern, html):
                errors.append(f"conteo canónico ausente del HTML: {label}")
        stage_tabs = re.findall(
            r'<button[^>]+data-cycle-stage="(\d+)"[^>]+role="tab"'
            r'[^>]+aria-controls="cycle-stage-panel-(\d+)"',
            html,
        )
        expected_stage_pairs = [(str(i), str(i)) for i in range(1, 8)]
        if stage_tabs != expected_stage_pairs:
            errors.append(f"tabs de etapa incompletos o mal enlazados: {stage_tabs}")

        stage_panels = re.findall(
            r'<article id="cycle-stage-panel-(\d+)"[^>]+'
            r'data-cycle-stage-panel="(\d+)"[^>]+role="tabpanel"[^>]+'
            r'aria-labelledby="cycle-stage-tab-(\d+)"',
            html,
        )
        expected_stage_triples = [(str(i), str(i), str(i)) for i in range(1, 8)]
        if stage_panels != expected_stage_triples:
            errors.append(f"paneles de etapa incompletos o mal enlazados: {stage_panels}")

        scene_pairs = [
            (int(scene), int(stage))
            for scene, stage in re.findall(
                r'<button[^>]+data-cycle-scene="(\d+)"[^>]+'
                r'data-cycle-scene-stage="(\d+)"',
                html,
            )
        ]
        expected_scene_pairs = list(enumerate(EXPECTED_STAGE_SCENE_MAP, start=1))
        if scene_pairs != expected_scene_pairs:
            errors.append(f"botones de escena incompletos o mal mapeados: {scene_pairs}")

        scene_panels = re.findall(
            r'<article id="cycle-scene-panel-(\d+)"[^>]+'
            r'data-cycle-scene-panel="(\d+)"',
            html,
        )
        expected_scene_panel_pairs = [(str(i), str(i)) for i in range(1, 9)]
        if scene_panels != expected_scene_panel_pairs:
            errors.append(f"paneles narrativos de escena incompletos: {scene_panels}")

        actions = set(re.findall(r'data-cycle-action="([a-z]+)"', html))
        if actions != EXPECTED_ACTIONS:
            errors.append(f"acciones de recorrido inválidas: {sorted(actions)}")
        if not re.search(
            r'data-cycle-progress[^>]+aria-live="polite"[^>]*>01 / 08<', html
        ):
            errors.append("contador vivo 01 / 08 ausente")

        selected_stages = re.findall(
            r'<button[^>]+class="cycle-stage"[^>]+aria-selected="true"', html
        )
        selected_scenes = re.findall(
            r'<button[^>]+class="scene-button"[^>]+aria-pressed="true"', html
        )
        if len(selected_stages) != 1 or len(selected_scenes) != 1:
            errors.append(
                "estado inicial debe seleccionar una etapa y una escena: "
                f"etapas={len(selected_stages)} escenas={len(selected_scenes)}"
            )

        interaction_contract = (
            'function selectScene(order,focusTarget)',
            'function firstSceneForStage(stage)',
            'function sceneForStage(stage)',
            "stageSceneMap[current-1]===stage?current:firstSceneForStage(stage)",
            "previous.disabled=selected===1",
            "next.disabled=selected===sceneButtons.length",
            '.cycle-stage[aria-selected="true"]',
            '.scene-button[aria-pressed="true"]',
            'button:focus-visible',
            '@media(max-width:700px)',
            '@media(prefers-reduced-motion:reduce)',
        )
        for marker in interaction_contract:
            if marker not in html:
                errors.append(f"contrato interactivo ausente del HTML: {marker}")

        nav_ids = re.findall(r'<a id="view-tab-([a-z-]+)"', html)
        if nav_ids != EXPECTED_NAV:
            errors.append(f"tabs HTML incompletos o desordenados: {nav_ids}")
        glossary_panels = re.findall(
            r'<section id="glossary"[^>]+data-panel="glossary"[^>]+role="tabpanel"',
            html,
        )
        if len(glossary_panels) != 1:
            errors.append(f"panel Glosario ausente o duplicado: {len(glossary_panels)}")
        rendered_terms = re.findall(r'data-glossary-term="([a-z0-9-]+)"', html)
        config_term_ids = [entry.get("id") for entry in data.get("glossary", {}).get("terms", [])]
        if rendered_terms != config_term_ids:
            errors.append("términos renderizados no coinciden con el config")
        glossary_contract = (
            'type="search"',
            'data-glossary-search-input',
            'data-glossary-category-select',
            'data-glossary-count role="status" aria-live="polite"',
            'data-glossary-empty hidden',
            'function normalizeGlossary(value)',
            "normalize('NFD')",
            'function filterGlossary()',
            "category==='all'||term.dataset.glossaryCategory===category",
            "glossaryEmpty.hidden=visible!==0",
            '.glossary-term[hidden]',
            '.glossary-term[hidden],.glossary-term>div{display:block!important}',
            '@media print',
        )
        for marker in glossary_contract:
            if marker not in html:
                errors.append(f"contrato de glosario ausente del HTML: {marker}")
        for phrase in (
            "Architecture Decision Record",
            "Request for Comments",
            "T001 no significa sensibilidad T1",
            "No existe hoy un catálogo VAL",
            "taxonomía operativa de Core",
            "Working memory",
            "Índice derivado",
            "Candidato de conflicto",
            "Memory adapter",
        ):
            if phrase not in html:
                errors.append(f"aclaración de glosario ausente: {phrase}")
        if "KOM + gates VAL" in html:
            errors.append("etiqueta heredada KOM + gates VAL sigue activa")

    for error in errors:
        print(f"[FAIL] {error}")
    if errors:
        return 1
    print(
        "[core-demo] OK: Core 3.1.0 portable bajo ADR-0013; raíz única "
        "derivada, Engram adapter incluido sin runtime y crecimiento sin iniciativa"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
