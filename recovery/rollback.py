"""Compensating actions for reversible demo writes."""

from agent.tools.database import DatabaseTool


class RollbackEngine:
    def __init__(self, db_tool: DatabaseTool) -> None:
        self.db_tool = db_tool

    def rollback_refund(self, refund_id: str) -> dict:
        return {"action": "rollback_refund", "result": self.db_tool.update_refund_status(refund_id, "CANCELLED")}
