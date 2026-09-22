"""Export a proof bundle from a JSON ledger bundle."""

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Existing proof bundle JSON")
    parser.add_argument("--output", default="proof_bundle.json")
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as source:
        bundle = json.load(source)
    with open(args.output, "w", encoding="utf-8") as destination:
        json.dump(bundle, destination, indent=2)
    print(f"Exported {len(bundle.get('receipts', []))} receipts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
