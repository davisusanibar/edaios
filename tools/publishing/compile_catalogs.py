#!/usr/bin/env python3
"""Compila ADR_CATALOG.md y RFC_CATALOG.md desde los documentos de decisión.

La fuente de verdad son los archivos individuales `governance/ADR-NNNN-*.md` y
`governance/RFC-NNNN-*.md` (ADR-0007). El catálogo es una proyección derivada:
solo lee metadatos explícitos de cabecera y falla cerrado ante números
duplicados, cabeceras no canónicas, estados fuera del dominio o drift.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADR_STATES = ("Aceptado", "Propuesto", "Derogado")
RFC_STATES = ("Borrador", "Propuesto", "Ratificado", "Rechazado", "Derogado")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
DECISION_FILE = {
    "ADR": re.compile(r"^(ADR-[0-9]{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$"),
    "RFC": re.compile(r"^(RFC-[0-9]{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$"),
}


class CatalogError(ValueError):
    """El corpus de decisiones no satisface el contrato de proyección."""


def field(
    text: str,
    name: str,
    *,
    path: Path,
    required: bool = False,
) -> str:
    pattern = re.compile(
        rf"^\*\*{re.escape(name)}:\*\*\s*(.+)$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        if required:
            raise CatalogError(f"{path.name}: {name} ausente de cabecera")
        return ""
    if len(matches) != 1:
        raise CatalogError(f"{path.name}: {name} duplicado")
    header_end = text.find("\n## ")
    if header_end < 0:
        header_end = len(text)
    if matches[0].start() >= header_end:
        raise CatalogError(f"{path.name}: {name} fuera de cabecera")
    return matches[0].group(1).strip()


def _heading_title(text: str, doc_id: str, path: Path) -> str:
    first = text.splitlines()[0] if text else ""
    prefix = f"# {doc_id} — "
    if not first.startswith(prefix) or not first[len(prefix):].strip():
        raise CatalogError(f"{path.name}: heading no canónico (esperado '# {doc_id} — Título')")
    return first[len(prefix):].strip()


def _collect(governance: Path, kind: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    candidates = [
        path for path in governance.rglob("*.md")
        if path.is_file() and path.name.startswith(f"{kind}-") and path.suffix == ".md"
    ]
    canonical: list[tuple[Path, re.Match[str]]] = []
    for path in candidates:
        match = DECISION_FILE[kind].fullmatch(path.name)
        if match is None:
            raise CatalogError(f"{path.name}: filename de decisión no canónico")
        canonical.append((path, match))
    for path, filename_match in sorted(canonical, key=lambda item: item[0].name):
        doc_id = filename_match.group(1)
        if doc_id in seen:
            raise CatalogError(f"{doc_id}: número duplicado ({seen[doc_id]} y {path.name})")
        seen[doc_id] = path.name
        text = path.read_text(encoding="utf-8")
        row = {
            "id": doc_id,
            "title": _heading_title(text, doc_id, path),
            "estado": field(text, "Estado", path=path, required=True),
            "owner": field(text, "Owner", path=path, required=True),
            "fecha": field(text, "Fecha", path=path, required=True),
            "resolved_by": field(text, "resolved_by", path=path),
            "path": path.relative_to(governance.parent).as_posix(),
        }
        if not DATE.fullmatch(row["fecha"]):
            raise CatalogError(f"{doc_id}: Fecha inválida {row['fecha']!r}")
        try:
            date.fromisoformat(row["fecha"])
        except ValueError as exc:
            raise CatalogError(f"{doc_id}: Fecha inválida {row['fecha']!r}") from exc
        for key in ("title", "owner", "resolved_by"):
            if "|" in row[key] or "`" in row[key]:
                raise CatalogError(f"{doc_id}: {key} contiene caracteres de tabla")
        rows.append(row)
    return rows


def collect_adrs(governance: Path) -> list[dict[str, str]]:
    rows = _collect(governance, "ADR")
    for row in rows:
        if row["estado"] not in ADR_STATES:
            raise CatalogError(f"{row['id']}: Estado fuera del dominio {row['estado']!r}")
    return rows


def collect_rfcs(governance: Path) -> list[dict[str, str]]:
    rows = _collect(governance, "RFC")
    for row in rows:
        if row["estado"] not in RFC_STATES:
            raise CatalogError(f"{row['id']}: Estado fuera del dominio {row['estado']!r}")
        if row["estado"] == "Ratificado" and not row["resolved_by"]:
            raise CatalogError(f"{row['id']}: Ratificado exige resolved_by")
        if row["resolved_by"] and re.fullmatch(
            r"ADR-[0-9]{4}(?:,\s*ADR-[0-9]{4})*",
            row["resolved_by"],
        ) is None:
            raise CatalogError(f"{row['id']}: resolved_by no canónico")
    return rows


def render_adr_catalog(rows: list[dict[str, str]]) -> str:
    counts = {state: sum(1 for row in rows if row["estado"] == state) for state in ADR_STATES}
    lines = [
        "# ADR Catalog",
        "",
        "> **Proyección generada; no editar.** Fuente: `governance/ADR-NNNN-*.md`. "
        "Regenerar con `python3 tools/publishing/compile_catalogs.py --write`.",
        "",
        f"**Total:** {len(rows)} · **Aceptados:** {counts['Aceptado']} · "
        f"**Propuestos:** {counts['Propuesto']} · **Derogados:** {counts['Derogado']}",
        "",
        "| ID | Título | Estado | Owner | Fecha | Path |",
        "|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {row['id']} | {row['title']} | {row['estado']} | {row['owner']} | "
        f"{row['fecha']} | `{row['path']}` |"
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def render_rfc_catalog(rows: list[dict[str, str]]) -> str:
    ratified = sum(1 for row in rows if row["estado"] == "Ratificado")
    proposed = sum(1 for row in rows if row["estado"] == "Propuesto")
    lines = [
        "# RFC Catalog",
        "",
        "> **Proyección generada; no editar.** Fuente: `governance/RFC-NNNN-*.md`. "
        "Regenerar con `python3 tools/publishing/compile_catalogs.py --write`.",
        "",
        f"**Total:** {len(rows)} · **Ratificados:** {ratified} · **Propuestos:** {proposed}",
        "",
        "| ID | Pregunta | Estado | Owner | Resuelto por |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {row['id']} | {row['title']} | {row['estado']} | {row['owner']} | "
        f"{row['resolved_by'] or '—'} |"
        for row in rows
    ]
    return "\n".join(lines) + "\n"


def _atomic_write(target: Path, content: str) -> None:
    fd, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _write_projections(projections: dict[Path, str]) -> None:
    lock = next(iter(projections)).parent / ".catalogs.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise CatalogError("otra compilación de catálogos mantiene el lock") from exc
    os.close(descriptor)
    originals = {
        target: target.read_text(encoding="utf-8") if target.exists() else None
        for target in projections
    }
    try:
        try:
            for target, expected in projections.items():
                _atomic_write(target, expected)
        except BaseException:
            for target, previous in originals.items():
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    _atomic_write(target, previous)
            raise
    finally:
        lock.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verificar sin escribir (default)")
    mode.add_argument("--write", action="store_true", help="regenerar proyecciones")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    governance = ROOT / "governance"
    try:
        projections = {
            governance / "ADR_CATALOG.md": render_adr_catalog(collect_adrs(governance)),
            governance / "RFC_CATALOG.md": render_rfc_catalog(collect_rfcs(governance)),
        }
    except (OSError, CatalogError) as exc:
        print(f"[catalogs] FAIL: {exc}")
        return 1
    if not args.write:
        for target, expected in projections.items():
            actual = target.read_text(encoding="utf-8") if target.exists() else ""
            if actual != expected:
                print(f"[catalogs] FAIL: proyección desactualizada: {target.name}")
                return 1
        print("[catalogs] OK: catálogos ADR/RFC coinciden con sus documentos")
        return 0
    try:
        _write_projections(projections)
    except (OSError, CatalogError) as exc:
        print(f"[catalogs] FAIL: {exc}")
        return 1
    for target in projections:
        print(f"[catalogs] generado {target.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
