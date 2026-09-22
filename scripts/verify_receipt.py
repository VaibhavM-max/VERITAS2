"""Verify a receipt JSON file offline."""

import argparse
import json

from ledger.crypto import verify_signature
from ledger.evidence_ledger import EvidenceReceipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--public-key", required=True)
    args = parser.parse_args()
    with open(args.receipt, encoding="utf-8") as receipt_file:
        receipt = EvidenceReceipt(**json.load(receipt_file))
    valid = verify_signature(args.public_key, receipt.serialize(exclude_signature=True), receipt.signature)
    print("VALID" if valid else "INVALID")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
