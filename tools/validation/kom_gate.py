#!/usr/bin/env python3
"""Ejecuta KOM-VR-01..11 sobre Core y federación gobernada explícita.

Core usa el namespace global ``edaios.core``. Los corpus externos solo ingresan
mediante un documento ``--mounts`` conforme: cada mount debe estar ligado a su
attachment, autoridad, root autorizado y digests. Las rutas declaradas en
``deriva_de`` se resuelven a exactamente un KO y se normalizan a su id antes de
validar relaciones.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
for _module in (
    "core/framework/modules/ess-core/src",
    "core/framework/modules/conformance-core/src",
):
    _module_path = str(REPOSITORY_ROOT / _module)
    if _module_path not in sys.path:
        sys.path.insert(0, _module_path)

from edaios_conformance import validate_federation_mounts
from edaios_core.knowledge import (
    KnowledgeMount,
    iter_mount_files,
    validate_knowledge_object,
)


REQUIRED = {
    "id", "tipo", "titulo", "version", "estado", "autoridad", "idioma",
    "owner", "deriva_de",
}
SEMVER = re.compile(r"\d+\.\d+\.\d+")
CORE_NAMESPACE = "edaios.core"
GOVERNANCE_FILE = re.compile(r"(ADR|RFC)-([0-9]{4})-[a-z0-9-]+\.md")
HEADING = re.compile(r"^#\s+((?:ADR|RFC)-[0-9]{4})\s+[—-]\s+(.+)$", re.MULTILINE)
META_LINE = re.compile(r"^\*\*([^*]+):\*\*\s*(.+)$", re.MULTILINE)
# Filas backticked de primera columna, con guion bajo permitido (las relaciones
# como derives_from lo usan); el parseo se acota por sección (ADR-0018).
ONTOLOGY_ROW = re.compile(r"^\|\s*`([A-Za-z_][A-Za-z0-9_]*)`\s*\|", re.MULTILINE)
ONTOLOGY_SECTION = re.compile(
    r"^## (Entidades|Relaciones)\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL
)
DERIVA_PROSA = re.compile(r"^\*\*Deriva de:\*\*\s*(.+)$", re.MULTILINE)
PROSA_TOKEN = re.compile(r"`([^`]+\.md)`(\s*\(histórico[^)]*\))?")


@dataclass
class KnowledgeObject:
    namespace: str
    scope: Path
    path: Path
    meta: dict[str, object]
    body: str
    specialized: bool = False
    relations: dict[str, list[str]] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return str(self.meta.get("id", "")).strip()

    @property
    def global_id(self) -> str:
        return f"{self.namespace}:{self.id}"

    @property
    def tipo(self) -> str:
        return str(self.meta.get("tipo", "")).strip()

    @property
    def authority(self) -> str:
        return str(self.meta.get("autoridad", "")).strip()

    @property
    def state(self) -> str:
        return str(self.meta.get("estado", "")).strip()


@dataclass
class Rule:
    id: str
    checked: int = 0
    errors: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.errors.append(message)


def scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter_text(text: str) -> tuple[dict[str, object], str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("front matter truncado: falta delimitador de cierre")
    meta: dict[str, object] = {}
    seen: set[str] = set()
    active: str | None = None
    for raw in lines[1:end]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and active:
            current = meta.setdefault(active, [])
            if not isinstance(current, list):
                return {}, ""
            current.append(scalar(stripped[2:]))
            continue
        if raw[:1].isspace():
            # El contrato interoperable de esta representación es plano. Una
            # estructura anidada no puede ignorarse silenciosamente.
            raise ValueError("front matter anidado no soportado")
        key, sep, value = raw.partition(":")
        if not sep:
            raise ValueError(f"línea de front matter inválida: {raw!r}")
        key = key.strip()
        if key in seen:
            raise ValueError(f"front matter contiene clave duplicada: {key}")
        seen.add(key)
        value = value.strip()
        if value:
            meta[key] = scalar(value)
            active = None
        else:
            meta[key] = []
            active = key
    body = "\n".join(lines[end + 1:]).strip()
    return meta, body


def governance_ko(path: Path, namespace: str, scope: Path) -> KnowledgeObject | None:
    match = GOVERNANCE_FILE.fullmatch(path.name)
    if not match:
        return None
    text = path.read_text(encoding="utf-8")
    heading = HEADING.search(text)
    if not heading or heading.group(1) != path.name[:8]:
        return KnowledgeObject(namespace, scope, path, {}, "", specialized=True)
    fields = {key.strip().casefold(): value.strip() for key, value in META_LINE.findall(text)}
    kind = match.group(1)
    derives = fields.get("deriva de", "Foundation")
    meta: dict[str, object] = {
        "id": heading.group(1),
        "tipo": kind,
        "titulo": heading.group(2).strip(),
        "version": "1.0.0",
        "estado": fields.get("estado", ""),
        "autoridad": "Core",
        "idioma": "es",
        "owner": fields.get("owner", ""),
        "deriva_de": derives,
    }
    relations: dict[str, list[str]] = {"derives_from": [derives]}
    resolved = fields.get("resolved_by") or fields.get("resuelto por")
    if resolved:
        relations["references"] = re.findall(r"ADR-[0-9]{4}", resolved)
    return KnowledgeObject(namespace, scope, path, meta, text.strip(), True, relations)


def relation_values(meta: dict[str, object]) -> dict[str, list[str]]:
    relations: dict[str, list[str]] = {}
    derives = meta.get("deriva_de")
    if isinstance(derives, str) and derives.strip():
        relations["derives_from"] = [derives.strip()]
    raw = meta.get("relaciones", [])
    items = raw if isinstance(raw, list) else [raw]
    for item in items:
        if not isinstance(item, str):
            continue
        name, sep, target = item.replace("=", ":", 1).partition(":")
        if sep and name.strip() and target.strip():
            relations.setdefault(name.strip(), []).append(target.strip())
    return relations


def markdown_ko(path: Path, namespace: str, scope: Path) -> KnowledgeObject | None:
    parsed = parse_frontmatter_text(path.read_text(encoding="utf-8"))
    if parsed is None:
        return None
    meta, body = parsed
    if "id" not in meta and "tipo" not in meta:
        return None
    scalar_meta = {
        key: str(value)
        for key, value in meta.items()
        if isinstance(value, str)
    }
    validate_knowledge_object(scalar_meta, body, source=str(path))
    return KnowledgeObject(
        namespace, scope, path, meta, body, False, relation_values(meta)
    )


def scan_scope(scope: Path, namespace: str, *, core_scope: bool) -> list[KnowledgeObject]:
    objects: list[KnowledgeObject] = []
    roots: Iterable[Path]
    if core_scope:
        roots = (
            scope / "core" / "foundation",
            scope / "core" / "framework" / "docs",
        )
    else:
        roots = (scope,)
    seen_paths: set[Path] = set()
    for base in roots:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            ko = markdown_ko(path, namespace, scope)
            if ko is not None:
                objects.append(ko)
    governance = scope / "governance"
    if governance.is_dir():
        for path in sorted(governance.rglob("*.md")):
            ko = governance_ko(path, namespace, scope)
            if ko is not None:
                objects.append(ko)
    return objects


def scan_federated_mount(mount: dict[str, str]) -> list[KnowledgeObject]:
    """Recorre un corpus validado sin seguir symlinks ni ampliar su scope."""
    normalized = KnowledgeMount.from_value(mount)
    scope = normalized.authorized_root
    if scope is None:  # KnowledgeMount.from_value ya lo impide; defensa local.
        raise ValueError(f"{normalized.namespace}: authorized_root ausente")
    objects: list[KnowledgeObject] = []
    governance = normalized.path / "governance"
    for path in iter_mount_files(normalized, normalized.path, suffix=".md"):
        ko = markdown_ko(path, normalized.namespace, scope)
        if ko is None and path.parent == governance:
            ko = governance_ko(path, normalized.namespace, scope)
        if ko is not None:
            if ko.authority != normalized.authority_layer:
                raise ValueError(
                    f"{normalized.namespace}:{ko.id}: autoridad {ko.authority!r} "
                    f"no coincide con {normalized.authority_layer!r}"
                )
            owner = str(ko.meta.get("owner", ""))
            if owner not in normalized.allowed_owner_actor_ids:
                raise ValueError(
                    f"{normalized.namespace}:{ko.id}: owner {owner!r} no activo"
                )
            objects.append(ko)
    return objects


def load_federated_objects(mounts_path: str | Path) -> list[KnowledgeObject]:
    """Valida el contrato FederationMount antes de exponer bytes al gate KOM."""
    objects: list[KnowledgeObject] = []
    mounts = validate_federation_mounts(mounts_path)
    for mount in mounts:
        objects.extend(scan_federated_mount(mount))
    if validate_federation_mounts(mounts_path) != mounts:
        raise ValueError("federation mounts cambiaron durante el consumo KOM")
    return objects


def load_contracts(root: Path) -> tuple[dict[str, object], set[str]]:
    grammar_path = root / "core/framework/core/profiles/governance-grammar.json"
    grammar = json.loads(grammar_path.read_text(encoding="utf-8"))
    if grammar.get("schema") != "edaios.governance-grammar/v1":
        raise ValueError("schema de governance-grammar no soportado")
    patterns = grammar.get("id_patterns")
    mappings = grammar.get("state_mappings")
    if not isinstance(patterns, dict) or not isinstance(mappings, dict):
        raise ValueError("grammar incompleta: id_patterns/state_mappings")
    if patterns.get("RFC") != "^RFC-[0-9]{4}$":
        raise ValueError("RFC debe usar exactamente cuatro dígitos")
    ontology = (root / "core/foundation/ontology/EDAIOS_ONTOLOGY.md").read_text(encoding="utf-8")
    sections = {name: body for name, body in ONTOLOGY_SECTION.findall(ontology)}
    md_entities = set(ONTOLOGY_ROW.findall(sections.get("Entidades", "")))
    md_relations = set(ONTOLOGY_ROW.findall(sections.get("Relaciones", "")))
    if not md_entities or not md_relations:
        raise ValueError("tablas de Ontología (Entidades/Relaciones) no resolubles")
    declared = grammar.get("entities")
    if (
        not isinstance(declared, list)
        or not declared
        or len(declared) != len({str(item) for item in declared})
    ):
        raise ValueError("grammar incompleta: entities ausente o con duplicados (ADR-0018)")
    entities = {str(item) for item in declared}
    relations = grammar.get("relations")
    relation_keys = {str(key) for key in relations} if isinstance(relations, dict) else set()
    # Correspondencia bidireccional y por sección: el MD conserva la autoridad,
    # el JSON es el contrato ejecutable; cualquier deriva falla cerrado.
    for label, in_grammar, in_markdown in (
        ("entities", entities, md_entities),
        ("relations", relation_keys, md_relations),
    ):
        extra = sorted(in_grammar - in_markdown)
        missing = sorted(in_markdown - in_grammar)
        if extra or missing:
            raise ValueError(
                f"grammar.{label} y Ontología divergen: "
                f"solo-grammar={extra} solo-ontología={missing}"
            )
    return grammar, entities


def normalized_authority(grammar: dict[str, object], value: str) -> str:
    aliases = grammar.get("authority_aliases", {})
    if isinstance(aliases, dict):
        value = str(aliases.get(value, value))
    return value


def lifecycle_state(grammar: dict[str, object], ko: KnowledgeObject) -> str | None:
    mappings = grammar.get("state_mappings", {})
    kind = ko.tipo if ko.specialized else "KO"
    if not isinstance(mappings, dict) or not isinstance(mappings.get(kind), dict):
        return None
    return str(mappings[kind].get(ko.state, "")) or None


def resolve_target(
    raw: str,
    source: KnowledgeObject,
    by_global: dict[str, KnowledgeObject],
    by_path: dict[Path, KnowledgeObject],
    root_authorities: set[str],
) -> tuple[str | None, str | None]:
    if raw in root_authorities:
        return None, raw
    candidate = Path(raw)
    if "/" in raw or raw.endswith(".md"):
        resolved = candidate if candidate.is_absolute() else source.scope / candidate
        try:
            resolved = resolved.resolve()
            resolved.relative_to(source.scope.resolve())
        except (OSError, ValueError):
            return None, None
        target = by_path.get(resolved)
        return (target.global_id, None) if target else (None, None)
    if ":" in raw:
        namespace, local = raw.split(":", 1)
        key = f"{namespace}:{local}"
    else:
        key = f"{source.namespace}:{raw}"
    return (key, None) if key in by_global else (None, None)


def previous_state(root: Path, ko: KnowledgeObject, base: str = "HEAD") -> str | None:
    try:
        rel = ko.path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None
    proc = subprocess.run(
        ["git", "show", f"{base}:{rel}"], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if proc.returncode != 0:
        return None
    if ko.specialized:
        fields = {key.strip().casefold(): value.strip() for key, value in META_LINE.findall(proc.stdout)}
        return fields.get("estado")
    parsed = parse_frontmatter_text(proc.stdout)
    return str(parsed[0].get("estado", "")) if parsed else None


def matches_domain(token: str, ko: KnowledgeObject) -> bool:
    return token == "KO" or token == ko.tipo or token == ko.authority


def evaluate(root: Path, objects: list[KnowledgeObject], grammar: dict[str, object], entities: set[str], base: str = "HEAD") -> list[Rule]:
    rules = {f"KOM-VR-{number:02d}": Rule(f"KOM-VR-{number:02d}") for number in range(1, 12)}
    rules["DERIVA-PROSA"] = Rule("DERIVA-PROSA")
    foundation = (root / "core/foundation").resolve()
    patterns = {
        key: re.compile(str(value))
        for key, value in dict(grammar["id_patterns"]).items()
    }
    authority_order = [str(item) for item in grammar.get("authority_order", [])]
    authority_rank = {name: index for index, name in enumerate(authority_order)}
    root_authorities = {str(item) for item in grammar.get("root_authorities", [])}
    relation_contracts = grammar.get("relations", {})
    transitions = grammar.get("lifecycle_transitions", {})

    by_global: dict[str, KnowledgeObject] = {}
    by_path: dict[Path, KnowledgeObject] = {}
    local_seen: dict[tuple[str, str], Path] = {}
    for ko in objects:
        ko.meta["autoridad"] = normalized_authority(grammar, ko.authority)
        rules["KOM-VR-01"].checked += 1
        identity_pattern = patterns.get(ko.tipo) or patterns.get("KO")
        if not identity_pattern or not identity_pattern.fullmatch(ko.id):
            rules["KOM-VR-01"].fail(f"{ko.path}: id no canónico {ko.id!r}")
        local_key = (ko.namespace, ko.id)
        if local_key in local_seen:
            rules["KOM-VR-01"].fail(
                f"{ko.namespace}:{ko.id} duplicado en {local_seen[local_key]} y {ko.path}"
            )
        local_seen[local_key] = ko.path
        by_global[ko.global_id] = ko
        by_path[ko.path.resolve()] = ko

        rules["KOM-VR-02"].checked += 1
        if ko.tipo not in entities:
            rules["KOM-VR-02"].fail(f"{ko.global_id}: tipo {ko.tipo!r} fuera de Ontología")

        # Las referencias `*.md` de las líneas de prosa **Deriva de:** en
        # Foundation deben resolver (ruta relativa o nombre único) o estar
        # anotadas como históricas — y entonces no deben resolver (ADR-0018).
        if ko.path.resolve().is_relative_to(foundation):
            for prosa in DERIVA_PROSA.finditer(ko.body):
                rules["DERIVA-PROSA"].checked += 1
                for token, historic in PROSA_TOKEN.findall(prosa.group(1)):
                    if "/" in token:
                        # Ruta relativa a Foundation o al repositorio.
                        resolved = (foundation / token).is_file() or (root / token).is_file()
                    else:
                        resolved = len(list(foundation.rglob(token))) == 1
                    if historic and resolved:
                        rules["DERIVA-PROSA"].fail(
                            f"{ko.global_id}: referencia histórica resuelve a archivo vivo {token!r}"
                        )
                    elif not historic and not resolved:
                        rules["DERIVA-PROSA"].fail(
                            f"{ko.global_id}: referencia de prosa no resoluble {token!r}"
                        )

        rules["KOM-VR-03"].checked += 1
        missing = REQUIRED - set(ko.meta)
        if missing:
            rules["KOM-VR-03"].fail(f"{ko.global_id}: faltan {sorted(missing)}")
        if not SEMVER.fullmatch(str(ko.meta.get("version", ""))):
            rules["KOM-VR-03"].fail(f"{ko.global_id}: version no semver")
        if ko.meta.get("idioma") != "es":
            rules["KOM-VR-03"].fail(f"{ko.global_id}: idioma normativo no es")
        if not ko.body.strip():
            rules["KOM-VR-03"].fail(f"{ko.global_id}: cuerpo vacío")
        # La presencia en un scope Git explícito materializa el historial de la
        # ruta; un mount fuera de Git no puede reclamar historial gobernado.
        if not (ko.scope / ".git").exists():
            rules["KOM-VR-03"].fail(f"{ko.global_id}: historial Git no resoluble")

        rules["KOM-VR-04"].checked += 1
        if lifecycle_state(grammar, ko) not in set(grammar.get("ko_lifecycle", [])):
            rules["KOM-VR-04"].fail(f"{ko.global_id}: estado no mapeable {ko.state!r}")

    resolved_relations: dict[str, dict[str, list[str]]] = {}
    for ko in objects:
        resolved_relations[ko.global_id] = {}
        for relation, targets in ko.relations.items():
            for raw_target in targets:
                rules["KOM-VR-05"].checked += 1
                target_id, root_target = resolve_target(
                    raw_target, ko, by_global, by_path, root_authorities
                )
                if target_id is None and root_target is None:
                    rules["KOM-VR-05"].fail(
                        f"{ko.global_id}: {relation} no resuelve {raw_target!r}"
                    )
                    continue
                resolved_relations[ko.global_id].setdefault(relation, []).append(
                    target_id or root_target or ""
                )

                rules["KOM-VR-06"].checked += 1
                contract = relation_contracts.get(relation) if isinstance(relation_contracts, dict) else None
                if not isinstance(contract, dict):
                    rules["KOM-VR-06"].fail(f"{ko.global_id}: relación no tipada {relation!r}")
                else:
                    domains = [str(item) for item in contract.get("domain", [])]
                    ranges = [str(item) for item in contract.get("range", [])]
                    if not any(matches_domain(token, ko) for token in domains):
                        rules["KOM-VR-06"].fail(
                            f"{ko.global_id}: {relation} viola dominio {domains}"
                        )
                    if target_id and not any(
                        matches_domain(token, by_global[target_id]) for token in ranges
                    ):
                        rules["KOM-VR-06"].fail(
                            f"{ko.global_id}: {relation} → {target_id} viola rango {ranges}"
                        )
                    if root_target and relation != "derives_from":
                        rules["KOM-VR-06"].fail(
                            f"{ko.global_id}: solo derives_from admite sentinel de raíz"
                        )

                if relation == "derives_from":
                    rules["KOM-VR-07"].checked += 1
                    target_authority = root_target
                    if target_id:
                        target_authority = by_global[target_id].authority
                    source_rank = authority_rank.get(ko.authority)
                    target_rank = authority_rank.get(str(target_authority))
                    if source_rank is None or target_rank is None or target_rank > source_rank:
                        rules["KOM-VR-07"].fail(
                            f"{ko.global_id}: deriva hacia autoridad inferior {target_authority!r}"
                        )

                if relation == "governs":
                    rules["KOM-VR-08"].checked += 1
                    if target_id and ko.authority != "Foundation" and by_global[target_id].authority == "Foundation":
                        rules["KOM-VR-08"].fail(
                            f"{ko.global_id}: capa inferior gobierna {target_id} Foundation"
                        )

    # Las reglas sin una relación aplicable también fueron ejecutadas sobre el
    # corpus: se reporta cero aplicables, no una promesa de control futuro.
    rules["KOM-VR-08"].checked += sum(
        1 for ko in objects if "governs" not in ko.relations
    )

    for ko in objects:
        if ko.tipo in {"ADR", "Decision"}:
            rules["KOM-VR-09"].checked += 1
            targets = sum(resolved_relations.get(ko.global_id, {}).values(), [])
            has_adr = ko.tipo == "ADR" or any(
                target in by_global and by_global[target].tipo == "ADR" for target in targets
            )
            if not has_adr:
                rules["KOM-VR-09"].fail(f"{ko.global_id}: Decision estructural sin ADR")

        rules["KOM-VR-10"].checked += 1
        current = lifecycle_state(grammar, ko)
        old_raw = previous_state(root, ko, base)
        if old_raw:
            shadow = KnowledgeObject(
                ko.namespace, ko.scope, ko.path,
                {**ko.meta, "estado": old_raw}, ko.body, ko.specialized,
            )
            previous = lifecycle_state(grammar, shadow)
            allowed = transitions.get(previous, []) if isinstance(transitions, dict) else []
            if not previous or current not in allowed:
                rules["KOM-VR-10"].fail(
                    f"{ko.global_id}: transición inválida {previous!r} → {current!r}"
                )
        if current == "Derogado":
            inbound = any(
                ko.global_id in rels.get("supersedes", [])
                for rels in resolved_relations.values()
            )
            if not inbound:
                rules["KOM-VR-10"].fail(
                    f"{ko.global_id}: Derogado sin KO que lo supersedes"
                )

        rules["KOM-VR-11"].checked += 1
        explicit = resolved_relations.get(ko.global_id, {}).get("represents", [])
        explicit += resolved_relations.get(ko.global_id, {}).get("projects", [])
        if ko.tipo == "DerivedView" and len(explicit) != 1:
            rules["KOM-VR-11"].fail(
                f"{ko.global_id}: DerivedView representa {len(explicit)} KOs; requiere 1"
            )
        elif ko.tipo != "DerivedView" and explicit:
            rules["KOM-VR-11"].fail(
                f"{ko.global_id}: representación explícita solo válida para DerivedView"
            )

    return list(rules.values())


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--mounts", metavar="FEDERATION_MOUNTS_JSON",
        help=(
            "documento federation-mounts gobernado; no se aceptan "
            "mounts namespace=path autoafirmados"
        ),
    )
    parser.add_argument("--base", default="HEAD", help="commit base explícito para comparar estado previo")
    parser.add_argument("--head", default="WORKTREE", help="identificador documental del head evaluado")
    return parser


def main() -> int:
    parser = argument_parser()
    args = parser.parse_args()
    if args.base == args.head:
        parser.error("--base y --head no pueden ser iguales")
    root = Path(args.root).resolve()
    try:
        grammar, entities = load_contracts(root)
        objects = scan_scope(root, CORE_NAMESPACE, core_scope=True)
        if args.mounts:
            objects.extend(load_federated_objects(args.mounts))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] KOM-CONTRACT: {exc}")
        return 1

    rules = evaluate(root, objects, grammar, entities, args.base)
    for rule in rules:
        if rule.errors:
            for error in rule.errors:
                print(f"[FAIL] {rule.id}: {error}")
        else:
            print(f"[OK ] {rule.id}: {rule.checked} comprobaciones")
    errors = sum(len(rule.errors) for rule in rules)
    print(f"-- KOM-VR-01..11 + DERIVA-PROSA: {len(objects)} KOs · {errors} errores · 0 avisos --")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
