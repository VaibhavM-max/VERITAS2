"""Persistent operator achievements backed by SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class AchievementManager:
    ACHIEVEMENTS = {
        "FIRST_TASK": ("First Steps", "Execute your first verified task", 10),
        "PERFECT_VERIFICATION": ("Perfectionist", "Complete a task with every step verified", 50),
        "OFFLINE_SURVIVOR": ("Offline Survivor", "Complete a task while offline", 30),
        "EVIDENCE_MASTER": ("Evidence Master", "Generate 100 evidence receipts", 100),
    }

    def __init__(self, db_path: str = "data/achievements.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_email TEXT PRIMARY KEY,
                    total_tasks INTEGER NOT NULL DEFAULT 0,
                    total_evidence INTEGER NOT NULL DEFAULT 0,
                    perfect_tasks INTEGER NOT NULL DEFAULT 0,
                    offline_tasks INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_email TEXT NOT NULL,
                    achievement_id TEXT NOT NULL,
                    unlocked_at TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    PRIMARY KEY (user_email, achievement_id)
                );
                """
            )

    def update_stats(self, user_email: str, task_result: dict) -> list[dict]:
        """Record a task and return achievements unlocked by this task."""
        evidence_count = int(task_result.get("evidence_count", len(task_result.get("evidence", []))))
        is_perfect = task_result.get("final_status") == "COMPLETE"
        is_offline = bool(task_result.get("is_offline", False))
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("INSERT OR IGNORE INTO user_stats (user_email) VALUES (?)", (user_email,))
            connection.execute(
                """UPDATE user_stats SET total_tasks = total_tasks + 1,
                   total_evidence = total_evidence + ?, perfect_tasks = perfect_tasks + ?,
                   offline_tasks = offline_tasks + ? WHERE user_email = ?""",
                (evidence_count, int(is_perfect), int(is_offline), user_email),
            )
        return self.check_achievements(user_email)

    def check_achievements(self, user_email: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as connection:
            stats_row = connection.execute("SELECT * FROM user_stats WHERE user_email = ?", (user_email,)).fetchone()
            unlocked = {row[0] for row in connection.execute("SELECT achievement_id FROM user_achievements WHERE user_email = ?", (user_email,))}
            if not stats_row:
                return []
            stats = {"tasks": stats_row[1], "evidence": stats_row[2], "perfect": stats_row[3], "offline": stats_row[4]}
            eligible = []
            if stats["tasks"] >= 1:
                eligible.append("FIRST_TASK")
            if stats["perfect"] >= 1:
                eligible.append("PERFECT_VERIFICATION")
            if stats["offline"] >= 1:
                eligible.append("OFFLINE_SURVIVOR")
            if stats["evidence"] >= 100:
                eligible.append("EVIDENCE_MASTER")
            new_ids = [achievement_id for achievement_id in eligible if achievement_id not in unlocked]
            now = datetime.now(timezone.utc).isoformat()
            for achievement_id in new_ids:
                connection.execute(
                    "INSERT INTO user_achievements VALUES (?, ?, ?, ?)",
                    (user_email, achievement_id, now, self.ACHIEVEMENTS[achievement_id][2]),
                )
        return [self._as_dict(achievement_id, now) for achievement_id in new_ids]

    def get_user_achievements(self, user_email: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT achievement_id, unlocked_at, points FROM user_achievements WHERE user_email = ? ORDER BY unlocked_at DESC",
                (user_email,),
            ).fetchall()
        return [self._as_dict(achievement_id, unlocked_at, points) for achievement_id, unlocked_at, points in rows]

    def get_total_points(self, user_email: str) -> int:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute("SELECT COALESCE(SUM(points), 0) FROM user_achievements WHERE user_email = ?", (user_email,)).fetchone()
        return int(row[0])

    def _as_dict(self, achievement_id: str, unlocked_at: str, points: int | None = None) -> dict:
        name, description, default_points = self.ACHIEVEMENTS[achievement_id]
        return {"id": achievement_id, "name": name, "description": description, "points": points or default_points, "unlocked_at": unlocked_at}
