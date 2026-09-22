"""Tests for competition dashboard feature modules."""

from analytics.anomaly_detector import AnomalyDetector
from analytics.comparison import build_comparison
from gamification.achievements import AchievementManager
from replay.execution_replay import ExecutionReplayer
from voice.voice_commands import parse_command


def test_anomaly_detector_flags_execution_time(tmp_path):
    detector = AnomalyDetector(str(tmp_path / "analytics.db"))
    for value in (1.0, 1.1, 0.9):
        detector.record_execution("history", {"execution_time": value, "verification_rate": 100})
    findings = detector.detect_anomalies("current", {"execution_time": 10.0, "verification_rate": 100})
    assert findings[0]["anomaly_type"] == "UNUSUAL_EXECUTION_TIME"
    assert detector.get_anomaly_summary()["total_anomalies"] == 1


def test_achievements_are_unlocked_once(tmp_path):
    manager = AchievementManager(str(tmp_path / "achievements.db"))
    task = {"final_status": "COMPLETE", "evidence": [{"result": "VERIFIED"}]}
    assert len(manager.update_stats("judge@example.com", task)) == 2
    assert manager.update_stats("judge@example.com", task) == []
    assert manager.get_total_points("judge@example.com") == 60


def test_replay_stays_within_step_bounds():
    replay = ExecutionReplayer({"steps": [{"step_id": "S1"}, {"step_id": "S2"}]})
    replay.next()
    replay.next()
    assert replay.current()["step_id"] == "S2"
    replay.previous()
    assert replay.current()["step_id"] == "S1"
    assert replay.progress() == 0.5


def test_comparison_marks_unmeasured_baseline():
    rows = build_comparison([{"final_status": "COMPLETE", "evidence": [{"result": "VERIFIED"}]}])
    assert rows[1]["VERITAS"] == "100.0%"
    assert rows[1]["Baseline reference"] == "Not available"


def test_command_parser():
    assert parse_command("please show the evidence ledger") == "Evidence ledger"
    assert parse_command("something unrelated") is None
