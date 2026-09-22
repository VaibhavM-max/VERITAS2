"""Connectivity monitoring without making network access a runtime prerequisite."""

from __future__ import annotations

from enum import Enum
import threading
import time
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen


class ConnectivityStatus(Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"


class ConnectivityMonitor:
    def __init__(
        self,
        check_interval_seconds: float = 10,
        heartbeat_url: str = "https://www.google.com",
        initial_status: ConnectivityStatus = ConnectivityStatus.OFFLINE,
    ) -> None:
        self.check_interval = check_interval_seconds
        self.heartbeat_url = heartbeat_url
        self.status = initial_status
        self.callbacks: dict[ConnectivityStatus, list[Callable[[ConnectivityStatus, ConnectivityStatus], None]]] = {
            status: [] for status in ConnectivityStatus
        }
        self._running = False
        self._thread: threading.Thread | None = None

    def register_callback(
        self,
        status: ConnectivityStatus,
        callback: Callable[[ConnectivityStatus, ConnectivityStatus], None],
    ) -> None:
        self.callbacks[status].append(callback)

    def check_connectivity(self, timeout_seconds: float = 5) -> ConnectivityStatus:
        request = Request(self.heartbeat_url, method="HEAD")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return (
                    ConnectivityStatus.ONLINE
                    if 200 <= response.status < 400
                    else ConnectivityStatus.DEGRADED
                )
        except (OSError, URLError):
            return ConnectivityStatus.OFFLINE

    def poll_once(self, timeout_seconds: float = 5) -> ConnectivityStatus:
        new_status = self.check_connectivity(timeout_seconds)
        old_status = self.status
        self.status = new_status
        if new_status != old_status:
            for callback in tuple(self.callbacks[new_status]):
                callback(old_status, new_status)
        return new_status

    def _monitor_loop(self) -> None:
        while self._running:
            self.poll_once()
            time.sleep(self.check_interval)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=max(1, self.check_interval + 1))
            self._thread = None

    def is_online(self) -> bool:
        return self.status == ConnectivityStatus.ONLINE

    def is_offline(self) -> bool:
        return self.status == ConnectivityStatus.OFFLINE


def check_internet(timeout_seconds: float = 5, heartbeat_url: str = "https://www.google.com") -> bool:
    return ConnectivityMonitor(heartbeat_url=heartbeat_url).check_connectivity(timeout_seconds) == ConnectivityStatus.ONLINE
