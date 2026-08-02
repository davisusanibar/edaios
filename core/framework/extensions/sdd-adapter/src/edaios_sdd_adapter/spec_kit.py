"""Adapter GitHub Spec Kit (ADR-0003, operacionalizado por ADR-0003/F3).

Spec Kit es MIT/agent-agnostic (CLI `specify`); su flujo es
`constitution → specify → clarify → checklist → plan → tasks → analyze → implement`,
con artefactos en el repo:
`.specify/memory/constitution.md` y, por feature, `spec.md` / `plan.md` / `tasks.md`.

Este adapter materializa el contrato del scaffold para Spec Kit, **pineado**:
- **Aguas arriba:** `seed_speckit_constitution` siembra `.specify/memory/constitution.md`
  con el bundle de contexto de EDAIOS (principios + dominio).
- **Aguas abajo:** `ingest_speckit` lee los artefactos de Spec Kit y los ingiere como
  **borradores** trazables en `.edaios/drafts/`, con procedencia y versión pineada.

Sin dependencias externas (no se invoca a Spec Kit aquí; se opera sobre sus
artefactos en disco). El invariante de dependencias sigue matizado por ADR-0003/PAT-003.
"""
from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

from edaios_sdd_adapter.adapter import (
    export_context_bundle,
    ingest_artifact,
)

SOURCE_TOOL = "github-spec-kit"
SPECKIT_VERSION_PINNED = "0.12.11"

# Mapeo DECLARADO artefacto-externo → (archivo, kind, tipo de KO borrador).
# Los borradores viven en zona excluida; el tipo definitivo se fija en la
# promoción humana + ADR. `ArtefactoExterno` señala "externo sin tipar aún".
SPECKIT_MAPPING: dict[str, tuple[str, str]] = {
    "spec": ("spec.md", "ArtefactoExterno"),
    "plan": ("plan.md", "ArtefactoExterno"),
    "tasks": ("tasks.md", "ArtefactoExterno"),
    "research": ("research.md", "ArtefactoExterno"),
    "data-model": ("data-model.md", "ArtefactoExterno"),
    "quickstart": ("quickstart.md", "ArtefactoExterno"),
    "checklist": ("requirements.md", "ArtefactoExterno"),
}

CONSTITUTION_REL = ".specify/memory/constitution.md"


def seed_speckit_constitution(
    root: Path, out_dir: Path, *, domain: str | None = None,
    domain_dir: str | Path | None = None, project: str = "proyecto"
) -> Path:
    """Proyecta la constitucion compilada y anexa el contexto del dominio.

    `root` es el repo EDAIOS autoritativo; `out_dir` es un repo de delivery. La
    funcion no reconstruye principios: copia la vista compilada y solo agrega un
    apendice derivado del bundle. Un dominio exige su `domain_dir` explícito:
    Core no fija ninguna raíz de dominios.
    """
    bundle = export_context_bundle(Path(root), domain=domain, domain_dir=domain_dir)
    if domain and not bundle.get("domain", {}).get("types"):
        raise ValueError(f"no se pudo exportar el contexto gobernado del dominio {domain}")
    source = Path(root) / CONSTITUTION_REL
    if not source.exists():
        raise FileNotFoundError(
            f"constitucion compilada ausente: {source}; ejecuta compile_constitution.py"
        )
    text = source.read_text(encoding="utf-8").rstrip() + "\n"
    lines = [
        "",
        "## Contexto de entrega exportado por EDAIOS",
        "",
        f"- Proyecto: {project}",
        f"- Dominio: {domain or 'sin dominio'}",
        f"- Context bundle: `{bundle.get('digest', '')}`",
        f"- Spec Kit: `{SPECKIT_VERSION_PINNED}`",
    ]
    types = bundle.get("domain", {}).get("types", [])
    if types:
        lines += ["", "### Tipos de dominio disponibles", "", ", ".join(types)]
    text += "\n".join(lines) + "\n"
    dest = Path(out_dir) / CONSTITUTION_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


GATE_REL = "tools/validation/spec_kit_gate.py"
GATE_SIDECAR_REL = "tools/validation/spec_kit_gate.SOURCE.md"


def _gate_sidecar_text(core_version: str, digest: str) -> str:
    return (
        "# Procedencia de spec_kit_gate.py (sembrado)\n\n"
        "Entrega gobernada por el adapter (ADR-0020, resuelve RFC-0002): la\n"
        "copia se re-siembra con `seed_gate`; una copia divergente nunca se\n"
        "sobrescribe sin confirmación explícita.\n\n"
        "| Campo | Valor |\n"
        "|---|---|\n"
        f"| Core | edaios-core v{core_version} |\n"
        f"| sha256 | `{digest}` |\n"
        f"| Fecha de siembra | {date.today().isoformat()} |\n"
        "| Vía | `edaios_sdd_adapter.seed_gate` |\n\n"
        "Re-sincronizar: volver a ejecutar `seed_gate` desde el Core vigente.\n"
    )


def seed_gate(root: Path, out_dir: Path, *, force: bool = False) -> Path:
    """Siembra el gate SDD en un consumer con procedencia verificable (ADR-0020).

    `root` es el repo EDAIOS autoritativo; `out_dir` es el repo o módulo del
    consumer. Contención física: destino y sidecar deben vivir bajo `out_dir`
    tras resolver symlinks (RA-003, specs/016). Idempotente y convergente: con
    gate byte-idéntico el sidecar se auto-repara si falta o no declara la
    procedencia vigente (RA-001) — reintentar tras una escritura parcial
    converge al estado correcto. Un gate divergente NO se sobrescribe sin
    `force=True` (la deriva se reporta con ambos digests, RFC-0002); un sidecar
    previo sin gate acompañante tampoco se pisa sin `force` (RA-004). `force`
    materializa la confirmación explícita del owner del consumer.
    """
    source = Path(root) / GATE_REL
    if not source.exists():
        raise FileNotFoundError(f"gate fuente ausente: {source}")
    payload = source.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    core_version = (Path(root) / "VERSION").read_text(encoding="utf-8").strip()
    out = Path(out_dir).resolve()
    dest = Path(out_dir) / GATE_REL
    sidecar = Path(out_dir) / GATE_SIDECAR_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.parent.resolve().is_relative_to(out):
        raise ValueError(
            "contención física violada: tools/validation del consumer escapa "
            "de su raíz (symlink) — la siembra se detiene"
        )
    for target in (dest, sidecar):
        if target.is_symlink() or (
            target.exists() and not target.resolve().is_relative_to(out)
        ):
            raise ValueError(
                f"contención física violada: {target.name} es o atraviesa un "
                "symlink — la siembra se detiene"
            )
    expected_sidecar = _gate_sidecar_text(core_version, digest)
    if dest.exists():
        current = hashlib.sha256(dest.read_bytes()).hexdigest()
        if current == digest:
            # RA-001: la procedencia es proyección del estado real; si falta o
            # no declara el digest vigente vía seed_gate, se repara.
            healthy = (
                sidecar.exists()
                and digest in sidecar.read_text(encoding="utf-8")
                and "seed_gate" in sidecar.read_text(encoding="utf-8")
            )
            if not healthy:
                sidecar.write_text(expected_sidecar, encoding="utf-8")
            return dest
        if not force:
            raise ValueError(
                "gate del consumer divergente de la fuente "
                f"(consumer=sha256:{current[:12]} fuente=sha256:{digest[:12]}); "
                "la deriva se reporta, no se pisa — re-siembra con force=True"
            )
    elif sidecar.exists() and not force:
        raise ValueError(
            "sidecar de procedencia previo sin gate acompañante: su registro "
            "no se pisa — archívalo y re-siembra con force=True"
        )
    dest.write_bytes(payload)
    sidecar.write_text(expected_sidecar, encoding="utf-8")
    return dest


def _resolve_specs_root(search_root: Path) -> tuple[Path, Path]:
    """Normaliza repo root, `specs/` o una feature a su raiz Spec Kit."""
    search_root = Path(search_root)
    if search_root.name == "specs" and search_root.is_dir():
        return search_root, search_root
    nested = search_root / "specs"
    if nested.is_dir():
        return nested, nested
    if search_root.parent.name == "specs" and search_root.is_dir():
        return search_root.parent, search_root
    raise ValueError(f"no se encontro un arbol Spec Kit specs/<feature> bajo {search_root}")


def discover_speckit_artifacts(specify_dir: Path) -> list[tuple[str, Path]]:
    """Lista artefactos bajo una raiz de repo, `specs/` o feature concreta.

    La contencion es FISICA, no lexical: la ruta RESUELTA (symlinks incluidos)
    debe vivir bajo specs/ resuelto. Un symlink que escapa del arbol ingeriria
    contenido arbitrario del disco como borrador con procedencia legitima —
    fail-closed (F3.4, tras verificacion adversarial con exfiltracion reproducida).
    """
    specs_root, scan_root = _resolve_specs_root(Path(specify_dir))
    resolved_root = specs_root.resolve()
    found: list[tuple[str, Path]] = []
    by_name = {fname: kind for kind, (fname, _tipo) in SPECKIT_MAPPING.items()}
    for p in sorted(scan_root.rglob("*.md")):
        if p.name not in by_name:
            continue
        try:
            p.resolve(strict=True).relative_to(resolved_root)
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"artefacto escapa de specs/ al resolver symlinks: {p}") from exc
        relative = p.relative_to(specs_root)
        if len(relative.parts) < 2:
            raise ValueError(f"artefacto fuera de specs/<feature>: {p}")
        if len(relative.parts) <= 4:
            found.append((by_name[p.name], p))
    return found


def ingest_speckit(
    root: Path,
    specify_dir: Path,
    *,
    sensitivity: str,
    tool_version: str = SPECKIT_VERSION_PINNED,
) -> list[Path]:
    """Ingiere los artefactos de Spec Kit de `specify_dir` como borradores en
    `.edaios/drafts/` del repo `root`. Devuelve las rutas de los borradores."""
    root = Path(root)
    search_root = Path(specify_dir)
    specs_root, _scan_root = _resolve_specs_root(search_root)
    artifacts: list[tuple[str, Path, str]] = []
    seen: set[tuple[str, str]] = set()
    for kind, path in discover_speckit_artifacts(specify_dir):
        feature_relative = path.relative_to(specs_root)
        feature = feature_relative.parts[0]
        key = (feature, kind)
        if key in seen:
            raise ValueError(f"artefacto Spec Kit duplicado para feature={feature} kind={kind}")
        seen.add(key)
        artifacts.append((kind, path, feature))

    drafts: list[Path] = []
    for kind, path, feature in artifacts:
        _fname, tipo = SPECKIT_MAPPING[kind]
        relative = path.relative_to(search_root)
        raw = path.read_bytes()
        content = raw.decode("utf-8", errors="strict")
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        drafts.append(
            ingest_artifact(
                root,
                name=f"{feature} {kind}",
                kind=kind,
                content=content,
                tipo=tipo,
                source_tool=SOURCE_TOOL,
                tool_version=tool_version,
                sensitivity=sensitivity,
                source_ref=relative.as_posix(),
                source_digest=digest,
            )
        )
    return drafts
