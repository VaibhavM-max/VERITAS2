"""Tool executor. Its returned trace is a claim, never proof."""

from agent.tools.database import DatabaseTool


class AgentExecutor:
    def __init__(self, db_tool: DatabaseTool) -> None:
        self.db_tool = db_tool
        self.operation_counter = 0

    def execute_step(self, step: dict, context: dict) -> dict:
        self.operation_counter += 1
        operation_id = f"OP-{self.operation_counter:03d}"
        step_type = step["type"]
        if step_type == "check_eligibility":
            result = self.db_tool.check_eligibility(context["customer_id"], context["request_id"], context["order_id"])
        elif step_type == "create_refund":
            result = self.db_tool.create_refund(context["refund_id"], context["order_id"], context["customer_id"], context["amount"], "Customer request")
        elif step_type == "send_email":
            result = self.db_tool.queue_email(context["refund_id"], context["email"])
        else:
            raise ValueError(f"Unknown step type: {step_type}")
        return {"operation_id": operation_id, "step_id": step["step_id"], "action": step_type,
                "result": result, "declared_write_set": set(result), "before_state": {},
                "after_state": result, "idempotency_key": step["idempotency_key"], "context": context}
