"""Pure execution replay state for dashboard controls."""

from __future__ import annotations


class ExecutionReplayer:
    """Navigate a saved task's steps without mutating execution state."""

    def __init__(self, task_result: dict) -> None:
        self.task_result = task_result
        self.current_step = 0

    @property
    def steps(self) -> list[dict]:
        return self.task_result.get("plan", {}).get("steps", self.task_result.get("steps", []))

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    def reset(self) -> None:
        self.current_step = 0

    def previous(self) -> None:
        self.current_step = max(0, self.current_step - 1)

    def next(self) -> None:
        self.current_step = min(max(0, self.total_steps - 1), self.current_step + 1)

    def current(self) -> dict | None:
        return self.steps[self.current_step] if self.steps else None

    def progress(self) -> float:
        return (self.current_step + 1) / self.total_steps if self.total_steps else 0.0
