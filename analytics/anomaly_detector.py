"""Lightweight statistical anomaly detection for VERITAS executions."""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class AnomalyDetector:
    """Persist execution metrics and flag meaningful deviations from history."""

    def __init__(self, db_path: str = "data/analytics.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS execution_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    evidence_count INTEGER NOT NULL,
                    verification_rate REAL NOT NULL,
                    retry_count INTEGER NOT NULL,
                    is_offline INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    metrics TEXT NOT NULL
                );
                """
            )

    def record_execution(self, task_id: str, metrics: dict[str, Any]) -> None:
        """Record one completed execution for future comparisons."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """INSERT INTO execution_metrics
                   (task_id, timestamp, execution_time, evidence_count,
                    verification_rate, retry_count, is_offline)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id,
                    datetime.now(timezone.utc).isoformat(),
                    float(metrics.get("execution_time", 0.0)),
                    int(metrics.get("evidence_count", 0)),
                    float(metrics.get("verification_rate", 100.0)),
                    int(metrics.get("retry_count", 0)),
                    int(bool(metrics.get("is_offline", False))),
                ),
            )

    def detect_anomalies(self, task_id: str, current: dict[str, Any]) -> list[dict[str, Any]]:
        """Compare current metrics with prior observations and persist findings."""
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """SELECT execution_time, evidence_count, verification_rate, retry_count
                   FROM execution_metrics ORDER BY id DESC LIMIT 100"""
            ).fetchall()

        if not rows:
            return []
        findings: list[dict[str, Any]] = []
        execution_times = [row[0] for row in rows]
        verification_rates = [row[2] for row in rows]
        retry_counts = [row[3] for row in rows]
        current_time = float(current.get("execution_time", 0.0))
        current_rate = float(current.get("verification_rate", 100.0))
        current_retries = int(current.get("retry_count", 0))

        mean_time = _mean(execution_times)
        std_time = _stddev(execution_times, mean_time)
        if len(rows) >= 3 and std_time > 0 and abs(current_time - mean_time) > 3 * std_time:
            findings.append(self._finding(
                task_id, "UNUSUAL_EXECUTION_TIME",
                "HIGH" if abs(current_time - mean_time) > 5 * std_time else "MEDIUM",
                f"Execution time {current_time:.2f}s is outside the historical range.",
                {"current": current_time, "mean": mean_time, "std": std_time},
            ))

        average_rate = _mean(verification_rates)
        if current_rate < 90 and average_rate > 95:
            findings.append(self._finding(
                task_id, "VERIFICATION_RATE_DROP",
                "CRITICAL" if current_rate < 50 else "HIGH",
                f"Verification rate dropped to {current_rate:.1f}% from a {average_rate:.1f}% average.",
                {"current": current_rate, "average": average_rate},
            ))

        average_retries = _mean(retry_counts)
        retry_stddev = _stddev(retry_counts, average_retries)
        if current_retries > average_retries + max(1.0, 3 * retry_stddev):
            findings.append(self._finding(
                task_id, "EXCESSIVE_RETRIES", "MEDIUM",
                f"Retry count {current_retries} is above the historical baseline.",
                {"current": current_retries, "average": average_retries},
            ))

        if findings:
            with sqlite3.connect(self.db_path) as connection:
                connection.executemany(
                    """INSERT INTO anomalies
                       (task_id, anomaly_type, severity, description, detected_at, metrics)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    [(
                        item["task_id"], item["anomaly_type"], item["severity"],
                        item["description"], item["detected_at"], json.dumps(item["metrics"]),
                    ) for item in findings],
                )
        return findings

    def _finding(self, task_id: str, anomaly_type: str, severity: str, description: str, metrics: dict) -> dict:
        return {
            "task_id": task_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "description": description,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
        }

    def get_anomaly_summary(self, hours: int = 24) -> dict[str, Any]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """SELECT anomaly_type, severity, COUNT(*) FROM anomalies
                   WHERE detected_at > ? GROUP BY anomaly_type, severity""", (cutoff,)
            ).fetchall()
        by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        by_type: dict[str, int] = {}
        for anomaly_type, severity, count in rows:
            by_type[anomaly_type] = by_type.get(anomaly_type, 0) + count
            by_severity[severity] = by_severity.get(severity, 0) + count
        return {"total_anomalies": sum(by_severity.values()), "by_type": by_type, "by_severity": by_severity}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev(values: list[float], mean: float) -> float:
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) if values else 0.0
