"""Proof-carrying reports with one evidence ID per verified claim."""


class ReportGenerator:
    def generate(self, execution_result: dict, plan: dict) -> dict:
        claims = []
        for step_id in execution_result.get("completed_steps", []):
            step = next(step for step in plan["steps"] if step["step_id"] == step_id)
            receipt = next((item for item in execution_result["evidence_log"] if item.step_id == step_id and item.result == "VERIFIED"), None)
            claims.append({"claim": step["description"], "evidence_id": receipt.receipt_id if receipt else None,
                           "verified": receipt is not None, "trust_level": receipt.trust_level if receipt else "none"})
        return {"status": execution_result.get("status"), "final_status": execution_result.get("final_status"),
                "summary": f"{plan['task_id']}: {len(claims)} verified claims",
                "claims": claims, "unproven_claims": [] if execution_result.get("status") == "COMPLETE" else [
                    {"step_id": execution_result.get("failed_step"), "verified": False}],
                "evidence_count": len(execution_result.get("evidence_log", []))}
