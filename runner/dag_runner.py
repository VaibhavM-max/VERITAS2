"""Deterministic sequential DAG runner with an enforced BLOCKED state."""

from enum import Enum
import uuid
from datetime import datetime, timezone

from ledger.evidence_ledger import EvidenceReceipt
from verifier.failure_classifier import FailureClassifier


class StepState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class DAGRunner:
    def __init__(self, executor, verifier, recovery_engine) -> None:
        self.executor = executor
        self.verifier = verifier
        self.recovery = recovery_engine
        self.failure_classifier = FailureClassifier()
        self.seen_idempotency_keys: set[str] = set()

    def run_plan(self, plan: dict) -> dict:
        states = {step["step_id"]: StepState.PENDING for step in plan["steps"]}
        completed: list[str] = []
        evidence = []
        for index, step in enumerate(plan["steps"]):
            step_id = step["step_id"]
            if any(states[previous["step_id"]] != StepState.VERIFIED for previous in plan["steps"][:index]):
                states[step_id] = StepState.BLOCKED
                return {"status": "PARTIAL", "completed_steps": completed, "failed_step": step_id,
                        "failure": {"type": "BLOCKED", "signal": "upstream_not_verified"}, "evidence_log": evidence,
                        "states": states}
            states[step_id] = StepState.RUNNING
            trace = self.executor.execute_step(step, plan["context"])
            if trace["idempotency_key"] in self.seen_idempotency_keys:
                states[step_id] = StepState.FAILED
                return {"status": "FAILED", "completed_steps": completed, "failed_step": step_id,
                        "failure": {"type": "DUPLICATE", "signal": "idempotency_violation"}, "evidence_log": evidence,
                        "states": states}
            self.seen_idempotency_keys.add(trace["idempotency_key"])
            verification = self.verifier.verify_step(step, trace)
            evidence.append(verification["receipt"])
            if not verification["passed"]:
                states[step_id] = StepState.FAILED
                failure = self.failure_classifier.classify({}, verification["receipt"].checked_values.get("actual") or {}, trace["declared_write_set"], trace["idempotency_key"], self.seen_idempotency_keys)
                return {"status": "ESCALATED" if step.get("reversibility") == "checkable-irreversible" else "PARTIAL",
                        "completed_steps": completed, "failed_step": step_id,
                        "failure": {"type": failure.type.value, "signal": failure.signal}, "evidence_log": evidence,
                        "states": states}
            states[step_id] = StepState.VERIFIED
            completed.append(step_id)
        return {"status": "COMPLETE", "completed_steps": completed, "evidence_log": evidence, "states": states}
