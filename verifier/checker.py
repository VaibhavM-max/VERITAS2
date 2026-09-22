"""Deterministic read-only checks against the system of record."""

from dataclasses import dataclass
import sqlite3
from typing import Any


@dataclass
class CheckerResult:
    expected: Any
    actual: Any
    systems: list[str]
    checks: list[dict]
    passed: bool

    def matches_expectation(self) -> bool:
        return self.passed


class SQLChecker:
    def __init__(self, read_only_db_path: str) -> None:
        self.db_path = f"file:{read_only_db_path}?mode=ro"

    def execute_query(self, query: str, params: tuple = ()) -> list[tuple]:
        with sqlite3.connect(self.db_path, uri=True) as connection:
            return connection.execute(query, params).fetchall()

    def check_eligibility(self, customer_id: str, request_id: str) -> CheckerResult:
        rows = self.execute_query(
            "SELECT eligibility_status, reason FROM refund_eligibility "
            "WHERE customer_id = ? AND request_id = ?",
            (customer_id, request_id),
        )
        if not rows:
            return CheckerResult("APPROVED or DENIED", None, ["refund_eligibility"],
                                 [{"check": "record exists", "result": "FAIL"}], False)
        status, reason = rows[0]
        passed = status in {"APPROVED", "DENIED"}
        return CheckerResult("APPROVED or DENIED", status, ["refund_eligibility"],
                             [{"check": "valid eligibility status", "result": "PASS" if passed else "FAIL"},
                              {"check": "reason", "result": reason}], passed)

    def check_refund_exists(self, refund_id: str, expected_amount: float) -> CheckerResult:
        rows = self.execute_query(
            "SELECT amount, currency, customer_id, status FROM refunds WHERE refund_id = ?",
            (refund_id,),
        )
        expected = {"refund_id": refund_id, "amount": expected_amount}
        if not rows:
            return CheckerResult(expected, None, ["refunds"],
                                 [{"check": "refund exists", "result": "FAIL"}], False)
        amount, currency, customer_id, status = rows[0]
        passed = abs(amount - expected_amount) < 0.01
        return CheckerResult(expected, {"amount": amount, "currency": currency,
                                        "customer_id": customer_id, "status": status},
                             ["refunds"], [{"check": "amount matches", "result": "PASS" if passed else "FAIL"}], passed)

    def check_no_duplicate_refund(self, order_id: str) -> CheckerResult:
        count = self.execute_query("SELECT COUNT(*) FROM refunds WHERE order_id = ?", (order_id,))[0][0]
        return CheckerResult(1, count, ["refunds"],
                             [{"check": "exactly one refund", "result": "PASS" if count == 1 else "FAIL"}], count == 1)
