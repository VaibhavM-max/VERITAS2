"""Focused tests for the dashboard OTP authentication flow."""

from datetime import datetime, timedelta, timezone

from auth.otp_auth import OTPAuthManager


def test_otp_request_verify_is_single_use(tmp_path):
    manager = OTPAuthManager(str(tmp_path / "auth.db"))
    captured = {}
    manager.send_otp_email = lambda email, otp: captured.setdefault("otp", otp) or True

    requested, message = manager.request_otp("operator@example.com")
    assert requested is True
    assert "code" in message

    verified, _, session_id = manager.verify_otp("operator@example.com", captured["otp"])
    assert verified is True
    assert session_id
    assert manager.validate_session(session_id) == (True, "operator@example.com")

    reused, _, no_session = manager.verify_otp("operator@example.com", captured["otp"])
    assert reused is False
    assert no_session is None


def test_invalid_otp_is_limited(tmp_path):
    manager = OTPAuthManager(str(tmp_path / "auth.db"))
    manager.send_otp_email = lambda email, otp: True
    manager.request_otp("operator@example.com")

    for _ in range(manager.max_attempts):
        valid, _, session_id = manager.verify_otp("operator@example.com", "000000")
        assert valid is False
        assert session_id is None

    valid, _, session_id = manager.verify_otp("operator@example.com", "000000")
    assert valid is False
    assert session_id is None


def test_expired_session_is_invalid(tmp_path):
    manager = OTPAuthManager(str(tmp_path / "auth.db"))
    session_id = "expired-session"
    expired = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    with manager._connect() as connection:
        connection.execute(
            "INSERT INTO users (email, created_at) VALUES (?, ?)",
            ("operator@example.com", expired),
        )
        connection.execute(
            "INSERT INTO active_sessions (session_id, email, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, "operator@example.com", expired, expired),
        )

    assert manager.validate_session(session_id) == (False, None)