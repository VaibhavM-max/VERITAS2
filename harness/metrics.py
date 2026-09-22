"""Small benchmark metrics collector."""

from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    agent_name: str
    failure_mode: str
    false_completion_rate: float
    duplicate_rate: float
    leftover_residue_rate: float
    false_reject_rate: float


class MetricsCollector:
    def __init__(self) -> None:
        self.results: list[BenchmarkResult] = []

    def record(self, agent_name: str, failure_mode: str, result: dict) -> None:
        self.results.append(BenchmarkResult(agent_name, failure_mode, result.get("false_completion_rate", 0),
                                            result.get("duplicate_rate", 0), result.get("leftover_residue_rate", 0),
                                            result.get("false_reject_rate", 0)))

    def summary(self) -> dict:
        grouped = {}
        for result in self.results:
            grouped.setdefault(result.agent_name, []).append(result)
        return {name: {"avg_false_completion_rate": sum(item.false_completion_rate for item in items) / len(items), "runs": len(items)}
                for name, items in grouped.items()}
