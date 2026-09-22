import sqlite3

from verifier.checker import SQLChecker
from verifier.failure_classifier import FailureClassifier, FailureType


def test_checker_reads_only_and_verifies_state(tmp_path) -> None:
    path = tmp_path / "world.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE refunds (refund_id TEXT, amount REAL, currency TEXT, customer_id TEXT, status TEXT)")
        connection.execute("INSERT INTO refunds VALUES ('R1', 50, 'USD', 'C123', 'PENDING')")
    result = SQLChecker(str(path)).check_refund_exists("R1", 50)
    assert result.passed
    assert result.actual["amount"] == 50


def test_classifier_distinguishes_ghost_success_and_partial() -> None:
    classifier = FailureClassifier()
    assert classifier.classify({"status": "PENDING"}, {"status": "PENDING"}, {"status"}, "k", set()).type == FailureType.NO_EFFECT
    assert classifier.classify({"status": "PENDING", "amount": 0}, {"status": "DONE"}, {"status", "amount"}, "k", set()).type == FailureType.PARTIAL
