from datetime import datetime, timezone

from ledger.crypto import generate_keypair
from ledger.evidence_ledger import EvidenceLedger, EvidenceReceipt
from offline_queue import OfflineQueueManager, QueueItem, QueueItemStatus
from sync.sync_manager import SyncManager
from utils.connectivity import ConnectivityMonitor, ConnectivityStatus


def test_queue_orders_by_priority_and_persists(tmp_path):
    queue = OfflineQueueManager(str(tmp_path / "queue.db"))
    queue.enqueue(QueueItem("low", "AUDIT_LOG", {"value": 1}, "2026-01-01T00:00:00Z", priority=1))
    queue.enqueue(QueueItem("high", "AUDIT_LOG", {"value": 2}, "2026-01-02T00:00:00Z", priority=10))

    assert [item.item_id for item in queue.dequeue_pending()] == ["high", "low"]
    queue.mark_synced("high")
    assert queue.get_queue_stats() == {"PENDING": 1, "SYNCED": 1, "FAILED": 0}


def test_ledger_queues_signed_receipt_without_changing_verification(tmp_path):
    queue = OfflineQueueManager(str(tmp_path / "queue.db"))
    keys = generate_keypair()
    ledger = EvidenceLedger(keys["private_key"], keys["public_key"], queue)
    receipt = ledger.append(EvidenceReceipt(
        "R1", "S1", "OP1", "VERITAS", "check", ["db"], [], "VERIFIED",
        datetime.now(timezone.utc).isoformat(), {"actual": True},
    ))

    assert ledger.verify(receipt)
    assert queue.get_queue_stats()["PENDING"] == 1


def test_sync_marks_items_failed_without_cloud_and_retries_with_client(tmp_path):
    queue = OfflineQueueManager(str(tmp_path / "queue.db"))
    queue.enqueue(QueueItem("item", "AUDIT_LOG", {"value": 1}, "2026-01-01T00:00:00Z"))
    connectivity = ConnectivityMonitor(initial_status=ConnectivityStatus.ONLINE)
    manager = SyncManager(queue, connectivity)
    assert manager.sync_now()
    assert queue.get_queue_stats()["FAILED"] == 1

    class Client:
        def upload_audit_log(self, data):
            assert data == {"value": 1}

    queue.retry_failed()
    manager.set_cloud_client(Client())
    assert manager.sync_now()
    assert queue.get_queue_stats()["SYNCED"] == 1
