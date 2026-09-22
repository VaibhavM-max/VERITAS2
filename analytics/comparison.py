"""Comparable dashboard metrics for verified and baseline agents."""


def build_comparison(tasks: list[dict]) -> list[dict]:
    """Return measured VERITAS metrics beside a clearly labeled baseline reference."""
    total = len(tasks)
    completed = sum(task.get("final_status") == "COMPLETE" for task in tasks)
    evidence = sum(len(task.get("evidence", [])) for task in tasks)
    verified = sum(
        1 for task in tasks for receipt in task.get("evidence", []) if receipt.get("result") == "VERIFIED"
    )
    verification_rate = round(verified / evidence * 100, 1) if evidence else 0.0
    return [
        {"Metric": "False completion risk", "VERITAS": "Evidence-gated", "Baseline reference": "Unmeasured"},
        {"Metric": "Verification rate", "VERITAS": f"{verification_rate:.1f}%", "Baseline reference": "Not available"},
        {"Metric": "Completed tasks", "VERITAS": str(completed), "Baseline reference": "Not measured"},
        {"Metric": "Offline queue", "VERITAS": "Supported", "Baseline reference": "Not measured"},
        {"Metric": "Sample size", "VERITAS": str(total), "Baseline reference": "Benchmark required"},
    ]
