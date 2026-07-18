"""Scaffold de adapter SDD (ADR-0003 · contrato de ADR-0003).

Borde de interoperabilidad entre EDAIOS (control plane) y las herramientas de
*delivery* SDD externas. **Sin dependencias externas** (solo stdlib): el invariante
"no dependencias de runtime externas" permanece **matizado por ADR-0003/PAT-003**
—la herramienta externa se invoca al borde, pineada; este código es nuestro.

Contrato bidireccional:
- **Aguas arriba (EDAIOS → delivery):** `export_context_bundle` arma un *bundle*
  **determinista** (principios/constraints de frontera + tipos/entidades de dominio
  + opcional *blast-radius*) que siembra la `constitution.md`/memoria del externo.
- **Aguas abajo (delivery → EDAIOS):** `ingest_artifact` escribe el artefacto
  externo como **Knowledge Object en estado `Borrador`** con procedencia, en la zona
  excluida `.edaios/drafts/` (nunca en zonas validadas). Promoción humana + ADR.

Garantías: determinismo e idempotencia (mismo input → mismo output y `digest`);
procedencia y versión pineada registradas; guard duro a la zona de borradores.
La herramienta externa es productora de borradores y consumidora de contexto,
jamás fuente de verdad.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from edaios_core.io import atomic_write_bytes, workspace_lock
from edaios_core.memory import ConflictCandidate, PendingConflictError

# Principios/constraints de frontera que siembran la constitución del externo.
# Son los invariantes de EDAIOS, no dependencias: viajan como texto.
FRONTIER_CONSTRAINTS: list[str] = [
    "Knowledge First: el conocimiento es el producto; el código/delivery es consecuencia.",
    "La única fuente de verdad vive en Git; ningún artefacto externo es verdad por existir.",
    "AI/herramientas externas consumen contexto y producen borradores; no gobiernan.",
    "No Architecture Change without ADR: todo cambio estructural exige ADR.",
    "Frontera de dependencias (matizada por ADR-0003/PAT-003): el núcleo permanece "
    "autocontenido y derivable de Git sin red; la interoperabilidad SDD vive solo en "
    "el borde de delivery (extensions/), con la herramienta pineada.",
    "Los artefactos del delivery se ingieren como borradores trazables; promoción humana + ADR.",
]

DRAFTS_SUBDIR = ".edaios/drafts/sdd"
SENSITIVITY_LEVELS = frozenset({"T0", "T1", "T2", "T3"})


def _load_domain_graph(domain_dir: Path) -> dict:
    """Carga el subset del EKG requerido por el adapter usando solo stdlib."""
    graph = {"entity_types": {}, "relationship_types": {}, "nodes": [], "edges": []}
    graph_dir = domain_dir / "knowledge-graph"
    for path in sorted(graph_dir.rglob("*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(spec, dict):
            raise ValueError(f"EKG malformado: {path} no es un objeto JSON")
        kind = spec.get("kind")
        if kind == "entity_type":
            graph["entity_types"][spec["name"]] = spec
        elif kind == "relationship_type":
            graph["relationship_types"][spec["name"]] = spec
        elif kind == "entity":
            graph["nodes"].append(
                {"id": spec["id"], "type": spec.get("type"), "name": spec.get("name")}
            )
        elif kind == "relationship":
            graph["edges"].append(
                {
                    "id": spec["id"],
                    "type": spec.get("type"),
                    "from": spec.get("from"),
                    "to": spec.get("to"),
                }
            )
    return graph


def build_context_bundle(
    *,
    constraints: list[str],
    domain_types: list[str],
    domain_entities: list[dict],
    blast_radius: dict | None = None,
) -> dict:
    """Arma el bundle de contexto (puro y determinista; claves ordenadas)."""
    bundle = {
        "schema": "edaios.sdd.context-bundle/v1",
        "constraints": list(constraints),
        "domain": {
            "types": sorted(domain_types),
            "entities": sorted(
                ({"id": e["id"], "type": e.get("type"), "name": e.get("name")} for e in domain_entities),
                key=lambda e: e["id"],
            ),
        },
        "blast_radius": blast_radius or {},
    }
    bundle["digest"] = bundle_digest(bundle)
    return bundle


def bundle_digest(bundle: dict) -> str:
    """SHA-256 del bundle canónico (sin la propia clave `digest`)."""
    payload = {k: v for k, v in bundle.items() if k != "digest"}
    canon = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canon.encode("utf-8")).hexdigest()


def export_context_bundle(
    root: Path,
    *,
    domain: str | None = None,
    zone: str | None = None,
    domain_dir: str | Path | None = None,
) -> dict:
    """Arma el bundle desde el repo: constraints de frontera + grafo de dominio
    (solo desde un `domain_dir` provisto explícitamente; Core no fija ninguna
    raíz de dominios) + *blast-radius* (si hay Query Engine y `zone`).
    Best-effort en lo opcional; determinista en lo presente."""
    root = Path(root)
    domain_types: list[str] = []
    domain_entities: list[dict] = []

    graph = None
    domain_dir = Path(domain_dir) if domain and domain_dir else None
    if domain_dir and (domain_dir / "knowledge-graph").exists():
        try:
            graph = _load_domain_graph(domain_dir)
            domain_types = list(graph.get("entity_types", {}).keys())
            domain_entities = graph.get("nodes", [])
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            graph = None  # el caller decide si un dominio vacio es aceptable

    blast_radius: dict | None = None
    if zone and graph is not None:
        try:
            from edaios_query.engine import impact  # type: ignore

            blast_radius = {"zone": zone, "impacted": impact(graph, zone)}
        except Exception:
            blast_radius = None  # opcional: si no hay Query Engine, se omite

    return build_context_bundle(
        constraints=FRONTIER_CONSTRAINTS,
        domain_types=domain_types,
        domain_entities=domain_entities,
        blast_radius=blast_radius,
    )


def seed_constitution_text(bundle: dict, *, project: str = "proyecto") -> str:
    """Texto de `constitution.md` (memoria del externo) sembrado desde el bundle.
    Genérico; cada adapter concreto puede formatearlo a su herramienta."""
    lines = [f"# Constitución de {project} (sembrada por EDAIOS)", ""]
    lines.append(f"<!-- bundle {bundle.get('digest','')} -->")
    lines += ["", "## Principios y restricciones no negociables", ""]
    for c in bundle.get("constraints", []):
        lines.append(f"- {c}")
    types = bundle.get("domain", {}).get("types", [])
    if types:
        lines += ["", "## Tipos de dominio disponibles", "", ", ".join(types)]
    return "\n".join(lines) + "\n"


class DraftGuardError(RuntimeError):
    """Se intentó escribir un borrador fuera de la zona `.edaios/drafts/`."""


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _single_line(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise DraftGuardError(f"{field} es obligatorio")
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized:
        raise DraftGuardError(f"{field} debe ocupar una sola línea")
    try:
        normalized.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise DraftGuardError(f"{field} no es UTF-8 válido") from exc
    return normalized


def _draft_root(root: Path, out_subdir: str) -> tuple[Path, Path]:
    if root.is_symlink():
        raise DraftGuardError("workspace root no puede ser symlink")
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise DraftGuardError("workspace root no resoluble") from exc
    raw_subdir = Path(out_subdir)
    if raw_subdir.is_absolute() or ".." in raw_subdir.parts:
        raise DraftGuardError("out_subdir debe ser relativo y sin traversal")
    out_dir = (root / raw_subdir).resolve(strict=False)
    drafts_root = (root / ".edaios" / "drafts").resolve(strict=False)
    if drafts_root not in out_dir.parents and out_dir != drafts_root:
        raise DraftGuardError(f"destino fuera de la zona de borradores: {out_dir}")
    cursor = root
    for part in out_dir.relative_to(root).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise DraftGuardError(f"symlink no admitido en borradores: {cursor}")
    return root, out_dir


def ingest_artifact(
    root: Path,
    *,
    name: str,
    kind: str,
    content: str,
    tipo: str,
    source_tool: str,
    tool_version: str,
    sensitivity: str,
    source_ref: str | None = None,
    source_digest: str | None = None,
    out_subdir: str = DRAFTS_SUBDIR,
) -> Path:
    """Escribe un artefacto externo como KO **Borrador** con procedencia, en la
    zona de borradores. Idempotente (mismo input → mismo archivo y contenido).
    Guard duro: nunca escribe fuera de `.edaios/drafts/`."""
    root, out_dir = _draft_root(Path(root), out_subdir)
    name = _single_line(name, "name")
    kind = _single_line(kind, "kind")
    tipo = _single_line(tipo, "tipo")
    source_tool = _single_line(source_tool, "source_tool")
    tool_version = _single_line(tool_version, "tool_version")
    sensitivity = _single_line(sensitivity, "sensitivity")
    if sensitivity not in SENSITIVITY_LEVELS:
        raise DraftGuardError("sensitivity debe ser T0, T1, T2 o T3")
    if source_ref is not None:
        source_ref = _single_line(source_ref, "source_ref")
    if not isinstance(content, str) or not content.strip():
        raise DraftGuardError("content es obligatorio")
    try:
        content.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise DraftGuardError("content no es UTF-8 válido") from exc
    if source_digest is not None:
        normalized = source_digest.removeprefix("sha256:").lower()
        if re.fullmatch(r"[0-9a-f]{64}", normalized) is None:
            raise DraftGuardError("source_digest debe ser SHA-256")
        source_digest = "sha256:" + normalized

    revision = {
        "name": name,
        "kind": kind,
        "tipo": tipo,
        "source_tool": source_tool,
        "tool_version": tool_version,
        "sensitivity": sensitivity,
        "source_ref": source_ref,
        "source_digest": source_digest,
        "content": content.rstrip("\n"),
    }
    revision_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            revision, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    out_dir.mkdir(parents=True, exist_ok=True)
    provenance = {
        "source_tool": source_tool,
        "tool_version": tool_version,  # pineada
        "artifact_kind": kind,
        "ingest_schema": "edaios.sdd.ingest/v1",
        "revision_digest": revision_digest,
        "subject": _slug(name),
        "claim": _slug(kind),
        "sensitivity": sensitivity,
    }
    if source_ref:
        provenance["source_ref"] = source_ref
    if source_digest:
        provenance["source_digest"] = source_digest
    observation = {
        "subject": provenance["subject"],
        "claim": provenance["claim"],
        "value": content.rstrip("\n"),
        "sensitivity": sensitivity,
        "revision_digest": revision_digest,
    }
    provenance["observation_digest"] = "sha256:" + hashlib.sha256(
        json.dumps(
            observation, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    front = (
        "---\n"
        f"id: DRAFT-{_slug(source_tool)}-{_slug(name)}-{revision_digest[-12:].upper()}\n"
        f"tipo: {tipo}\n"
        f"titulo: \"[BORRADOR] {name} ({source_tool})\"\n"
        "estado: Borrador\n"
        "idioma: es\n"
        f"procedencia: {json.dumps(provenance, ensure_ascii=False)}\n"
        "---\n\n"
    )
    body = content.rstrip("\n") + "\n\n## Historial\n- Ingerido como borrador desde " \
        f"{source_tool} {tool_version}; pendiente de promoción humana + ADR.\n"
    out_path = out_dir / (
        f"{_slug(source_tool)}--{_slug(name)}--{revision_digest[-12:]}.md"
    )
    payload = (front + body).encode("utf-8")
    with workspace_lock(root, "sdd-draft-ingest"):
        if out_path.exists() and out_path.read_bytes() != payload:
            raise DraftGuardError("colisión content-addressed en borrador")
        if not out_path.exists():
            atomic_write_bytes(out_path, payload)
    return out_path


def _draft_observations(root: Path) -> list[dict[str, str]]:
    root, out_dir = _draft_root(Path(root), DRAFTS_SUBDIR)
    if not out_dir.exists():
        return []
    observations: list[dict[str, str]] = []
    for path in sorted(out_dir.glob("*.md")):
        if path.is_symlink() or not path.is_file():
            raise DraftGuardError(f"borrador inseguro: {path}")
        try:
            raw = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as exc:
            raise DraftGuardError(f"borrador ilegible: {path}") from exc
        match = re.match(r"\A---\n(?P<header>.*?)\n---\n\n(?P<body>.*)\Z", raw, re.DOTALL)
        if match is None or "estado: Borrador" not in match.group("header").splitlines():
            raise DraftGuardError(f"front matter de borrador inválido: {path}")
        provenance_line = next(
            (
                line.removeprefix("procedencia: ")
                for line in match.group("header").splitlines()
                if line.startswith("procedencia: ")
            ),
            None,
        )
        try:
            provenance = json.loads(provenance_line or "")
        except json.JSONDecodeError as exc:
            raise DraftGuardError(f"procedencia de borrador inválida: {path}") from exc
        if not isinstance(provenance, dict):
            raise DraftGuardError(f"procedencia de borrador inválida: {path}")
        required = {
            key: _single_line(str(provenance.get(key, "")), key)
            for key in (
                "subject", "claim", "sensitivity", "revision_digest",
                "observation_digest",
            )
        }
        if required["sensitivity"] not in SENSITIVITY_LEVELS:
            raise DraftGuardError(f"sensibilidad de borrador inválida: {path}")
        for digest_key in ("revision_digest", "observation_digest"):
            if re.fullmatch(r"sha256:[0-9a-f]{64}", required[digest_key]) is None:
                raise DraftGuardError(f"{digest_key} inválido: {path}")
        value = match.group("body").split("\n\n## Historial\n", 1)[0].rstrip("\n")
        observation = {
            "subject": required["subject"],
            "claim": required["claim"],
            "value": value,
            "sensitivity": required["sensitivity"],
            "revision_digest": required["revision_digest"],
        }
        observed_digest = "sha256:" + hashlib.sha256(
            json.dumps(
                observation, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        if observed_digest != required["observation_digest"]:
            raise DraftGuardError(f"contenido de borrador alterado: {path}")
        created_at = datetime.fromtimestamp(
            path.stat().st_mtime, tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        observations.append(
            {
                **observation,
                "record_id": "DRAFT-" + required["revision_digest"][-24:].upper(),
                "created_at": created_at,
                "source_ref": path.relative_to(root).as_posix(),
            }
        )
    return observations


def draft_conflict_candidates(
    root: Path, *, name: str | None = None
) -> list[ConflictCandidate]:
    """Recalcula candidatos desde los drafts; la SQLite local no es autoridad."""
    subject_filter = _slug(_single_line(name, "name")) if name is not None else None
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for observation in _draft_observations(Path(root)):
        if subject_filter is not None and observation["subject"] != subject_filter:
            continue
        grouped.setdefault(
            (observation["subject"], observation["claim"]), []
        ).append(observation)
    candidates: list[ConflictCandidate] = []
    for (subject, claim), records in sorted(grouped.items()):
        for left, right in itertools.combinations(records, 2):
            if left["value"] == right["value"]:
                continue
            source_id, target_id = sorted((left["record_id"], right["record_id"]))
            identity = {
                "project": "edaios-drafts",
                "subject": subject,
                "claim": claim,
                "source_record_id": source_id,
                "target_record_id": target_id,
            }
            candidate_id = "CONFLICT-" + hashlib.sha256(
                json.dumps(
                    identity, ensure_ascii=True, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest()[:24].upper()
            candidates.append(
                ConflictCandidate(
                    candidate_id=candidate_id,
                    project="edaios-drafts",
                    subject=subject,
                    claim=claim,
                    source_record_id=source_id,
                    target_record_id=target_id,
                    status="review-required",
                    created_at=max(left["created_at"], right["created_at"]),
                )
            )
    return candidates


def assert_draft_promotable(root: Path, *, name: str | None = None) -> None:
    """Checkpoint fail-closed; la resolución ocurre en el flujo humano gobernado."""
    candidates = draft_conflict_candidates(Path(root), name=name)
    if candidates:
        raise PendingConflictError(
            f"promoción bloqueada: {len(candidates)} conflicto(s) review-required"
        )
