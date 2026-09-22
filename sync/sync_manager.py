"""Reconcile queued offline work with an optional cloud client."""

from __future__ import annotations

import threading
from typing import Any

from offline_queue import OfflineQueueManager, QueueItem
from utils.connectivity import ConnectivityMonitor, ConnectivityStatus


class SyncManager:
    def __init__(self, queue_manager: OfflineQueueManager, connectivity_monitor: ConnectivityMonitor) -> None:
        self.queue = queue_manager
        self.connectivity = connectivity_monitor
        self._cloud_client: Any = None
        self._sync_lock = threading.Lock()
        self._sync_in_progress = False

    def set_cloud_client(self, cloud_client: Any) -> None:
        self._cloud_client = cloud_client

    def start_auto_sync(self) -> None:
        self.connectivity.register_callback(ConnectivityStatus.ONLINE, self._on_reconnect)

    def _on_reconnect(self, _old_status: ConnectivityStatus, _new_status: ConnectivityStatus) -> None:
        threading.Thread(target=self.sync_now, daemon=True).start()

    def _sync_item(self, item: QueueItem) -> None:
        if self._cloud_client is None:
            raise RuntimeError("Cannot synchronize offline item: no cloud client configured")
        handlers = {
            "EVIDENCE_RECEIPT": "upload_evidence",
            "LLM_REQUEST": "process_llm_request",
            "AUDIT_LOG": "upload_audit_log",
        }
        method_name = handlers.get(item.item_type)
        if method_name is None or not hasattr(self._cloud_client, method_name):
            raise ValueError(f"Unsupported sync item type: {item.item_type}")
        getattr(self._cloud_client, method_name)(item.data)

    def sync_now(self) -> bool:
        if not self.connectivity.is_online():
            return False
        if not self._sync_lock.acquire(blocking=False):
            return False
        self._sync_in_progress = True
        try:
            for item in self.queue.dequeue_pending():
                try:
                    self._sync_item(item)
                except Exception:
                    self.queue.mark_failed(item.item_id)
                else:
                    self.queue.mark_synced(item.item_id)
            return True
        finally:
            self._sync_in_progress = False
            self._sync_lock.release()

    def get_sync_status(self) -> dict[str, Any]:
        return {
            "connectivity": self.connectivity.status.value,
            "sync_in_progress": self._sync_in_progress,
            "queue_stats": self.queue.get_queue_stats(),
        }
