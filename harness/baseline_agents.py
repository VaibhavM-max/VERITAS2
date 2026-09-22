"""Intentionally unsafe baselines for comparison."""


class TrustTheToolAgent:
    def run(self, task: str, context: dict) -> dict:
        return {"status": "COMPLETE", "claimed": True, "verified": False, "false_completion": True}


class RetryOnlyAgent(TrustTheToolAgent):
    def run(self, task: str, context: dict, max_retries: int = 3) -> dict:
        return {**super().run(task, context), "retries": max_retries}


class NaivePostconditionsAgent(TrustTheToolAgent):
    def run(self, task: str, context: dict) -> dict:
        return {**super().run(task, context), "postconditions_checked": True}
