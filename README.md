# VERITAS

VERITAS is an evidence-gated, zero-trust agent demo. The executor can claim that a tool succeeded, but only a separate read-only verifier can produce evidence. The completion gate derives the final status from those receipts.

## Quick start

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q
python main.py
```

The demo creates `data/veritas.db`, runs a refund workflow, checks each state transition independently, signs each receipt with Ed25519, and prints a claim-vs-truth table. The generated demo key is in memory, so no secret is written by the default run.

## Offline-first operation

Task execution, read-only verification, signed receipts, and the completion gate are
local operations. Receipts are appended to the tamper-evident ledger and persisted in
the SQLite store-and-forward queue at `data/offline_queue.db` (override with
`OFFLINE_QUEUE_PATH`). This means an outage does not discard evidence.

`utils.connectivity.ConnectivityMonitor` can monitor transitions and
`sync.SyncManager` can flush queued receipts when an application supplies a cloud
client implementing `upload_evidence`, `process_llm_request`, or `upload_audit_log`.
Failed items remain retryable with `OfflineQueueManager.retry_failed()`.

Planning remains safe without a model: `AgentPlanner.plan_task()` uses the
deterministic refund contract when a local adapter is unavailable. To use an
on-device Ollama model, install Ollama, pull a model, and construct
`AgentPlanner(LocalLLMAdapter("llama3.1:8b"))`. No network request is required for
execution or verification.

## Structure

- `agent/`: planner, executor, and write-side tools
- `verifier/`: read-only SQL checks and failure classification
- `ledger/`: signed receipts and Merkle accumulator
- `runner/`: DAG execution, completion gate, and report generation
- `harness/`: fault injection, baselines, and metrics
- `dashboard/`: terminal and optional Streamlit views
- `scripts/`: database, key, and proof utilities

## Safety behavior

`COMPLETE` requires every planned step to be `VERIFIED` and every receipt to be valid. An upstream mismatch returns `PARTIAL` or `ESCALATED` and downstream steps are `BLOCKED`; the executor's text is never used as proof.
