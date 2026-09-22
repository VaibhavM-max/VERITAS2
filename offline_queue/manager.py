"""SQLite-backed store-and-forward queue for offline evidence and requests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import json
import os
import sqlite3
import uuid
from typing import Any


class QueueItemStatus(Enum):
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


@dataclass
class QueueItem:
    item_id: str
    item_type: str
    data: dict[str, Any]
    created_at: str
    status: QueueItemStatus = QueueItemStatus.PENDING
    synced_at: str | None = None
    retry_count: int = 0
    priority: int = 0


class OfflineQueueManager:
    def __init__(self, db_path: str = "data/offline_queue.db") -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS offline_queue (
                    item_id TEXT PRIMARY KEY, item_type TEXT NOT NULL, data TEXT NOT NULL,
                    created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING',
                    synced_at TEXT, retry_count INTEGER NOT NULL DEFAULT 0,
                    priority INTEGER NOT NULL DEFAULT 0
                )"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS offline_queue_status ON offline_queue(status)")

    def enqueue(self, item: QueueItem) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """INSERT OR REPLACE INTO offline_queue
                (item_id, item_type, data, created_at, status, synced_at, retry_count, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (item.item_id, item.item_type, json.dumps(item.data, sort_keys=True), item.created_at,
                 item.status.value, item.synced_at, item.retry_count, item.priority),
            )

    def dequeue_pending(self, limit: int = 100) -> list[QueueItem]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """SELECT item_id, item_type, data, created_at, status, synced_at, retry_count, priority
                FROM offline_queue WHERE status = 'PENDING'
                ORDER BY priority DESC, created_at ASC LIMIT ?""", (limit,)
            ).fetchall()
        return [QueueItem(row[0], row[1], json.loads(row[2]), row[3], QueueItemStatus(row[4]),
                          row[5], row[6], row[7]) for row in rows]

    def mark_synced(self, item_id: str) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("UPDATE offline_queue SET status = 'SYNCED', synced_at = ? WHERE item_id = ?",
                               (datetime.now(timezone.utc).isoformat(), item_id))

    def mark_failed(self, item_id: str, increment_retry: bool = True) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("UPDATE offline_queue SET status = 'FAILED', retry_count = retry_count + ? WHERE item_id = ?",
                               (1 if increment_retry else 0, item_id))

    def retry_failed(self, item_id: str | None = None) -> int:
        with sqlite3.connect(self.db_path) as connection:
            if item_id is None:
                cursor = connection.execute("UPDATE offline_queue SET status = 'PENDING' WHERE status = 'FAILED'")
            else:
                cursor = connection.execute("UPDATE offline_queue SET status = 'PENDING' WHERE item_id = ? AND status = 'FAILED'",
                                            (item_id,))
            return cursor.rowcount

    def get_queue_stats(self) -> dict[str, int]:
        stats = {status.value: 0 for status in QueueItemStatus}
        with sqlite3.connect(self.db_path) as connection:
            for status, count in connection.execute("SELECT status, COUNT(*) FROM offline_queue GROUP BY status"):
                stats[status] = count
        return stats

    def clear_synced(self, older_than_days: int = 7) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
        with sqlite3.connect(self.db_path) as connection:
            return connection.execute("DELETE FROM offline_queue WHERE status = 'SYNCED' AND synced_at < ?",
                                      (cutoff,)).rowcount

    def enqueue_evidence_receipt(self, receipt_data: dict[str, Any], priority: int = 10) -> str:
        item_id = f"EVD-{uuid.uuid4().hex[:12].upper()}"
        self.enqueue(QueueItem(item_id, "EVIDENCE_RECEIPT", receipt_data,
                               datetime.now(timezone.utc).isoformat(), priority=priority))
        return item_id

    def enqueue_llm_request(self, request_data: dict[str, Any], priority: int = 5) -> str:
        item_id = f"LLM-{uuid.uuid4().hex[:12].upper()}"
        self.enqueue(QueueItem(item_id, "LLM_REQUEST", request_data,
                               datetime.now(timezone.utc).isoformat(), priority=priority))
        return item_id
