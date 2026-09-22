"""Dependency-free command parser for keyboard or optional voice adapters."""


COMMANDS = {
    "dashboard": "Dashboard",
    "home": "Dashboard",
    "run task": "Run task",
    "execute task": "Run task",
    "evidence": "Evidence ledger",
    "ledger": "Evidence ledger",
    "queue": "Offline queue",
    "analytics": "Analytics",
    "achievements": "Achievements",
    "anomalies": "Anomalies",
    "replay": "Replay",
}


def parse_command(command: str) -> str | None:
    """Map a natural-language command to a dashboard view."""
    normalized = command.casefold().strip()
    for phrase, page in sorted(COMMANDS.items(), key=lambda item: len(item[0]), reverse=True):
        if phrase in normalized:
            return page
    return None
