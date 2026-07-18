"""Adapter SDD (borde de delivery) — ADR-0003. Sin dependencias externas."""
from edaios_sdd_adapter.adapter import (
    DRAFTS_SUBDIR,
    DraftGuardError,
    FRONTIER_CONSTRAINTS,
    build_context_bundle,
    bundle_digest,
    export_context_bundle,
    ingest_artifact,
    assert_draft_promotable,
    draft_conflict_candidates,
    seed_constitution_text,
)

__version__ = "3.1.0"

__all__ = [
    "__version__",
    "DRAFTS_SUBDIR", "DraftGuardError", "FRONTIER_CONSTRAINTS",
    "build_context_bundle", "bundle_digest", "export_context_bundle",
    "assert_draft_promotable", "draft_conflict_candidates", "ingest_artifact",
    "seed_constitution_text",
]
