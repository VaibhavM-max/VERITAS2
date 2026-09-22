from ledger.crypto import generate_keypair
from ledger.evidence_ledger import EvidenceLedger, EvidenceReceipt


def make_receipt() -> EvidenceReceipt:
    return EvidenceReceipt("R1", "S1", "OP1", "VERITAS", "check", ["db"],
                           [{"check": "exists", "result": "PASS"}], "VERIFIED",
                           "2026-09-22T00:00:00Z", {"actual": True})


def test_receipt_is_signed_and_tamper_evident() -> None:
    keys = generate_keypair()
    ledger = EvidenceLedger(keys["private_key"], keys["public_key"])
    receipt = ledger.append(make_receipt())
    assert ledger.verify(receipt)
    receipt.result = "MISMATCH"
    assert not ledger.verify(receipt)
