"""Terminal claim-vs-truth view."""

from rich.console import Console
from rich.table import Table


class TerminalDashboard:
    def __init__(self) -> None:
        self.console = Console()

    def render_claim_vs_truth(self, claims: list, truths: list, final_status: str) -> None:
        table = Table(title="VERITAS: Claim vs Truth")
        table.add_column("Claim")
        table.add_column("System state")
        table.add_column("Evidence")
        for claim, truth in zip(claims, truths):
            table.add_row(claim["claim"], truth.get("state", "unknown"), claim.get("evidence_id") or "NONE")
        self.console.print(table)
        self.console.print(f"Completion Gate: {final_status}")

    def render_evidence_log(self, evidence_log: list) -> None:
        for receipt in evidence_log:
            self.console.print(f"[{receipt.trust_level}] {receipt.receipt_id}: {receipt.result}")
