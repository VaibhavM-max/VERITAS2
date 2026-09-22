"""Independent verifier that never uses the executor's claimed result as proof."""

from datetime import datetime, timezone
import uuid

from ledger.evidence_ledger import EvidenceLedger, EvidenceReceipt
from verifier.checker import SQLChecker


class IndependentVerifier:
    def __init__(self, read_only_db_path: str, evidence_ledger: EvidenceLedger) -> None:
        self.checker = SQLChecker(read_only_db_path)
        self.ledger = evidence_ledger

    def verify_step(self, step: dict, trace: dict) -> dict:
        context = trace["context"]
        kind = step.get("checker_type")
        if kind == "eligibility":
            result = self.checker.check_eligibility(context["customer_id"], context["request_id"])
        elif kind == "refund_exists":
            result = self.checker.check_refund_exists(context["refund_id"], context["amount"])
        elif kind == "email_outbox":
            rows = self.checker.execute_query("SELECT status FROM email_outbox WHERE email_id = ?", (trace["result"]["email_id"],))
            from verifier.checker import CheckerResult
            result = CheckerResult("QUEUED", rows[0][0] if rows else None, ["email_outbox"],
                                   [{"check": "email queued", "result": "PASS" if rows and rows[0][0] == "QUEUED" else "FAIL"}],
                                   bool(rows and rows[0][0] == "QUEUED"))
        else:
            from verifier.checker import CheckerResult
            result = CheckerResult(None, None, [], [], False)
        verdict = "VERIFIED" if result.passed else "MISMATCH"
        receipt = self.ledger.append(EvidenceReceipt(
            receipt_id=f"RCP-{uuid.uuid4().hex[:8].upper()}", step_id=step["step_id"],
            operation_id=trace["operation_id"], agent_id="VERITAS-VERIFIER",
            claimed_action=step["description"], systems_checked=result.systems,
            postconditions_evaluated=result.checks, result=verdict,
            timestamp=datetime.now(timezone.utc).isoformat(),
            checked_values={"expected": result.expected, "actual": result.actual},
            trust_level="hard" if result.passed else "none"))
        return {"passed": result.passed, "verdict": verdict, "receipt": receipt}
