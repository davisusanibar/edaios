"""Checksum, SBOM y provenance deterministas con biblioteca estándar."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping
import json
import zipfile


CHECKSUM_SCHEMA = "edaios.checksums/v1"
PROVENANCE_SCHEMA = "edaios.local-provenance/v1"
BUILDER_ID = "edaios.local-stdlib-wheel-builder/v1"
CLAIM_BOUNDARY = (
    "Integridad reproducible local; no prueba firma, identidad, publicación "
    "remota ni procedencia fuera de los materiales declarados."
)


class SupplyChainError(ValueError):
    """Los artefactos de supply chain son incompletos o no verificables."""


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _safe_archive_name(name: str) -> str:
    pure = PurePosixPath(name)
    if not name or pure.is_absolute() or ".." in pure.parts:
        raise SupplyChainError(f"entrada insegura en el artefacto: {name!r}")
    return pure.as_posix()


def _zip_inventory(subject: Path) -> list[dict[str, object]]:
    try:
        archive = zipfile.ZipFile(subject)
    except (OSError, zipfile.BadZipFile) as exc:
        raise SupplyChainError(f"subject no es ZIP verificable: {subject}") from exc
    with archive:
        entries: list[dict[str, object]] = []
        seen: set[str] = set()
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            if info.is_dir():
                continue
            name = _safe_archive_name(info.filename)
            if name in seen:
                raise SupplyChainError(f"entrada ZIP duplicada: {name}")
            seen.add(name)
            content = archive.read(info)
            entries.append(
                {
                    "type": "file",
                    "name": name,
                    "bom-ref": f"file:{name}",
                    "hashes": [
                        {"alg": "SHA-256", "content": sha256(content).hexdigest()}
                    ],
                    "properties": [
                        {"name": "edaios:size", "value": str(len(content))}
                    ],
                }
            )
    return entries


def _material_rows(materials: Mapping[str, str | Path] | None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, source in sorted((materials or {}).items()):
        safe_name = _safe_archive_name(str(name))
        path = Path(source)
        if not path.is_file():
            raise SupplyChainError(f"material ausente: {safe_name} -> {path}")
        rows.append({"path": safe_name, "digest": sha256_file(path)})
    return rows


def _checksum_text(files: Iterable[Path]) -> bytes:
    rows = []
    for path in sorted(files, key=lambda item: item.name):
        rows.append(f"{sha256_file(path).removeprefix('sha256:')}  {path.name}")
    return (("\n".join(rows)) + "\n").encode("ascii")


def build_supply_chain_artifacts(
    subject: str | Path,
    output_dir: str | Path,
    *,
    version: str,
    materials: Mapping[str, str | Path] | None = None,
    builder_id: str = BUILDER_ID,
) -> dict[str, Path]:
    """Genera sidecars estables para un wheel ya construido.

    No usa reloj, host, usuario ni red. Por tanto, los mismos bytes, versión y
    materiales producen exactamente los mismos sidecars.
    """
    subject = Path(subject).resolve()
    output = Path(output_dir).resolve()
    if not subject.is_file():
        raise SupplyChainError(f"subject ausente: {subject}")
    if not version.strip() or not builder_id.strip():
        raise SupplyChainError("version y builder_id son obligatorios")
    output.mkdir(parents=True, exist_ok=True)

    subject_digest = sha256_file(subject)
    components = _zip_inventory(subject)
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "library",
                "name": "edaios-core",
                "version": version,
                "bom-ref": f"pkg:pypi/edaios-core@{version}",
                "hashes": [
                    {"alg": "SHA-256", "content": subject_digest.split(":", 1)[1]}
                ],
            },
            "properties": [
                {"name": "edaios:subject", "value": subject.name},
                {"name": "edaios:claim-boundary", "value": CLAIM_BOUNDARY},
            ],
        },
        "components": components,
    }
    provenance = {
        "schema": PROVENANCE_SCHEMA,
        "builder": {"id": builder_id, "execution": "local-stdlib"},
        "build": {
            "core_version": version,
            "network_required": False,
            "reproducible": True,
        },
        "subject": {
            "name": subject.name,
            "digest": subject_digest,
            "size": subject.stat().st_size,
        },
        "materials": _material_rows(materials),
        "claims": {
            "signature": "absent",
            "publication": "not-performed",
            "boundary": CLAIM_BOUNDARY,
        },
    }

    sbom_path = output / f"{subject.name}.sbom.json"
    provenance_path = output / f"{subject.name}.provenance.json"
    checksum_path = output / f"{subject.name}.sha256"
    sbom_path.write_bytes(_canonical_json(sbom))
    provenance_path.write_bytes(_canonical_json(provenance))
    checksum_path.write_bytes(
        _checksum_text((subject, sbom_path, provenance_path))
    )
    return {
        "subject": subject,
        "checksum": checksum_path,
        "sbom": sbom_path,
        "provenance": provenance_path,
    }


def _load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SupplyChainError(f"{label} no es JSON válido: {path}") from exc
    if not isinstance(value, dict):
        raise SupplyChainError(f"{label} debe ser un objeto")
    return value


def _verify_checksums(checksum_path: Path, files: Mapping[str, Path]) -> None:
    try:
        lines = checksum_path.read_text(encoding="ascii").splitlines()
    except OSError as exc:
        raise SupplyChainError(f"checksum ilegible: {checksum_path}") from exc
    declared: dict[str, str] = {}
    for line in lines:
        digest, separator, name = line.partition("  ")
        if not separator or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise SupplyChainError(f"línea checksum inválida: {line!r}")
        if name in declared:
            raise SupplyChainError(f"checksum duplicado: {name}")
        declared[name] = digest
    if set(declared) != set(files):
        raise SupplyChainError("checksum no cubre exactamente subject, SBOM y provenance")
    for name, path in files.items():
        if sha256_file(path) != f"sha256:{declared[name]}":
            raise SupplyChainError(f"tampering detectado por checksum: {name}")


def verify_supply_chain_artifacts(
    subject: str | Path,
    checksum: str | Path,
    sbom: str | Path,
    provenance: str | Path,
    *,
    materials: Mapping[str, str | Path] | None = None,
) -> dict[str, object]:
    """Verifica bytes y coherencia semántica de los sidecars locales."""
    subject = Path(subject).resolve()
    checksum = Path(checksum).resolve()
    sbom = Path(sbom).resolve()
    provenance = Path(provenance).resolve()
    files = {subject.name: subject, sbom.name: sbom, provenance.name: provenance}
    if len(files) != 3:
        raise SupplyChainError("nombres de sidecars colisionan")
    _verify_checksums(checksum, files)

    subject_digest = sha256_file(subject)
    sbom_data = _load_object(sbom, "SBOM")
    if sbom_data.get("bomFormat") != "CycloneDX" or sbom_data.get("specVersion") != "1.5":
        raise SupplyChainError("SBOM fuera del contrato CycloneDX 1.5")
    try:
        component = sbom_data["metadata"]["component"]
        hashes = {row["alg"]: row["content"] for row in component["hashes"]}
    except (KeyError, TypeError) as exc:
        raise SupplyChainError("SBOM sin subject tipado") from exc
    if hashes.get("SHA-256") != subject_digest.split(":", 1)[1]:
        raise SupplyChainError("SBOM no corresponde al subject")
    if sbom_data.get("components") != _zip_inventory(subject):
        raise SupplyChainError("inventario SBOM no corresponde a las entradas del wheel")

    provenance_data = _load_object(provenance, "provenance")
    if provenance_data.get("schema") != PROVENANCE_SCHEMA:
        raise SupplyChainError("schema de provenance no soportado")
    expected_subject = {
        "name": subject.name,
        "digest": subject_digest,
        "size": subject.stat().st_size,
    }
    if provenance_data.get("subject") != expected_subject:
        raise SupplyChainError("provenance no corresponde al subject")
    claims = provenance_data.get("claims", {})
    if claims != {
        "signature": "absent",
        "publication": "not-performed",
        "boundary": CLAIM_BOUNDARY,
    }:
        raise SupplyChainError("provenance eleva o altera la frontera de claims")
    if materials is not None and provenance_data.get("materials") != _material_rows(materials):
        raise SupplyChainError("materiales de provenance no coinciden con las fuentes")

    return {
        "status": "ok",
        "subject": subject.name,
        "digest": subject_digest,
        "components": len(sbom_data.get("components", [])),
        "signature": "absent",
        "publication": "not-performed",
    }
