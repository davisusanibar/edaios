"""EDAIOS Core conformance contracts; no consumer runtime is installed."""

from .attachment import (
    AttachmentError,
    initialize_attachment,
    prepare_upgrade,
    rollback_attachment,
    validate_attachment,
    validate_federation_mounts,
    write_upgrade_plan,
)
from .profiles import (
    PolicyWeakeningError,
    ProfileError,
    ProfileRegistry,
    diff_policy,
    explain_failure,
    load_policy,
    require_monotonic_policy,
)
from .schemas import (
    SchemaError,
    SchemaRegistry,
    ValidationError,
    canonical_digest,
    canonical_json,
    read_json,
)

__version__ = "3.1.0"
__all__ = [
    "AttachmentError", "PolicyWeakeningError", "ProfileError", "ProfileRegistry",
    "SchemaError", "SchemaRegistry", "ValidationError", "canonical_digest",
    "canonical_json", "diff_policy", "explain_failure", "initialize_attachment",
    "load_policy", "prepare_upgrade", "read_json", "require_monotonic_policy",
    "rollback_attachment", "validate_attachment", "validate_federation_mounts",
    "write_upgrade_plan",
]
