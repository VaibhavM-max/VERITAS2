"""Run the offline VERITAS refund demo."""

import os

from agent.executor import AgentExecutor
from agent.planner import AgentPlanner
from agent.tools.database import DatabaseTool
from dashboard.terminal_view import TerminalDashboard
from ledger.crypto import generate_keypair
from ledger.evidence_ledger import EvidenceLedger
from recovery.recovery_engine import RecoveryEngine
from runner.completion_gate import CompletionGate
from runner.dag_runner import DAGRunner
from runner.report_generator import ReportGenerator
from scripts.init_db import init_database
from verifier.independent_verifier import IndependentVerifier


def main() -> tuple[dict, dict, dict]:
    db_path = os.getenv("DATABASE_PATH", "data/veritas.db")
    init_database(db_path)
    keys = generate_keypair()
    ledger = EvidenceLedger(keys["private_key"], keys["public_key"])
    plan = AgentPlanner().plan_refund_task("C123", "ORD-001", 50.0, "REQ-001")
    executor = AgentExecutor(DatabaseTool(db_path))
    verifier = IndependentVerifier(db_path, ledger)
    execution = DAGRunner(executor, verifier, RecoveryEngine()).run_plan(plan)
    gated = CompletionGate().compute_status(execution, len(plan["steps"]))
    report = ReportGenerator().generate(gated, plan)
    bundle = ledger.export_proof_bundle()
    claims = report["claims"]
    TerminalDashboard().render_claim_vs_truth(claims, [{"state": "verified"} for _ in claims], gated["final_status"])
    return gated, report, bundle


if __name__ == "__main__":
    main()
