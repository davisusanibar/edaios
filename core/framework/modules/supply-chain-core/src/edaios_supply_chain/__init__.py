"""Supply chain local y reproducible para artefactos EDAIOS Core.

Los digests prueban integridad de bytes dentro del scope local. No representan
firma, identidad, publicación remota ni un nivel SLSA.
"""

from .artifacts import (
    SupplyChainError,
    build_supply_chain_artifacts,
    sha256_file,
    verify_supply_chain_artifacts,
)

__version__ = "3.1.0"

__all__ = [
    "__version__",
    "SupplyChainError",
    "build_supply_chain_artifacts",
    "sha256_file",
    "verify_supply_chain_artifacts",
]
