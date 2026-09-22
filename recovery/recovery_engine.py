"""Bounded recovery decisions for failed verification."""

from verifier.failure_classifier import Failure, FailureType


class RecoveryEngine:
    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries

    def recover(self, failure: Failure, step: dict, trace: dict, context: dict) -> dict:
        retries = trace.get("retry_count", 0)
        if failure.type in {FailureType.NO_EFFECT, FailureType.PARTIAL, FailureType.WRONG_VALUE} and retries < self.max_retries:
            return {"success": False, "should_escalate": False, "retry": True}
        return {"success": False, "should_escalate": step.get("reversibility") == "checkable-irreversible" or failure.type == FailureType.COLLATERAL,
                "retry": False, "reason": failure.type.value}
