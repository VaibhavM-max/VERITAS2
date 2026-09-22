"""SQLite-backed one-time-password authentication for the dashboard."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import smtplib
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional


class OTPAuthManager:
    """Generate, deliver, and verify short-lived email OTPs and sessions."""

    def __init__(self, db_path: str | None = None, otp_ttl_minutes: int = 5, session_ttl_hours: int = 24):
        self.db_path = db_path or os.getenv("AUTH_DB_PATH", "data/auth.db")
        self.otp_ttl = timedelta(minutes=otp_ttl_minutes)
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.max_attempts = 5
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _init_database(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                );
                CREATE TABLE IF NOT EXISTS otp_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    otp_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    is_used INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (email) REFERENCES users(email)
                );
                CREATE TABLE IF NOT EXISTS active_sessions (
                    session_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (email) REFERENCES users(email)
                );
                CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_sessions(email, is_used);
                CREATE INDEX IF NOT EXISTS idx_session_expiry ON active_sessions(expires_at);
                """
            )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _stamp(value: datetime) -> str:
        return value.isoformat()

    @staticmethod
    def _valid_email(email: str) -> bool:
        local, separator, domain = email.strip().partition("@")
        return bool(local and separator and domain and "." in domain)

    @staticmethod
    def _hash_otp(otp: str) -> str:
        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    def generate_otp(self) -> str:
        """Return a cryptographically random six-digit OTP."""
        return f"{secrets.randbelow(1_000_000):06d}"

    def send_otp_email(self, email: str, otp: str) -> bool:
        """Send an OTP via SMTP, or print a demo code when SMTP is unset."""
        if not self.smtp_username or not self.smtp_password:
            print(f"VERITAS demo OTP for {email}: {otp}")
            return True

        message = MIMEMultipart("alternative")
        message["From"] = self.from_email
        message["To"] = email
        message["Subject"] = "VERITAS dashboard login code"
        message.attach(MIMEText(
            f"Your VERITAS login code is {otp}. It expires in {int(self.otp_ttl.total_seconds() // 60)} minutes.",
            "plain",
        ))
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            return True
        except (OSError, smtplib.SMTPException) as error:
            print(f"OTP delivery failed: {error}")
            return False

    def request_otp(self, email: str) -> tuple[bool, str]:
        """Create and deliver a single-use OTP for a valid email address."""
        email = email.strip().lower()
        if not self._valid_email(email):
            return False, "Enter a valid email address."

        otp = self.generate_otp()
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO users (email, created_at) VALUES (?, ?)",
                (email, self._stamp(now)),
            )
            connection.execute(
                "UPDATE otp_sessions SET is_used = 1 WHERE email = ? AND is_used = 0",
                (email,),
            )
            connection.execute(
                "INSERT INTO otp_sessions (email, otp_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (email, self._hash_otp(otp), self._stamp(now), self._stamp(now + self.otp_ttl)),
            )

        if self.send_otp_email(email, otp):
            return True, "A one-time code was sent."
        return False, "The code could not be delivered. Check SMTP configuration."

    def verify_otp(self, email: str, otp: str) -> tuple[bool, str, Optional[str]]:
        """Verify an OTP once and return a new expiring session ID."""
        email = email.strip().lower()
        otp_hash = self._hash_otp(otp.strip())
        now = self._now()
        with self._connect() as connection:
            row = connection.execute(
                """SELECT id, otp_hash, attempts FROM otp_sessions
                   WHERE email = ? AND is_used = 0 AND expires_at > ?
                   ORDER BY id DESC LIMIT 1""",
                (email, self._stamp(now)),
            ).fetchone()
            if not row or row[2] >= self.max_attempts:
                return False, "Invalid or expired code.", None

            if not hmac.compare_digest(row[1], otp_hash):
                connection.execute("UPDATE otp_sessions SET attempts = attempts + 1 WHERE id = ?", (row[0],))
                return False, "Invalid or expired code.", None

            session_id = f"sess_{uuid.uuid4().hex}"
            connection.execute("UPDATE otp_sessions SET is_used = 1 WHERE id = ?", (row[0],))
            connection.execute(
                "INSERT INTO active_sessions (session_id, email, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (session_id, email, self._stamp(now), self._stamp(now + self.session_ttl)),
            )
            connection.execute("UPDATE users SET last_login = ? WHERE email = ?", (self._stamp(now), email))
            return True, "Login successful.", session_id

    def validate_session(self, session_id: str | None) -> tuple[bool, Optional[str]]:
        """Return whether a session exists and has not expired."""
        if not session_id:
            return False, None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT email FROM active_sessions WHERE session_id = ? AND expires_at > ?",
                (session_id, self._stamp(self._now())),
            ).fetchone()
        return (True, row[0]) if row else (False, None)

    def logout(self, session_id: str | None) -> bool:
        """Invalidate a dashboard session."""
        if not session_id:
            return False
        with self._connect() as connection:
            connection.execute("DELETE FROM active_sessions WHERE session_id = ?", (session_id,))
        return True


auth_manager = OTPAuthManager()