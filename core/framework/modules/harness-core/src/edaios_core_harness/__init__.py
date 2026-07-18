"""EDAIOS Core Harness: local enforcement without implicit authority."""

from .core import ContractError, CoreHarness, HarnessError, ReceiptError
from .receipts import (
    INTEGRITY_CLAIM,
    create_approval_receipt,
    create_evidence_receipt,
    verify_approval_receipt,
    verify_evidence_receipt,
)

__version__ = "3.1.0"
__all__ = [
    "ContractError", "CoreHarness", "HarnessError", "INTEGRITY_CLAIM",
    "ReceiptError", "create_approval_receipt", "create_evidence_receipt",
    "verify_approval_receipt", "verify_evidence_receipt",
]
