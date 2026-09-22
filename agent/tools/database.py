"""Read-write demo system-of-record tool."""

import sqlite3
from typing import Any


class DatabaseTool:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def check_eligibility(self, customer_id: str, request_id: str, order_id: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO refund_eligibility "
                "(eligibility_id, customer_id, request_id, order_id, eligibility_status, reason) "
                "VALUES (?, ?, ?, ?, 'APPROVED', ?)",
                (f"E-{request_id}", customer_id, request_id, order_id, "Demo policy approved"),
            )
        return {"eligibility_id": f"E-{request_id}", "status": "APPROVED"}

    def create_refund(self, refund_id: str, order_id: str, customer_id: str,
                      amount: float, reason: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO refunds "
                "(refund_id, order_id, customer_id, amount, reason, status) VALUES (?, ?, ?, ?, ?, 'PENDING')",
                (refund_id, order_id, customer_id, amount, reason),
            )
        return {"refund_id": refund_id, "status": "PENDING", "amount": amount}

    def queue_email(self, refund_id: str, recipient: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO email_outbox (email_id, refund_id, recipient) VALUES (?, ?, ?)",
                (f"EMAIL-{refund_id}", refund_id, recipient),
            )
        return {"email_id": f"EMAIL-{refund_id}", "refund_id": refund_id, "recipient": recipient, "status": "QUEUED"}

    def update_refund_status(self, refund_id: str, status: str) -> dict[str, str]:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("UPDATE refunds SET status = ? WHERE refund_id = ?", (status, refund_id))
        return {"refund_id": refund_id, "status": status}
