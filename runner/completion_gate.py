"""Evidence-derived final status."""

from enum import Enum


class FinalStatus(Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"


class CompletionGate:
    def compute_status(self, execution_result: dict, expected_step_count: int | None = None) -> dict:
        expected = expected_step_count or len(execution_result.get("states", execution_result.get("completed_steps", [])))
        completed = execution_result.get("completed_steps", [])
        status = execution_result.get("status")
        if status == "COMPLETE" and len(completed) == expected and all(receipt.result == "VERIFIED" for receipt in execution_result.get("evidence_log", [])):
            final = FinalStatus.COMPLETE.value
        elif status == "ESCALATED":
            final = FinalStatus.ESCALATED.value
        elif status == "FAILED":
            final = FinalStatus.FAILED.value
        else:
            final = FinalStatus.PARTIAL.value
        return {**execution_result, "final_status": final}
