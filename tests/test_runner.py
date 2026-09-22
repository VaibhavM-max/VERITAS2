from agent.executor import AgentExecutor
from agent.planner import AgentPlanner
from agent.tools.database import DatabaseTool
from ledger.crypto import generate_keypair
from ledger.evidence_ledger import EvidenceLedger
from recovery.recovery_engine import RecoveryEngine
from runner.completion_gate import CompletionGate
from runner.dag_runner import DAGRunner
from verifier.independent_verifier import IndependentVerifier


def test_refund_plan_is_complete_when_system_state_is_verified(tmp_path) -> None:
    db_path = tmp_path / "veritas.db"
    from scripts.init_db import init_database
    init_database(str(db_path))
    keys = generate_keypair()
    ledger = EvidenceLedger(keys["private_key"], keys["public_key"])
    plan = AgentPlanner().plan_refund_task("C123", "ORD-001", 50.0, "REQ-TEST")
    result = DAGRunner(AgentExecutor(DatabaseTool(str(db_path))), IndependentVerifier(str(db_path), ledger), RecoveryEngine()).run_plan(plan)
    gated = CompletionGate().compute_status(result, len(plan["steps"]))
    assert gated["final_status"] == "COMPLETE"
    assert len(result["evidence_log"]) == 3
