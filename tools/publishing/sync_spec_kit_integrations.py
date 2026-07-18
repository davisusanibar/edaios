#!/usr/bin/env python3
"""Genera integraciones de agentes desde los comandos canonicos de EDAIOS.

Fuente: `.specify/commands/speckit.*.md`.
Derivados: Claude, Codex skills, Copilot prompts y preset distribuible.
`--check` no escribe y falla ante cualquier deriva — incluida la de mundo
cerrado: archivos huerfanos o apocrifos dentro del espacio de nombres
gestionado de cada superficie (F3.1). En modo escritura, los huerfanos del
espacio gestionado se eliminan (son derivados regenerables por definicion).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(os.environ.get("EDAIOS_REPO_ROOT") or Path(__file__).resolve().parents[2])
SOURCE_DIR = ROOT / ".specify" / "commands"
LOCK_PATH = ROOT / ".specify" / "integrations.lock.json"
SPEC_KIT_VERSION = "0.12.11"


def core_version() -> str:
    value = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise ValueError(f"VERSION no es SemVer estable: {value!r}")
    return value


def managed_files() -> set[Path]:
    """Todos los archivos REALES dentro del espacio de nombres gestionado.

    Cualquier archivo aqui que no este en `expected()` es un huerfano (su fuente
    ya no existe) o un apocrifo (nunca tuvo fuente): ambos son deriva.
    """
    found: set[Path] = set()
    found.update((ROOT / ".claude" / "commands").glob("speckit.*.md"))
    found.update((ROOT / ".github" / "prompts").glob("speckit.*.prompt.md"))
    for skill_dir in (ROOT / ".agents" / "skills").glob("speckit-*"):
        found.update(p for p in skill_dir.rglob("*") if p.is_file())
    preset_dir = (ROOT / "core" / "framework" / "extensions" / "sdd-adapter"
                  / "spec-kit" / "preset" / "commands")
    found.update(preset_dir.glob("*.md"))
    # extension/commands es superficie manual (edaios.*) que viaja en el bundle:
    # el espacio de nombres speckit.* alli nunca es legitimo.
    extension_dir = (ROOT / "core" / "framework" / "extensions" / "sdd-adapter"
                     / "spec-kit" / "extension" / "commands")
    found.update(extension_dir.glob("speckit.*.md"))
    return found


def parse_command(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: frontmatter ausente")
    try:
        raw, body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError(f"{path}: frontmatter sin cierre") from exc
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"{path}: linea invalida en frontmatter: {line}")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    required = {
        "id", "display_name", "description", "trigger",
        "short_description", "default_prompt",
    }
    missing = sorted(required - meta.keys())
    if missing:
        raise ValueError(f"{path}: faltan campos {', '.join(missing)}")
    if meta["id"] != path.stem:
        raise ValueError(
            f"{path}: id '{meta['id']}' no coincide con el nombre de archivo "
            f"'{path.stem}' — un id ajeno desplazaria al comando canonico")
    return meta, body.strip() + "\n"


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def rendered_files(meta: dict[str, str], body: str) -> dict[Path, str]:
    command_id = meta["id"]
    skill_name = command_id.replace(".", "-")
    marker = "<!-- GENERADO desde .specify/commands; no editar a mano. -->\n\n"
    description = f"{meta['description']} {meta['trigger']}"

    claude = (
        "---\n"
        f"description: {meta['description']}\n"
        "---\n\n"
        + marker + body
    )
    skill = (
        "---\n"
        f"name: {skill_name}\n"
        f"description: {description}\n"
        "---\n\n"
        + marker + body
    )
    openai = (
        "interface:\n"
        f"  display_name: {quoted(meta['display_name'])}\n"
        f"  short_description: {quoted(meta['short_description'])}\n"
        f"  default_prompt: {quoted(meta['default_prompt'])}\n"
    )
    copilot = (
        "---\n"
        "mode: agent\n"
        f"description: {quoted(meta['description'])}\n"
        "---\n\n"
        + marker + body
    )
    preset = claude

    return {
        ROOT / ".claude" / "commands" / f"{command_id}.md": claude,
        ROOT / ".agents" / "skills" / skill_name / "SKILL.md": skill,
        ROOT / ".agents" / "skills" / skill_name / "agents" / "openai.yaml": openai,
        ROOT / ".github" / "prompts" / f"{command_id}.prompt.md": copilot,
        ROOT / "core" / "framework" / "extensions" / "sdd-adapter" / "spec-kit"
        / "preset" / "commands" / f"{command_id}.md": preset,
    }


def expected() -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    lock_commands: dict[str, dict[str, object]] = {}
    sources = sorted(SOURCE_DIR.glob("speckit.*.md"))
    if not sources:
        raise ValueError("no hay comandos canonicos Spec Kit")
    stray = sorted(p.name for p in SOURCE_DIR.glob("*.md") if p not in sources)
    if stray:
        raise ValueError(
            "fuentes no gestionadas en .specify/commands/ (se esperan solo "
            f"speckit.*.md): {', '.join(stray)}")
    for source in sources:
        meta, body = parse_command(source)
        if meta["id"] in lock_commands:
            raise ValueError(f"id duplicado '{meta['id']}' en {source}")
        generated = rendered_files(meta, body)
        collisions = sorted(str(p) for p in generated if p in outputs)
        if collisions:
            raise ValueError(f"colision de derivados: {', '.join(collisions)}")
        outputs.update(generated)
        source_text = source.read_text(encoding="utf-8")
        lock_commands[meta["id"]] = {
            "source": source.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            "surfaces": sorted(p.relative_to(ROOT).as_posix() for p in generated),
        }
    lock = {
        "schema": "edaios.speckit.integrations/v1",
        "spec_kit_version": SPEC_KIT_VERSION,
        "source": f"edaios-core@v{core_version()}+spec-kit@v{SPEC_KIT_VERSION}",
        "generated_by": "tools/publishing/sync_spec_kit_integrations.py",
        "commands": lock_commands,
    }
    outputs[LOCK_PATH] = json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return outputs


def main() -> int:
    check = "--check" in sys.argv
    drift: list[str] = []
    try:
        outputs = expected()
    except ValueError as exc:
        print(f"[spec-kit-integrations] ERROR: {exc}")
        return 1
    for path, content in outputs.items():
        actual = path.read_text(encoding="utf-8") if path.exists() else None
        if actual == content:
            continue
        if check:
            drift.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    # Mundo cerrado: nada vive en el espacio gestionado sin fuente canonica.
    orphans = sorted(managed_files() - set(outputs))
    for orphan in orphans:
        rel = orphan.relative_to(ROOT).as_posix()
        if check:
            drift.append(f"{rel} (huerfano: sin fuente canonica)")
        else:
            orphan.unlink()
            print(f"[spec-kit-integrations] huerfano eliminado: {rel}")
            parent = orphan.parent
            skills_root = ROOT / ".agents" / "skills"
            while skills_root in parent.parents and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
    if drift:
        print("[spec-kit-integrations] DRIFT: " + ", ".join(drift))
        return 1
    mode = "verificadas" if check else "sincronizadas"
    print(f"[spec-kit-integrations] OK - integraciones {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
