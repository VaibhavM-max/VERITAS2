"""Create explicit step contracts for the refund demo."""

import yaml


class AgentPlanner:
    def plan_refund_task(self, customer_id: str, order_id: str, amount: float, request_id: str) -> dict:
        refund_id = f"R-{request_id}"
        return {
            "task_id": f"TASK-{request_id}",
            "description": f"Process refund for {customer_id} on {order_id}",
            "steps": [
                {"step_id": "S1", "type": "check_eligibility", "description": "Verify refund eligibility",
                 "checker_type": "eligibility", "postconditions": ["eligibility record exists"],
                 "idempotency_key": f"eligibility-{request_id}", "reversibility": "reversible"},
                {"step_id": "S2", "type": "create_refund", "description": "Create refund record",
                 "checker_type": "refund_exists", "postconditions": ["refund exists with correct amount"],
                 "idempotency_key": f"refund-{order_id}", "reversibility": "reversible"},
                {"step_id": "S3", "type": "send_email", "description": "Queue confirmation email",
                 "checker_type": "email_outbox", "postconditions": ["email is queued"],
                 "idempotency_key": f"email-{refund_id}", "reversibility": "checkable-irreversible"},
            ],
            "context": {"customer_id": customer_id, "order_id": order_id, "amount": amount,
                        "request_id": request_id, "refund_id": refund_id, "email": "customer@example.com"},
        }

    def load_plan_from_yaml(self, yaml_path: str) -> dict:
        with open(yaml_path, encoding="utf-8") as plan_file:
            return yaml.safe_load(plan_file)
