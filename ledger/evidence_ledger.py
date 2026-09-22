"""Append-only, signed evidence receipts with Merkle inclusion checks."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from typing import Any
import uuid

from ledger.crypto import load_keys_from_env, sha256_hash, sign_message, verify_signature
from ledger.merkle import MerkleAccumulator
from offline_queue import OfflineQueueManager


@dataclass
class EvidenceReceipt:
    receipt_id: str
    step_id: str
    operation_id: str
    agent_id: str
    claimed_action: str
    systems_checked: list[str]
    postconditions_evaluated: list[dict]
    result: str
    timestamp: str
    checked_values: dict[str, Any]
    signature: str | None = None
    merkle_root: str | None = None
    previous_hash: str | None = None
    trust_level: str = "hard"

    def to_dict(self) -> dict:
        return asdict(self)

    def serialize(self, exclude_signature: bool = False) -> bytes:
        payload = self.to_dict()
        if exclude_signature:
            payload["signature"] = None
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    def leaf_payload(self) -> bytes:
        payload = self.to_dict()
        payload["signature"] = None
        payload["merkle_root"] = None
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


class EvidenceLedger:
    def __init__(
        self,
        private_key_hex: str,
        public_key_hex: str,
        offline_queue: OfflineQueueManager | None = None,
    ) -> None:
        self.private_key = private_key_hex
        self.public_key = public_key_hex
        self.checkpoints: list[EvidenceReceipt] = []
        self.merkle_tree = MerkleAccumulator()
        self.ledger_id = f"VERITAS-LEDGER-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.offline_queue = offline_queue

    def append(self, receipt: EvidenceReceipt) -> EvidenceReceipt:
        receipt.previous_hash = (
            sha256_hash(self.checkpoints[-1].serialize()) if self.checkpoints else None
        )
        self.merkle_tree.add(sha256_hash(receipt.leaf_payload()))
        receipt.merkle_root = self.merkle_tree.root
        receipt.signature = sign_message(self.private_key, receipt.serialize(exclude_signature=True))
        self.checkpoints.append(receipt)
        if self.offline_queue is not None:
            self.offline_queue.enqueue_evidence_receipt(receipt.to_dict())
        return receipt

    def verify(self, receipt: EvidenceReceipt) -> bool:
        signature_valid = verify_signature(
            self.public_key, receipt.serialize(exclude_signature=True), receipt.signature
        )
        leaf_valid = self.merkle_tree.verify_inclusion(
            sha256_hash(receipt.leaf_payload()), receipt.merkle_root or ""
        )
        return signature_valid and leaf_valid and receipt in self.checkpoints

    def get_receipts(self) -> list[EvidenceReceipt]:
        return list(self.checkpoints)

    def get_receipt_by_id(self, receipt_id: str) -> EvidenceReceipt | None:
        return next((receipt for receipt in self.checkpoints if receipt.receipt_id == receipt_id), None)

    def get_checkpoint_count(self) -> int:
        return len(self.checkpoints)

    def export_proof_bundle(self) -> dict:
        return {
            "ledger_id": self.ledger_id,
            "public_key": self.public_key,
            "receipts": [receipt.to_dict() for receipt in self.checkpoints],
            "merkle_tree": self.merkle_tree.export(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }


def create_ledger_from_env() -> EvidenceLedger:
    private_key, public_key = load_keys_from_env()
    if not private_key or not public_key:
        raise ValueError("PRIVATE_KEY_HEX and PUBLIC_KEY_HEX must be set")
    return EvidenceLedger(private_key, public_key)
