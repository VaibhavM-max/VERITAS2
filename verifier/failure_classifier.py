"""Classify state mismatches before selecting recovery."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FailureType(Enum):
    NO_EFFECT = "NO_EFFECT"
    PARTIAL = "PARTIAL"
    WRONG_VALUE = "WRONG_VALUE"
    DUPLICATE = "DUPLICATE"
    COLLATERAL = "COLLATERAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class Failure:
    type: FailureType
    signal: str
    details: dict[str, Any]


class FailureClassifier:
    def classify(self, before_state: dict, after_state: dict, declared_write_set: set,
                 idempotency_key: str, seen_keys: set) -> Failure:
        if before_state == after_state:
            return Failure(FailureType.NO_EFFECT, "ghost_success", {"before": before_state, "after": after_state})
        if idempotency_key in seen_keys:
            return Failure(FailureType.DUPLICATE, "idempotency_violation", {"idempotency_key": idempotency_key})
        missing = sorted(field for field in declared_write_set if field not in after_state)
        if missing:
            return Failure(FailureType.PARTIAL, f"missing_fields:{','.join(missing)}", {"missing": missing})
        collateral = sorted(field for field in after_state
                            if field not in declared_write_set and after_state[field] != before_state.get(field))
        if collateral:
            return Failure(FailureType.COLLATERAL, f"collateral_change:{','.join(collateral)}",
                           {"collateral_fields": collateral})
        return Failure(FailureType.WRONG_VALUE, "state_mismatch", {"before": before_state, "after": after_state})
