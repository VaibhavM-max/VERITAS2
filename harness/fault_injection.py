"""Controlled faults for testing whether claims survive inspection."""

from enum import Enum


class FailureMode(Enum):
    GHOST_SUCCESS = "GHOST_SUCCESS"
    TIMEOUT_AFTER_WRITE = "TIMEOUT_AFTER_WRITE"
    PARTIAL_WRITE = "PARTIAL_WRITE"
    WRONG_VALUE = "WRONG_VALUE"
    COLLATERAL_CHANGE = "COLLATERAL_CHANGE"


class FaultInjector:
    def __init__(self, failure_mode: FailureMode) -> None:
        self.failure_mode = failure_mode

    def inject(self, tool_call, *args, **kwargs):
        if self.failure_mode == FailureMode.GHOST_SUCCESS:
            return {"status": "success", "injected": True, "ghost": True}
        if self.failure_mode == FailureMode.TIMEOUT_AFTER_WRITE:
            raise TimeoutError("Injected timeout after write")
        if self.failure_mode == FailureMode.PARTIAL_WRITE:
            return {"status": "success", "partial": True}
        if self.failure_mode == FailureMode.WRONG_VALUE:
            return {"status": "success", "wrong_value": True}
        if self.failure_mode == FailureMode.COLLATERAL_CHANGE:
            return {"status": "success", "collateral": True}
        return tool_call(*args, **kwargs)
