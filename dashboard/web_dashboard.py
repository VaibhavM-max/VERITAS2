"""Optional Streamlit renderer for a saved report bundle."""

import json
import streamlit as st


def render_dashboard(final_status: str, claims: list, evidence_log: list, proof_bundle: dict) -> None:
    st.set_page_config(page_title="VERITAS Dashboard", layout="wide")
    st.title("VERITAS: Claim vs Truth")
    st.metric("Completion Gate", final_status)
    st.metric("Evidence Receipts", len(evidence_log))
    for claim in claims:
        (st.success if claim.get("verified") else st.error)(f"{claim['claim']} [{claim.get('evidence_id', 'NONE')}]")
    st.download_button("Export proof bundle", json.dumps(proof_bundle, indent=2), "proof_bundle.json", "application/json")
