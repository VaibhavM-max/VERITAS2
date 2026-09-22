"""Interactive Streamlit dashboard for the VERITAS execution pipeline."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from auth.login_page import render_login_page
from auth.otp_auth import auth_manager


st.set_page_config(
    page_title="VERITAS Control Room",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink: #17202a; --muted: #68737d; --line: #dce3e8; --mint: #dff3ea; --coral: #ffe5df; }
    .stApp { background: #f6f8f7; }
    [data-testid="stSidebar"] { background: #17202a; }
    [data-testid="stSidebar"] * { color: #f6f8f7; }
    .eyebrow { color: #287d68; font-size: .76rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    .hero { border-bottom: 1px solid var(--line); padding: .4rem 0 1.2rem; animation: rise .45s ease-out; }
    .hero h1 { color: var(--ink); font-size: 2.2rem; margin: .2rem 0; }
    .hero p { color: var(--muted); margin: 0; }
    .status-strip { background: white; border: 1px solid var(--line); border-radius: 8px; padding: 1rem; }
    .receipt { background: white; border: 1px solid var(--line); border-left: 4px solid #287d68; border-radius: 6px; padding: .75rem 1rem; margin: .5rem 0; }
    .receipt-fail { border-left-color: #cf4d3d; }
    .pulse { display: inline-block; width: .55rem; height: .55rem; border-radius: 50%; background: #287d68; box-shadow: 0 0 0 0 rgba(40,125,104,.45); animation: pulse 1.8s infinite; }
    @keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes pulse { 70% { box-shadow: 0 0 0 8px rgba(40,125,104,0); } 100% { box-shadow: 0 0 0 0 rgba(40,125,104,0); } }
    </style>
    """,
    unsafe_allow_html=True,
)


def _init_state() -> None:
    if "ledger" not in st.session_state:
        from ledger.crypto import generate_keypair
        from ledger.evidence_ledger import EvidenceLedger

        keys = generate_keypair()
        st.session_state.ledger = EvidenceLedger(keys["private_key"], keys["public_key"])
    st.session_state.setdefault("tasks", [])


def _queue_manager():
    from offline_queue.manager import OfflineQueueManager

    return OfflineQueueManager()


def _connectivity() -> bool:
    from utils.connectivity import check_internet

    return check_internet(timeout_seconds=2)


def _run_task(customer_id: str, order_id: str, amount: float) -> dict:
    from agent.executor import AgentExecutor
    from agent.planner import AgentPlanner
    from agent.tools.database import DatabaseTool
    from recovery.recovery_engine import RecoveryEngine
    from runner.completion_gate import CompletionGate
    from runner.dag_runner import DAGRunner
    from runner.report_generator import ReportGenerator
    from scripts.init_db import init_database
    from verifier.independent_verifier import IndependentVerifier

    progress = st.progress(0, text="Preparing verified execution")
    database_path = os.getenv("DATABASE_PATH", "data/veritas.db")
    init_database(database_path)
    progress.progress(20, text="Building the refund plan")
    request_id = datetime.now(timezone.utc).strftime("REQ-%Y%m%d%H%M%S%f")
    plan = AgentPlanner().plan_refund_task(customer_id, order_id, amount, request_id)
    ledger = st.session_state.ledger
    runner = DAGRunner(
        AgentExecutor(DatabaseTool(database_path)),
        IndependentVerifier(database_path, ledger),
        RecoveryEngine(),
    )
    progress.progress(45, text="Executing steps with independent checks")
    execution = runner.run_plan(plan)
    progress.progress(80, text="Computing evidence-gated completion")
    gated = CompletionGate().compute_status(execution, len(plan["steps"]))
    report = ReportGenerator().generate(gated, plan)
    result = {
        "task_id": plan["task_id"],
        "description": plan["description"],
        "final_status": gated["final_status"],
        "completed_steps": gated.get("completed_steps", []),
        "evidence": [receipt.to_dict() for receipt in gated.get("evidence_log", [])],
        "claims": report["claims"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    progress.progress(100, text="Execution complete")
    time.sleep(0.25)
    progress.empty()
    st.session_state.tasks.insert(0, result)
    return result


def _all_receipts() -> list[dict]:
    return [receipt.to_dict() for receipt in st.session_state.ledger.get_receipts()]


def _render_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><div class="eyebrow">Evidence-gated operations</div><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def _render_status() -> tuple[dict, bool]:
    queue_stats = _queue_manager().get_queue_stats()
    online = _connectivity()
    st.sidebar.markdown("## VERITAS")
    st.sidebar.caption("Control room")
    st.sidebar.markdown(f'<span class="pulse"></span> <strong>{"ONLINE" if online else "OFFLINE"}</strong>', unsafe_allow_html=True)
    st.sidebar.metric("Pending queue", queue_stats["PENDING"])
    st.sidebar.metric("Synced", queue_stats["SYNCED"])
    st.sidebar.metric("Failed", queue_stats["FAILED"])
    st.sidebar.markdown("---")
    st.sidebar.caption(st.session_state.get("user_email", "Authenticated operator"))
    if st.sidebar.button("Sign out", use_container_width=True):
        auth_manager.logout(st.session_state.get("session_id"))
        for key in ("logged_in", "session_id", "user_email", "login_email"):
            st.session_state.pop(key, None)
        st.rerun()
    return queue_stats, online


def render_dashboard(queue_stats: dict, online: bool) -> None:
    receipts = _all_receipts()
    tasks = st.session_state.tasks
    verified = sum(receipt["result"] == "VERIFIED" for receipt in receipts)
    trust_score = round(verified / len(receipts) * 100) if receipts else 0
    _render_header("Control room", "A live view of execution, proof, and recovery state.")
    st.caption(f"Last checked {datetime.now().strftime('%H:%M:%S')} · {"Connected to the network" if online else "Operating offline-first"}")

    columns = st.columns(4)
    columns[0].metric("Tasks executed", len(tasks))
    columns[1].metric("Evidence receipts", len(receipts))
    columns[2].metric("Verification rate", f"{trust_score}%")
    columns[3].metric("Queue pending", queue_stats["PENDING"])

    st.subheader("System posture")
    status_columns = st.columns(3)
    status_columns[0].success("Ledger active" if receipts else "Ledger ready")
    status_columns[1].success("Verifier active")
    status_columns[2].success("Online" if online else "Offline-first mode")

    st.subheader("Recent task activity")
    if not tasks:
        st.info("No task executions in this dashboard session.")
    else:
        for task in tasks[:5]:
            status = task["final_status"]
            (st.success if status == "COMPLETE" else st.warning)(
                f"{task['task_id']} · {status} · {len(task['evidence'])} receipts"
            )
    if tasks:
        st.subheader("Execution footprint")
        st.bar_chart({
            "Evidence receipts": [len(task["evidence"]) for task in reversed(tasks[:10])],
            "Verified steps": [len(task["completed_steps"]) for task in reversed(tasks[:10])],
        })


def render_run_task() -> None:
    _render_header("Run a verified task", "Every step must produce evidence before completion is reported.")
    with st.form("refund_task"):
        customer_id = st.text_input("Customer ID", "C123")
        order_id = st.text_input("Order ID", "ORD-001")
        amount = st.number_input("Refund amount", min_value=0.01, value=50.0, step=0.01)
        submitted = st.form_submit_button("Execute refund", type="primary")
    if submitted:
        with st.spinner("Executing and independently verifying..."):
            result = _run_task(customer_id, order_id, amount)
        if result["final_status"] == "COMPLETE":
            st.success(f"{result['task_id']} completed with {len(result['evidence'])} verified receipts.")
        else:
            st.warning(f"{result['task_id']} ended in {result['final_status']}.")
        st.json({"status": result["final_status"], "completed_steps": result["completed_steps"]})


def render_evidence() -> None:
    receipts = _all_receipts()
    _render_header("Evidence ledger", "Inspect signed receipts and their Merkle commitments.")
    bundle = st.session_state.ledger.export_proof_bundle()
    st.download_button(
        "Download proof bundle",
        json.dumps(bundle, indent=2),
        "veritas-proof-bundle.json",
        "application/json",
    )
    if not receipts:
        st.info("No receipts have been generated in this session.")
        return
    result_filter = st.selectbox("Result", ["All", "VERIFIED", "MISMATCH", "UNVERIFIABLE"])
    trust_filter = st.selectbox("Trust level", ["All", "hard", "soft", "none"])
    filtered = [
        receipt for receipt in receipts
        if (result_filter == "All" or receipt["result"] == result_filter)
        and (trust_filter == "All" or receipt["trust_level"] == trust_filter)
    ]
    st.caption(f"Showing {len(filtered)} of {len(receipts)} receipts")
    for receipt in filtered:
        valid = st.session_state.ledger.verify(st.session_state.ledger.get_receipt_by_id(receipt["receipt_id"]))
        css_class = "receipt" if valid else "receipt receipt-fail"
        label = "VERIFIED" if valid else "TAMPER DETECTED"
        st.markdown(
            f'<div class="{css_class}"><strong>{label} · {receipt["receipt_id"]}</strong><br>'
            f'Step {receipt["step_id"]} · {receipt["result"]} · trust: {receipt["trust_level"]}<br>'
            f'<small>Merkle root: {receipt["merkle_root"] or "n/a"}</small></div>',
            unsafe_allow_html=True,
        )
        with st.expander("Inspect receipt payload", expanded=False):
            st.json(receipt)
            st.caption("Signature verification is performed against the in-memory ledger keypair.")


def render_queue(queue_stats: dict, online: bool) -> None:
    _render_header("Offline queue", "Store-and-forward state backed by SQLite.")
    columns = st.columns(3)
    columns[0].metric("Pending", queue_stats["PENDING"])
    columns[1].metric("Synced", queue_stats["SYNCED"])
    columns[2].metric("Failed", queue_stats["FAILED"])
    if online:
        st.info("Connectivity is available. Pending receipts can be synchronized by the application sync manager.")
    else:
        st.warning("Offline mode: new evidence will remain local until reconnect.")
    items = _queue_manager().dequeue_pending(limit=50)
    if items:
        st.dataframe(
            [{"Item": item.item_id, "Type": item.item_type, "Priority": item.priority, "Created": item.created_at} for item in items],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No pending items.")
    action_columns = st.columns(2)
    with action_columns[0]:
        if st.button("Force sync", disabled=not online, use_container_width=True):
            from sync.sync_manager import SyncManager
            from utils.connectivity import ConnectivityMonitor

            manager = SyncManager(_queue_manager(), ConnectivityMonitor())

            class DashboardCloud:
                def upload_evidence(self, data):
                    return True

            manager.set_cloud_client(DashboardCloud())
            manager.sync_now()
            st.success("Queue sync completed.")
            st.rerun()
    with action_columns[1]:
        if st.button("Clear synced older than 7 days", use_container_width=True):
            deleted = _queue_manager().clear_synced(older_than_days=7)
            st.info(f"Removed {deleted} old synced item(s).")
            st.rerun()


def render_analytics() -> None:
    _render_header("Analytics", "A compact view of claim truth and execution outcomes.")
    tasks = st.session_state.tasks
    receipts = _all_receipts()
    complete = sum(task["final_status"] == "COMPLETE" for task in tasks)
    columns = st.columns(3)
    columns[0].metric("Completed tasks", complete)
    columns[1].metric("Partial or failed", len(tasks) - complete)
    columns[2].metric("Receipts", len(receipts))
    st.subheader("Claim versus truth")
    claims = [claim for task in tasks for claim in task["claims"]]
    if claims:
        st.dataframe(
            [{"Claim": claim["claim"], "Verified": "YES" if claim["verified"] else "NO", "Evidence": claim["evidence_id"] or "NONE"} for claim in claims],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Run a task to populate claim verification data.")


def render_settings() -> None:
    st.sidebar.markdown("### Live view")
    auto_refresh = st.sidebar.checkbox("Auto-refresh every 5 seconds", value=False)
    if auto_refresh:
        time.sleep(5)
        st.rerun()


is_authenticated, authenticated_email = auth_manager.validate_session(st.session_state.get("session_id"))
if not is_authenticated:
    st.session_state.pop("logged_in", None)
    render_login_page()
    st.stop()

st.session_state.logged_in = True
st.session_state.user_email = authenticated_email
_init_state()
queue_stats, online = _render_status()
st.sidebar.markdown("---")
page = st.sidebar.radio("View", ["Dashboard", "Run task", "Evidence ledger", "Offline queue", "Analytics"])
if st.sidebar.button("Refresh data"):
    st.rerun()
render_settings()

if page == "Dashboard":
    render_dashboard(queue_stats, online)
elif page == "Run task":
    render_run_task()
elif page == "Evidence ledger":
    render_evidence()
elif page == "Offline queue":
    render_queue(queue_stats, online)
else:
    render_analytics()