import pytest

from harness.baseline_agents import TrustTheToolAgent
from harness.fault_injection import FailureMode, FaultInjector


def test_ghost_success_is_explicitly_injected() -> None:
    result = FaultInjector(FailureMode.GHOST_SUCCESS).inject(lambda: {"status": "success"})
    assert result["ghost"] and result["injected"]


def test_timeout_is_not_silently_converted_to_success() -> None:
    with pytest.raises(TimeoutError):
        FaultInjector(FailureMode.TIMEOUT_AFTER_WRITE).inject(lambda: None)


def test_baseline_agent_claims_without_evidence() -> None:
    result = TrustTheToolAgent().run("refund", {})
    assert result["claimed"] and not result["verified"] and result["false_completion"]
