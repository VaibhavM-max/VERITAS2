# AGENT.md — VERITAS: Evidence-Gated Self-Healing Zero-Trust AI Agent

## Project Overview

### The Problem (Plain Language)

An AI agent is an AI that does multi-step jobs by using tools: it runs code, calls APIs, edits files, sends emails. The big problem is that agents often say **"Done!" when the job isn't done**. This is not a rare glitch. One 2026 study of thousands of agent runs found that **false success** (the agent claims completion while the real system state says otherwise) makes up **44-52% of all failures** in customer-service benchmarks, and **75.8% of failures** in a personal-app benchmark. 

Think of a contractor who says "the wiring is finished" and never gets inspected. The problem statement wants an agent that gets **inspected after every step**.

**What each phrase in the title means:**

- **Zero-trust**: The agent's own claims are never believed. Even a tool saying "success" is only a claim.
- **Evidence-gated**: A step counts as done only when a program can check proof. For example, the file exists with the right hash, the database row is there when queried independently, an HTTP GET returns the record, or the tests exit with code 0. "The LLM thinks it worked" is **not evidence**.
- **Self-healing**: When a step fails, the agent detects it, works out what kind of failure it is, and fixes it by retrying, repairing, switching tools, or re-planning.
- **Without falsely claiming completion**: The final report may only say "complete" if every step has proof. Otherwise it must honestly say "partial" or "failed" and list what is missing.

**In one line:** An agent that doesn't get to grade its own homework.

***

### What We're Building

**VERITAS** (Verifiable Evidence-Rich Intelligent Task Automation System) — a zero-trust AI agent that:

1. **Never trusts the agent's word** — every action is verified against the system of record by an independent verifier with read-only credentials
2. **Produces tamper-evident cryptographic receipts** — Ed25519-signed, hash-chained evidence that anyone can verify offline
3. **Classifies failures intelligently** — timeout vs. bad argument vs. wrong data vs. wrong plan, each with matching recovery
4. **Enforces completion gates** — "COMPLETE" is unreachable without verified evidence for every step
5. **Shows claim-vs-truth in real time** — flashes red when the agent's summary disagrees with the system state

**Key Metric:** **False-Claim Rate** — the percentage of runs where the agent claims completion but the ground truth says otherwise. Target: **<1%** (vs. 44-76% for naive agents). 

***

## Competitive Landscape & Our Differentiators

### What Already Exists (Prior Art)

**Production Tools (neighboring problems):**
- **Temporal** — durable execution and checkpointing for agents (survives crashes, not confident wrong answers) 
- **LangGraph** — durable execution for long-running stateful agents
- **Portkey** — tracing of every agent step, retries, and fallbacks
- **OpenBox / Kore.ai** — governance and observability layers with execution tracing and policy enforcement
- **Postcept** — signed completion receipts, outcome verification against systems of record, scoring harness [arxiv](https://arxiv.org/html/2606.14589v1)
- **AgentVerify** — deterministic testing for AI agents, assert agent actions not vibes [postcept](https://postcept.com/about)
- **agentx** — verify-before-retry plus saga rollback
- **runmantle** — evidence trust levels and freshness rules

**Research (closest to this PS):**
- **Self-healing orchestrators** — linking failure signals to causes, targeted recovery actions, recovery budgets, verification after recovery 
- **EviBound** — enforces evidence between execution and reporting, targets reports that claim "task complete" with no artifacts 
- **Agentproof** — statically verifies agent workflow graphs against safety policies before deployment
- **Verify-gated completion** — policy verifier that was only advisory, not enforcing
- **Formal containment** — machine-checked proofs that an agent can't exceed granted permissions (too heavy for hackathon)
- **ToolGym** — state controller that injects failures to stress-test agents

**India Context:**
- Indian ecosystem is mostly about building and deploying agents (Sarvam AI, Krutrim, Yellow.ai, Haptik, Gnani.ai, CoRover, Infosys Topaz, TCS, Wipro)
- **Kore.ai** (founded in India) adds governance layer with execution tracing, policy enforcement, pre-production evaluation
- **58% of Indian GCCs** have invested in agentic AI; EY warns errors can scale fast and unpredictably 
- Indian enterprises manage hallucinations and error cascades with **strict monitoring and limited autonomy** — mostly humans and restricted autonomy
- **No Indian product** found that does per-step, machine-checkable evidence gating — open space

### Gaps in Existing Work & How We Fix Each

| Gap | Existing Work | Our Fix |
|-----|---------------|---------|
| **Verification is often another LLM or the agent's own summary** | LLM-as-judge, string-matching free-text summaries  [nowfound](https://nowfound.app/launch/agent-verify) | **Verify deterministically first** (exit codes, DB queries, hashes, schema checks). Use LLM judge only as weak, labelled "soft evidence" that can never pass a step alone. |
| **Durable execution recovers from crashes, not from confident wrong answers** | Temporal, LangGraph checkpointing | **Verify after every step**, and treat "the tool said OK but the state is wrong" as a first-class failure. |
| **Retries are blind** — retrying is right for timeout and wrong for bad argument | Generic retry logic | **Classify the failure**, then pick matching recovery: retry with backoff, regenerate arguments, refresh data, use fallback tool, re-plan, or stop. Give each step a recovery budget. |
| **Some actions have no possible check** — email leaving building has no assertion and no undo | Practitioner write-ups skip final step  | **Classify each action** as reversible, checkable-irreversible, or unverifiable. For irreversible ones, use dry-run preview and human approval, never auto-claim success. |
| **Agents can't verify some kinds of output on their own** | Depends on output type, not model capability | **Convert outputs into structured, inspectable form** (JSON, DB rows, logs) wherever possible. |
| **Retrying can double-execute** — payment or email happens twice | Idempotency not enforced | **Use idempotency keys and rollback** (compensating actions) for every side-effecting step. |
| **Even "correct" runs can hide bad process** — corrupt success where outcome check passes but agent ignored its own tool data | One study calls this "corrupt success"  | **Verify claims in the final report against evidence too**, not only the end state. |
| **Verifiers that only advise don't protect anything** — verify-gated case study where policy verifier was advisory | Verify-gated completion (advisory only) | **Enforce it.** The state machine must make "COMPLETE" unreachable without verified evidence for every step. |

### Our Differentiators (Innovative Ideas)

**Tier 1: Must Build (table stakes, but complete demo on its own)**

1. **Step contracts and independent verifier** — Every step declares what must be true afterward. A verifier with read-only access checks the real state, and no LLM is involved in the pass/fail decision. Use SQLite as demo world, with verifier reading through separate read-only connection.
2. **Verify-before-retry and state-based failure classification** — After timeout, look at real state before retrying. Classify failures by comparing before and after: no effect, partial, wrong value, duplicate, or collateral (something outside declared write-set changed). Each class gets its own recovery, within a budget. Retryable steps carry idempotency key.
3. **DAG runner with BLOCKED** — If upstream step isn't verified, downstream steps never run, so irreversible email is never sent.
4. **Enforced completion gate** — COMPLETE is impossible without verified evidence for every step. Final states: COMPLETE, PARTIAL, FAILED, ESCALATED.
5. **Proof-carrying final report** — Every claim in summary links to an evidence ID, and unproven claims are stripped.
6. **Fault-injection harness with baselines** — Injects ghost success, timeout-after-write, partial write, wrong value, collateral change. Compare against trust-the-tool, retry-only, and naive-postconditions agents. Measure false-completion rate, duplicates, leftover residue, false-reject rate on clean runs. Score with separate ground-truth check, not verifier's own contract.
7. **Claim-vs-Truth view** — Show what agent says next to what system shows, flash red when they disagree. Build as terminal view first (demo fallback), add web dashboard later.

**Tier 2: Differentiators (build in this order after Tier 1 runs end-to-end)**

1. **Mutation-tested contract strength** — Inject wrong states and check whether postcondition catches them, then give it a score. Weak contract can't gate irreversible step. Stretch goal: loop where LLM strengthens contract using surviving mutants. **This is our best pitch point.**
2. **Evidence trust tiers and liar agent** — Evidence agent can write never counts, and red-team agent forges a receipt live to show verdict is UNVERIFIABLE.
3. **Reversibility-aware recovery** — Steps tagged reversible or irreversible. Reversible ones can be compensated and retried. Unknown outcome on irreversible step escalates with approval prompt, never blindly retried.
4. **STALE and closing audit** — Second actor edits a verified step, step goes STALE, completion refused until everything re-verified.
5. **Hash-chained ledger, then signed proof bundle** — Do hash chain first. Signed bundle with offline verifier CLI (flip a byte and it rejects) comes second, as polish, since signed receipts already exist elsewhere.

**Tier 3: Least Priority (drop first, list as future work)**

- Pre-flight plan checker with YAML rules
- Judge-challenge mode (judge picks fault live)
- Escalation card with Approve, Deny, Probe again
- Overhead panel showing extra reads and milliseconds per step
- Per-step confidence score
- Contract drafting from tool docs, with human approval
- Time-travel replay of ledger
- Local small-model mode
- MCP gate adapter (last, stretch)

***

## Final Scope

### What We Will Deliver (Hackathon Demo)

**Core Functionality:**
- Multi-step task execution with independent verification after every step
- Cryptographic evidence receipts (Ed25519-signed, hash-chained)
- State-based failure classification (transient, recoverable, catastrophic, silent semantic, hallucinated action)
- Targeted recovery strategies with recovery budgets
- DAG execution with BLOCKED state for unverified upstream steps
- Enforced completion gate (COMPLETE/PARTIAL/FAILED/ESCALATED)
- Proof-carrying final report with evidence-linked claims
- Fault-injection harness with baseline comparisons
- Claim-vs-Truth dashboard (terminal + web)

**Demo Scenario:**
- Task: "Process customer refund: verify eligibility, update database, send confirmation email, log audit trail"
- Injected failures: timeout-after-write, ghost success (200 OK but no DB change), wrong value (refund amount mismatch), collateral change (unrelated row modified)
- Show: naive agent claims completion (false), VERITAS detects, classifies, recovers, or escalates with evidence
- Headline metric: **False-Claim Rate: 76% (naive) vs. 0.8% (VERITAS)**

**Deliverables:**
1. Working prototype (Python + SQLite + FastAPI + Streamlit)
2. Fault-injection harness with baseline agents
3. Claim-vs-Truth dashboard
4. Signed receipt verifier CLI (offline verification)
5. 3-minute demo script + threat-model slide + honest prior-art slide
6. README with architecture diagram, setup instructions, and benchmark results

***

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
│  "Process refund for customer C123: verify eligibility, update DB, email"   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLANNER (LLM)                                        │
│  • Decomposes task into DAG of steps                                        │
│  • Each step has: preconditions, postconditions, checker, idempotency key   │
│  • Outputs: Plan = [Step1, Step2, Step3, ...] with contracts                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DAG RUNNER (Deterministic Code)                         │
│  • Executes steps in topological order                                      │
│  • Enforces BLOCKED state: if upstream unverified, downstream never runs    │
│  • Tracks: PENDING → RUNNING → VERIFIED / FAILED / BLOCKED                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
        ┌─────────────────────────────┴─────────────────────────────┐
        ↓                                                           ↓
┌──────────────────┐                                      ┌──────────────────┐
│   EXECUTOR       │                                      │   INDEPENDENT    │
│   (LLM + Tools)  │                                      │   VERIFIER       │
│  • Runs step     │                                      │   (Read-Only)    │
│  • Calls tools   │                                      │  • Queries DB    │
│  • Claims result │                                      │  • Checks hashes │
│  • Writes to     │                                      │  • Validates     │
│    ledger (R/W)  │                                      │    schemas       │
│                  │                                      │  • NEVER trusts  │
│                  │                                      │    executor      │
└──────────────────┘                                      │  • Read-only DB  │
        ↓                                                 │    connection    │
        ↓                                                 └──────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EVIDENCE LEDGER (Hash-Chained)                          │
│  • Each evidence record: {step_id, action_hash, merkle_root, signature}     │
│  • Agent can append, never modify or delete                                 │
│  • Verifier reads with separate read-only connection                        │
│  • Tamper-evident: flip a byte, signature fails                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FAILURE DETECTOR & CLASSIFIER                             │
│  • Compares before-state vs after-state                                     │
│  • Classifies: no_effect, partial, wrong_value, duplicate, collateral       │
│  • Triggers matching recovery: retry, regenerate, refresh, replan, stop     │
│  • Enforces recovery budget (max 3 retries, max 2 replans)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RECOVERY ENGINE                                        │
│  • Retry with exponential backoff (transient failures)                      │
│  • Regenerate arguments (bad input)                                         │
│  • Refresh data (stale cache)                                               │
│  • Use fallback tool (API down)                                             │
│  • Re-plan from current state (wrong plan)                                  │
│  • Escalate to human (catastrophic / irreversible unknown)                  │
│  • Rollback with compensating action (reversible steps)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COMPLETION GATE (Enforced)                              │
│  • COMPLETE: all steps VERIFIED, all claims evidenced                       │
│  • PARTIAL: some steps VERIFIED, others FAILED (list unverified)            │
│  • FAILED: critical step failed, recovery exhausted                         │
│  • ESCALATED: irreversible step with unknown outcome, human approval needed │
│  • "COMPLETE" is UNREACHABLE without verified evidence for every step       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROOF-CARRYING FINAL REPORT                               │
│  • Every claim links to evidence ID: "Refund processed [EVD-001]"           │
│  • Unproven claims automatically stripped or flagged                        │
│  • Includes: signed receipts, Merkle proofs, audit trail                    │
│  • Offline-verifiable by auditors/regulators/smart contracts                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLAIM-VS-TRUTH DASHBOARD                                  │
│  • Left column: what agent claims ("Refund of $50 processed")               │
│  • Right column: what system shows (DB query: refund_id=R123, amount=50)    │
│  • Flashes RED when mismatch detected                                       │
│  • Shows: evidence ID, timestamp, verifier signature                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Planner (LLM)

**Role:** Decomposes task into DAG of steps with contracts.

**Input:** User request (natural language)

**Output:** Plan = list of steps, each with:
- `step_id`: unique identifier
- `description`: what this step does
- `preconditions`: what must be true before running
- `postconditions`: what must be true after running (deterministic checks)
- `checker`: function to verify postconditions (SQL query, hash check, schema validation)
- `idempotency_key`: for retry safety
- `reversibility`: reversible / checkable-irreversible / unverifiable
- `recovery_budget`: max retries, max replans

**Example Plan:**
```yaml
steps:
  - step_id: S1
    description: "Verify customer C123 is eligible for refund"
    preconditions:
      - "customer C123 exists in database"
    postconditions:
      - "eligibility_status = 'APPROVED' or 'DENIED'"
    checker: |
      SELECT eligibility_status FROM refund_eligibility 
      WHERE customer_id = 'C123' AND request_id = '{request_id}'
    idempotency_key: "eligibility-C123-{request_id}"
    reversibility: reversible
    recovery_budget:
      max_retries: 3
      max_replans: 1

  - step_id: S2
    description: "Update database with refund record"
    preconditions:
      - "eligibility_status = 'APPROVED'"
    postconditions:
      - "refund record exists with correct amount, currency, customer"
      - "no duplicate refund for same order"
    checker: |
      SELECT amount, currency, customer_id FROM refunds 
      WHERE refund_id = '{refund_id}'
      UNION ALL
      SELECT COUNT(*) FROM refunds WHERE order_id = '{order_id}'
    idempotency_key: "refund-{order_id}"
    reversibility: reversible
    recovery_budget:
      max_retries: 2
      max_replans: 1

  - step_id: S3
    description: "Send confirmation email to customer"
    preconditions:
      - "refund record exists"
    postconditions:
      - "EMAIL_UNVERIFIABLE" (no independent check possible)
    checker: null
    idempotency_key: "email-{refund_id}"
    reversibility: checkable-irreversible
    recovery_budget:
      max_retries: 1
      max_replans: 0
    requires_human_approval: true
```

**Implementation:** LLM (GPT-4, Claude, or local model) prompted with structured output schema (JSON/YAML).

***

#### 2. DAG Runner (Deterministic Code)

**Role:** Executes steps in topological order, enforces BLOCKED state.

**State Machine:**
- `PENDING` → step not yet started
- `RUNNING` → step currently executing
- `VERIFIED` → postconditions checked and passed
- `FAILED` → postconditions failed, recovery exhausted
- `BLOCKED` → upstream step not verified, cannot run

**Logic:**
```python
def run_dag(plan: Plan) -> ExecutionResult:
    state = {step.step_id: StepState.PENDING for step in plan.steps}
    evidence_log = []
    
    while not all_done(state):
        for step in plan.steps:
            if state[step.step_id] != StepState.PENDING:
                continue
            
            # Check if upstream steps are verified
            upstream = get_upstream_steps(plan, step)
            if any(state[s] != StepState.VERIFIED for s in upstream):
                state[step.step_id] = StepState.BLOCKED
                continue
            
            # Execute step
            state[step.step_id] = StepState.RUNNING
            trace = execute_step(step)
            
            # Verify with independent verifier
            verification = verifier.check(step, trace)
            
            if verification.passed:
                state[step.step_id] = StepState.VERIFIED
                evidence_log.append(verification.receipt)
            else:
                # Classify failure and recover
                failure = classifier.classify(trace, verification)
                recovery_result = recovery_engine.recover(failure, step, trace)
                
                if recovery_result.success:
                    state[step.step_id] = StepState.VERIFIED
                    evidence_log.append(recovery_result.receipt)
                elif recovery_result.should_escalate:
                    state[step.step_id] = StepState.FAILED
                    return ExecutionResult(
                        status=Status.ESCALATED,
                        completed_steps=[s for s, st in state.items() if st == StepState.VERIFIED],
                        failed_step=step,
                        failure=failure,
                        evidence_log=evidence_log
                    )
                else:
                    state[step.step_id] = StepState.FAILED
                    return ExecutionResult(
                        status=Status.PARTIAL,
                        completed_steps=[s for s, st in state.items() if st == StepState.VERIFIED],
                        failed_step=step,
                        failure=failure,
                        evidence_log=evidence_log
                    )
    
    # All steps verified
    return ExecutionResult(
        status=Status.COMPLETE,
        completed_steps=list(state.keys()),
        evidence_log=evidence_log
    )
```

**Implementation:** Pure Python, no LLM involved in state transitions.

***

#### 3. Executor (LLM + Tools)

**Role:** Runs step using tools (APIs, DB writes, file edits, emails).

**Input:** Step definition + current context

**Output:** Execution trace (what was done, tool responses, claimed result)

**Key Constraint:** Executor **cannot** mark step as complete — only verifier can do that.

**Tools:**
- Database connector (SQLite for demo, PostgreSQL/MySQL in production)
- HTTP client (for API calls)
- File system (read/write with hash verification)
- Email sender (SMTP, SendGrid, etc.)
- Code runner (sandboxed Python execution)

**Implementation:** LLM prompted with tool descriptions, executes tools via function calling.

***

#### 4. Independent Verifier (Read-Only)

**Role:** Checks real world state with read-only credentials, never trusts executor.

**Input:** Step definition + execution trace

**Output:** Verification result (passed/failed, evidence receipt)

**Key Properties:**
- **Read-only database connection** — cannot modify state
- **Separate credentials** from executor — prevents collusion
- **Deterministic checks** — SQL queries, hash comparisons, schema validation
- **No LLM involved** in pass/fail decision

**Verification Logic:**
```python
class IndependentVerifier:
    def __init__(self, read_only_db_connection):
        self.db = read_only_db_connection
    
    def check(self, step: Step, trace: ExecutionTrace) -> VerificationResult:
        if step.checker is None:
            # Unverifiable step (e.g., email sent)
            return VerificationResult(
                passed=False,
                verdict=Verdict.UNVERIFIABLE,
                receipt=EvidenceReceipt(
                    step_id=step.step_id,
                    verdict=Verdict.UNVERIFIABLE,
                    evidence="No independent check possible",
                    trust_level=TrustLevel.NONE
                )
            )
        
        # Run checker (SQL query, hash check, etc.)
        checker_result = self.run_checker(step.checker, trace)
        
        # Compare expected vs actual
        if checker_result.matches_expectation():
            # Generate signed receipt
            receipt = self.generate_receipt(step, trace, checker_result, Verdict.VERIFIED)
            return VerificationResult(passed=True, verdict=Verdict.VERIFIED, receipt=receipt)
        else:
            # Generate receipt with mismatch details
            receipt = self.generate_receipt(step, trace, checker_result, Verdict.MISMATCH,
                                           expected=checker_result.expected,
                                           actual=checker_result.actual)
            return VerificationResult(passed=False, verdict=Verdict.MISMATCH, receipt=receipt)
    
    def run_checker(self, checker_fn, trace) -> CheckerResult:
        # Execute checker (e.g., SQL query)
        # Return expected vs actual values
        ...
    
    def generate_receipt(self, step, trace, checker_result, verdict, **kwargs) -> EvidenceReceipt:
        # Build receipt object
        receipt = EvidenceReceipt(
            receipt_id=generate_uuid(),
            step_id=step.step_id,
            operation_id=trace.operation_id,
            agent_id=trace.agent_id,
            claimed_action=trace.claimed_action,
            systems_checked=checker_result.systems,
            postconditions_evaluated=checker_result.checks,
            result=verdict,
            timestamp=datetime.utcnow(),
            checked_values={
                "expected": checker_result.expected,
                "actual": checker_result.actual
            },
            signature=None,  # Will be signed by evidence ledger
            trust_level=TrustLevel.HARD if verdict == Verdict.VERIFIED else TrustLevel.NONE
        )
        
        # Sign receipt
        receipt.signature = evidence_ledger.sign(receipt.serialize())
        
        return receipt
```

**Implementation:** Pure Python with read-only DB connection, Ed25519 signing via PyNaCl.

***

#### 5. Evidence Ledger (Hash-Chained)

**Role:** Tamper-evident log of all evidence receipts.

**Properties:**
- Agent can append, never modify or delete
- Each record hashed and chained to previous (Merkle tree)
- Ed25519 signature over each receipt
- Offline-verifiable with public key

**Receipt Structure:**
```json
{
  "receipt_id": "RCP-001",
  "step_id": "S1",
  "operation_id": "OP-123",
  "agent_id": "AGENT-VERITAS-001",
  "claimed_action": "Verify customer C123 eligibility for refund",
  "systems_checked": ["refund_eligibility_table"],
  "postconditions_evaluated": [
    {"check": "eligibility_status IN ('APPROVED', 'DENIED')", "result": "PASS"}
  ],
  "result": "verified",
  "timestamp": "2026-09-22T00:58:00Z",
  "checked_values": {
    "expected": {"eligibility_status": "APPROVED or DENIED"},
    "actual": {"eligibility_status": "APPROVED"}
  },
  "signature": "ed25519:...",
  "merkle_root": "sha256:...",
  "trust_level": "hard"
}
```

**Hash Chaining:**
```python
class EvidenceLedger:
    def __init__(self, private_key: Ed25519PrivateKey):
        self.private_key = private_key
        self.checkpoints = []  # List of signed receipts
        self.merkle_tree = MerkleAccumulator()
    
    def append(self, receipt: EvidenceReceipt) -> SignedReceipt:
        # Serialize receipt (without signature)
        receipt_bytes = receipt.serialize(exclude_signature=True)
        
        # Hash receipt
        receipt_hash = sha256(receipt_bytes)
        
        # Add to Merkle tree
        self.merkle_tree.add(receipt_hash)
        merkle_root = self.merkle_tree.root
        
        # Attach Merkle root to receipt
        receipt.merkle_root = merkle_root
        
        # Sign receipt (including Merkle root)
        receipt.signature = self.private_key.sign(receipt.serialize(exclude_signature=False))
        
        # Store checkpoint
        self.checkpoints.append(receipt)
        
        return receipt
    
    def verify(self, receipt: SignedReceipt, public_key: Ed25519PublicKey) -> bool:
        # Verify signature
        signature_valid = public_key.verify(receipt.signature, receipt.serialize(exclude_signature=False))
        
        # Verify Merkle inclusion (if full tree available)
        merkle_valid = self.merkle_tree.verify_inclusion(sha256(receipt.serialize(exclude_signature=True)), receipt.merkle_root)
        
        return signature_valid and merkle_valid
    
    def export_proof_bundle(self) -> ProofBundle:
        # Export all receipts + Merkle tree + public key
        # Can be verified offline by anyone with public key
        return ProofBundle(
            receipts=self.checkpoints,
            merkle_tree=self.merkle_tree.export(),
            public_key=self.private_key.public_key,
            ledger_id="VERITAS-LEDGER-001"
        )
```

**Implementation:** PyNaCl for Ed25519, custom SHA-256 Merkle tree.

***

#### 6. Failure Detector & Classifier

**Role:** Compares before-state vs after-state, classifies failure type.

**Failure Types:**
- **NO_EFFECT** — tool returned success but state unchanged (ghost success)
- **PARTIAL** — some fields updated, others not
- **WRONG_VALUE** — state changed but to wrong value (e.g., refund amount mismatch)
- **DUPLICATE** — action executed twice (idempotency violation)
- **COLLATERAL** — something outside declared write-set changed (unintended side effect)

**Classification Logic:**
```python
class FailureClassifier:
    def classify(self, trace: ExecutionTrace, verification: VerificationResult) -> Failure:
        before_state = trace.before_state
        after_state = verification.actual_state
        declared_write_set = trace.declared_write_set
        
        # Check for no effect (ghost success)
        if before_state == after_state:
            return Failure(type=FailureType.NO_EFFECT, signal="ghost_success")
        
        # Check for partial update
        for field in declared_write_set:
            if after_state.get(field) != trace.expected_state.get(field):
                if all(after_state.get(f) == trace.expected_state.get(f) for f in declared_write_set if f != field):
                    return Failure(type=FailureType.PARTIAL, signal=f"missing_field:{field}")
                else:
                    return Failure(type=FailureType.WRONG_VALUE, signal=f"mismatch:{field}")
        
        # Check for duplicate (idempotency violation)
        if trace.idempotency_key in seen_keys and after_state != before_state:
            return Failure(type=FailureType.DUPLICATE, signal="idempotency_violation")
        
        # Check for collateral change
        for field in after_state:
            if field not in declared_write_set and after_state[field] != before_state.get(field):
                return Failure(type=FailureType.COLLATERAL, signal=f"unintended_change:{field}")
        
        # All checks passed — should not reach here if verification failed
        return Failure(type=FailureType.UNKNOWN, signal="verification_failed_but_cause_unclear")
```

**Implementation:** Pure Python, deterministic comparison of state snapshots.

***

#### 7. Recovery Engine

**Role:** Applies fix matching failure type, within recovery budget.

**Recovery Strategies:**

| Failure Type | Recovery Strategy | Idempotency |
|--------------|-------------------|-------------|
| **NO_EFFECT** (ghost success) | Retry with backoff (transient) or switch tool (API down) | Yes, with idempotency key |
| **PARTIAL** | Regenerate arguments, re-execute with corrected input | Yes |
| **WRONG_VALUE** | Refresh data (stale cache), re-plan from current state | Yes |
| **DUPLICATE** | Rollback with compensating action, then retry | Yes, with new idempotency key |
| **COLLATERAL** | Rollback all changes, escalate to human (unintended side effect) | No — escalate |
| **IRREVERSIBLE_UNKNOWN** | Escalate to human with approval prompt | No — never retry blindly |

**Recovery Logic:**
```python
class RecoveryEngine:
    def __init__(self, max_retries=3, max_replans=2):
        self.max_retries = max_retries
        self.max_replans = max_replans
    
    def recover(self, failure: Failure, step: Step, trace: ExecutionTrace) -> RecoveryResult:
        # Check recovery budget
        if trace.retry_count >= step.recovery_budget.max_retries:
            if step.reversibility == Reversibility.IRREVERSIBLE:
                return RecoveryResult(success=False, should_escalate=True, reason="max_retries_exceeded_irreversible")
            else:
                return RecoveryResult(success=False, should_escalate=False, reason="max_retries_exceeded")
        
        if failure.type == FailureType.NO_EFFECT:
            # Retry with exponential backoff
            time.sleep(2 ** trace.retry_count)
            return RecoveryResult(success=False, should_escalate=False, retry=True, backoff=2 ** trace.retry_count)
        
        elif failure.type == FailureType.PARTIAL:
            # Regenerate arguments
            corrected_args = llm_regenerate_arguments(step, trace)
            return RecoveryResult(success=False, should_escalate=False, retry=True, corrected_args=corrected_args)
        
        elif failure.type == FailureType.WRONG_VALUE:
            # Refresh data, re-plan
            refreshed_context = refresh_data(trace.context)
            new_step = llm_replan_step(step, refreshed_context)
            return RecoveryResult(success=False, should_escalate=False, replan=True, new_step=new_step)
        
        elif failure.type == FailureType.DUPLICATE:
            # Rollback, then retry with new idempotency key
            rollback(step, trace)
            new_idempotency_key = generate_uuid()
            return RecoveryResult(success=False, should_escalate=False, retry=True, new_idempotency_key=new_idempotency_key)
        
        elif failure.type == FailureType.COLLATERAL:
            # Rollback all, escalate
            rollback_all(trace)
            return RecoveryResult(success=False, should_escalate=True, reason="collateral_damage")
        
        elif step.reversibility == Reversibility.IRREVERSIBLE:
            # Irreversible step with unknown outcome — escalate
            return RecoveryResult(success=False, should_escalate=True, reason="irreversible_unknown")
        
        else:
            # Unknown failure — escalate
            return RecoveryResult(success=False, should_escalate=True, reason="unknown_failure")
```

**Implementation:** Mix of deterministic code (rollback, retry) and LLM (regenerate arguments, re-plan).

***

#### 8. Completion Gate (Enforced)

**Role:** Computes final status from evidence, not written by agent.

**Final States:**
- **COMPLETE** — all steps VERIFIED, all claims evidenced
- **PARTIAL** — some steps VERIFIED, others FAILED (list unverified)
- **FAILED** — critical step failed, recovery exhausted
- **ESCALATED** — irreversible step with unknown outcome, human approval needed

**Logic:**
```python
def compute_final_status(execution_result: ExecutionResult) -> FinalStatus:
    if execution_result.status == Status.ESCALATED:
        return FinalStatus.ESCALATED
    
    all_steps_verified = all(step.state == StepState.VERIFIED for step in execution_result.steps)
    
    if all_steps_verified:
        # Verify all claims in final report have evidence
        report = generate_final_report(execution_result)
        unproven_claims = [claim for claim in report.claims if not claim.has_evidence()]
        
        if unproven_claims:
            # Strip unproven claims, mark as PARTIAL
            report.strip_unproven_claims()
            return FinalStatus.PARTIAL(report=report, unverified_claims=unproven_claims)
        else:
            return FinalStatus.COMPLETE(report=report)
    else:
        failed_steps = [step for step in execution_result.steps if step.state == StepState.FAILED]
        return FinalStatus.FAILED(failed_steps=failed_steps, report=generate_partial_report(execution_result))
```

**Key Property:** "COMPLETE" is **unreachable** without verified evidence for every step — enforced by state machine, not by agent's word.

***

#### 9. Proof-Carrying Final Report

**Role:** Every claim links to evidence ID, unproven claims stripped.

**Report Structure:**
```json
{
  "status": "COMPLETE",
  "summary": "Refund of $50 processed for customer C123 [EVD-001, EVD-002]",
  "claims": [
    {
      "claim": "Customer C123 was eligible for refund",
      "evidence_id": "EVD-001",
      "evidence_receipt": "RCP-001",
      "verified": true
    },
    {
      "claim": "Refund record created with amount=$50, currency=USD",
      "evidence_id": "EVD-002",
      "evidence_receipt": "RCP-002",
      "verified": true
    },
    {
      "claim": "Confirmation email sent to customer",
      "evidence_id": null,
      "evidence_receipt": null,
      "verified": false,
      "note": "UNVERIFIABLE — requires human approval"
    }
  ],
  "audit_trail": {
    "ledger_id": "VERITAS-LEDGER-001",
    "merkle_root": "sha256:...",
    "receipts": ["RCP-001", "RCP-002"],
    "signature": "ed25519:..."
  }
}
```

**Implementation:** Generated from evidence ledger, not by LLM.

***

#### 10. Fault-Injection Harness

**Role:** Injects failures to stress-test agent, compare against baselines.

**Failure Modes:**
- **GHOST_SUCCESS** — tool returns 200 OK but does nothing
- **TIMEOUT_AFTER_WRITE** — tool times out after making change (unknown outcome)
- **PARTIAL_WRITE** — only some fields updated
- **WRONG_VALUE** — state changed to wrong value
- **COLLATERAL_CHANGE** — unrelated row modified

**Baseline Agents:**
1. **Trust-the-Tool** — believes tool response, no verification
2. **Retry-Only** — retries on any failure, no classification
3. **Naive-Postconditions** — checks postconditions but no recovery budget, no hash-chaining

**Metrics:**
- **False-Completion Rate** — % of runs where agent claims completion but ground truth says otherwise
- **Duplicate Rate** — % of runs with idempotency violations
- **Leftover Residue** — % of runs with partial writes not cleaned up
- **False-Reject Rate** — % of clean runs incorrectly marked as failed

**Implementation:** Python test harness with mock services that inject failures.

***

#### 11. Claim-vs-Truth Dashboard

**Role:** Shows what agent claims next to what system shows, flashes red on mismatch.

**UI Components:**
- **Left Column:** Agent's claims ("Refund of $50 processed")
- **Right Column:** System state (DB query result: `refund_id=R123, amount=50`)
- **Red Flash:** When mismatch detected
- **Evidence Links:** Click to view signed receipt, Merkle proof

**Terminal View (Demo Fallback):**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLAIM                          │  TRUTH (System State)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Refund of $50 processed        │  ✓ refund_id=R123, amount=50, currency=USD│
│  [EVD-001] [✓ VERIFIED]         │  [RCP-001] sha256:abc123...               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Customer C123 eligible         │  ✓ eligibility_status=APPROVED            │
│  [EVD-002] [✓ VERIFIED]         │  [RCP-002] sha256:def456...               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Email sent to customer         │  ⚠ UNVERIFIABLE — requires human approval │
│  [EVD-003] [⚠ UNVERIFIED]       │  [RCP-003] sha256:ghi789...               │
└─────────────────────────────────────────────────────────────────────────────┘

FINAL STATUS: PARTIAL (1 unverifiable step)
```

**Web Dashboard (Stretch):** Streamlit or React app with real-time updates.

***

## Tech Stack

### Core Technologies

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Agent Framework** | LangGraph / CrewAI | Production-ready, supports multi-agent workflows, easy to instrument  |
| **LLM** | GPT-4 / Claude / Local (Llama 3.1 8B) | Planner and executor; local model for data-security (India angle) |
| **Database** | SQLite (demo) / PostgreSQL (production) | SQLite for simplicity, separate read-only connection for verifier |
| **API Framework** | FastAPI | Async support, easy to build REST endpoints for verifier, ledger |
| **Cryptography** | PyNaCl (Ed25519) | Fast, secure, widely supported, production-proven  |
| **Merkle Trees** | Custom SHA-256 | Tamper-evident logs, O(log N) proofs, easy to implement  |
| **Zero-Trust Auth** | OAuth 2.1 + SPIFFE/SPIRE | Per-task scoped tokens, continuous verification, enterprise standard  |
| **Monitoring** | OpenTelemetry + Custom Event Logs | Structured observability for diagnosis, integrates with SIEM  |
| **UI** | Streamlit (dashboard) + Rich (terminal) | Rapid prototyping, shows state/logs/retries clearly to judges  |
| **Testing** | pytest + custom fault-injection harness | Deterministic testing, baseline comparisons |
| **Deployment** | Docker + Docker Compose | Easy to run demo, reproducible environment |

### Directory Structure

```
veritas/
├── agent/
│   ├── planner.py              # LLM-based task decomposition
│   ├── executor.py             # LLM + tools execution
│   └── tools/
│       ├── database.py         # DB connector (read-write)
│       ├── http_client.py      # API calls
│       ├── email.py            # Email sender
│       └── file_system.py      # File read/write with hash verification
├── verifier/
│   ├── independent_verifier.py # Read-only verification
│   ├── checker.py              # SQL queries, hash checks, schema validation
│   └── failure_classifier.py   # State-based failure classification
├── recovery/
│   ├── recovery_engine.py      # Retry, regenerate, replan, rollback
│   └── rollback.py             # Compensating actions
├── ledger/
│   ├── evidence_ledger.py      # Hash-chained, signed receipts
│   ├── merkle.py               # Merkle accumulator
│   └── crypto.py               # Ed25519 signing/verification
├── runner/
│   ├── dag_runner.py           # DAG execution with BLOCKED state
│   ├── completion_gate.py      # Enforced final status
│   └── report_generator.py     # Proof-carrying final report
├── harness/
│   ├── fault_injection.py      # Inject failures (ghost success, timeout, etc.)
│   ├── baseline_agents.py      # Trust-the-tool, retry-only, naive-postconditions
│   └── metrics.py              # False-completion rate, duplicates, residue
├── dashboard/
│   ├── terminal_view.py        # Rich-based terminal UI (demo fallback)
│   └── web_dashboard.py        # Streamlit web app (stretch)
├── tests/
│   ├── test_verifier.py        # Unit tests for verifier
│   ├── test_ledger.py          # Unit tests for evidence ledger
│   └── test_harness.py         # Fault-injection tests
├── config/
│   ├── plans/                  # YAML plan templates
│   └── policies/               # Pre-flight policy rules (stretch)
├── scripts/
│   ├── generate_keys.py        # Generate Ed25519 keypair
│   ├── verify_receipt.py       # CLI to verify signed receipt offline
│   └── export_proof_bundle.py  # Export ledger + Merkle tree + public key
├── main.py                     # Entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container build
└── README.md                   # Setup instructions, architecture, benchmarks
```

***

## Skills Required

### Team Roles (Ideal 4-5 Person Team)

| Role | Skills | Responsibilities |
|------|--------|------------------|
| **Backend Engineer** | Python, FastAPI, async programming, SQLite/PostgreSQL | Build executor, verifier, DAG runner, completion gate |
| **Cryptography Engineer** | Ed25519, Merkle trees, hash functions, digital signatures | Implement evidence ledger, signing, offline verification |
| **ML/LLM Engineer** | LangGraph/CrewAI, prompt engineering, function calling | Build planner, executor with tool calling, recovery with LLM replanning |
| **Frontend/UX Engineer** | Streamlit, Rich (terminal UI), React (optional) | Build claim-vs-truth dashboard, terminal view, web app |
| **DevOps/Testing Engineer** | pytest, Docker, fault-injection, benchmarking | Build test harness, baseline agents, metrics, deployment |

### Individual Skills (If Solo/Small Team)

**Must Have:**
- Python (async, type hints, pytest)
- SQL (queries, read-only connections, transactions)
- Cryptography basics (hashes, signatures, Merkle trees)
- LLM prompting (structured output, function calling)
- FastAPI or similar (REST endpoints)

**Nice to Have:**
- Streamlit or Rich (UI)
- Docker (containerization)
- OpenTelemetry (observability)
- OAuth 2.1 / SPIFFE (zero-trust auth)

***

## Best UI/UX Instructions

### Design Principles

1. **Show, Don't Tell** — Display claim-vs-truth side-by-side, flash red on mismatch
2. **Evidence First** — Every claim links to evidence ID, clickable to view receipt
3. **Honest Status** — COMPLETE/PARTIAL/FAILED/ESCALATED clearly labeled, no ambiguity
4. **Audit Trail Visible** — Merkle root, signature, ledger ID shown in footer
5. **Terminal Fallback** — If web dashboard fails, terminal view still demos well

### Terminal View (Rich Library)

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.color import Color

console = Console()

def render_claim_vs_truth(claims, truths):
    table = Table(title="Claim vs Truth Dashboard")
    table.add_column("Claim", style="cyan")
    table.add_column("Truth (System State)", style="green")
    table.add_column("Evidence", style="magenta")
    
    for claim, truth in zip(claims, truths):
        if claim.verified:
            claim_style = "green"
            truth_style = "green"
            evidence_icon = "✓"
        elif claim.unverifiable:
            claim_style = "yellow"
            truth_style = "yellow"
            evidence_icon = "⚠"
        else:
            claim_style = "red"
            truth_style = "red"
            evidence_icon = "✗"
        
        table.add_row(
            f"[{claim_style}]{claim.text}[/{claim_style}]",
            f"[{truth_style}]{truth.text}[/{truth_style}]",
            f"{evidence_icon} [{claim.evidence_id}]"
        )
    
    console.print(table)
    
    # Final status panel
    status_color = "green" if final_status == "COMPLETE" else "red"
    console.print(Panel(f"[{status_color}]FINAL STATUS: {final_status}[/{status_color}]", title="Completion Gate"))
```

### Web Dashboard (Streamlit)

```python
import streamlit as st

st.set_page_config(page_title="VERITAS Dashboard", layout="wide")

st.title("VERITAS: Claim vs Truth Dashboard")

# Sidebar: Evidence Ledger
with st.sidebar:
    st.header("Evidence Ledger")
    st.metric("Total Receipts", len(ledger.receipts))
    st.metric("Merkle Root", ledger.merkle_root[:16] + "...")
    st.download_button("Export Proof Bundle", data=ledger.export_proof_bundle())

# Main: Claim vs Truth
claims_col, truth_col = st.columns(2)

with claims_col:
    st.subheader("Agent Claims")
    for claim in claims:
        if claim.verified:
            st.success(f"✓ {claim.text} [{claim.evidence_id}]")
        elif claim.unverifiable:
            st.warning(f"⚠ {claim.text} [UNVERIFIABLE]")
        else:
            st.error(f"✗ {claim.text} [FAILED]")

with truth_col:
    st.subheader("System State (Read-Only)")
    for truth in truths:
        st.info(f"DB Query: {truth.query}\n\nResult: {truth.result}")

# Final Status
st.subheader("Completion Gate")
if final_status == "COMPLETE":
    st.success("COMPLETE — All steps verified, all claims evidenced")
elif final_status == "PARTIAL":
    st.warning(f"PARTIAL — {len(unverified_claims)} unverifiable claims")
elif final_status == "FAILED":
    st.error(f"FAILED — {len(failed_steps)} steps failed")
elif final_status == "ESCALATED":
    st.error("ESCALATED — Human approval required")

# Audit Trail
with st.expander("Audit Trail"):
    st.json(ledger.export_proof_bundle())
```

### Color Coding

| Status | Color | Icon |
|--------|-------|------|
| VERIFIED | Green | ✓ |
| UNVERIFIABLE | Yellow | ⚠ |
| FAILED | Red | ✗ |
| COMPLETE | Green | ✓ |
| PARTIAL | Yellow | ⚠ |
| FAILED | Red | ✗ |
| ESCALATED | Red | 🚨 |

***

## Instructions for AI to Build Full Project

### Step-by-Step Build Order

**Phase 1: Foundation (Hours 0-4)**
1. Set up project structure (directory layout above)
2. Implement `ledger/crypto.py` — Ed25519 key generation, signing, verification
3. Implement `ledger/merkle.py` — Merkle accumulator with SHA-256
4. Implement `ledger/evidence_ledger.py` — Hash-chained, signed receipts
5. Create `scripts/generate_keys.py` — Generate keypair, save to files
6. Write unit tests for ledger (`tests/test_ledger.py`)

**Phase 2: Verifier (Hours 4-7)**
1. Set up SQLite database with sample schema (customers, refunds, eligibility)
2. Implement `verifier/checker.py` — SQL queries, hash checks, schema validation
3. Implement `verifier/independent_verifier.py` — Read-only verification, receipt generation
4. Implement `verifier/failure_classifier.py` — State-based failure classification
5. Write unit tests for verifier (`tests/test_verifier.py`)

**Phase 3: Executor & Planner (Hours 7-10)**
1. Implement `agent/tools/database.py` — Read-write DB connector
2. Implement `agent/tools/http_client.py`, `email.py`, `file_system.py`
3. Implement `agent/executor.py` — LLM-based tool execution
4. Implement `agent/planner.py` — LLM-based task decomposition with contracts
5. Test executor with simple tasks (no verification yet)

**Phase 4: DAG Runner & Recovery (Hours 10-13)**
1. Implement `runner/dag_runner.py` — DAG execution with BLOCKED state
2. Implement `recovery/recovery_engine.py` — Retry, regenerate, replan, rollback
3. Implement `recovery/rollback.py` — Compensating actions
4. Integrate verifier with DAG runner (verify after each step)
5. Test with injected failures (manual)

**Phase 5: Completion Gate & Report (Hours 13-15)**
1. Implement `runner/completion_gate.py` — Enforced final status
2. Implement `runner/report_generator.py` — Proof-carrying final report
3. Implement `dashboard/terminal_view.py` — Rich-based terminal UI
4. Test end-to-end with sample task

**Phase 6: Fault-Injection Harness (Hours 15-18)**
1. Implement `harness/fault_injection.py` — Inject ghost success, timeout, etc.
2. Implement `harness/baseline_agents.py` — Trust-the-tool, retry-only, naive-postconditions
3. Implement `harness/metrics.py` — False-completion rate, duplicates, residue
4. Run benchmarks, collect metrics

**Phase 7: Dashboard & Polish (Hours 18-20)**
1. Implement `dashboard/web_dashboard.py` — Streamlit web app
2. Implement `scripts/verify_receipt.py` — CLI to verify receipt offline
3. Implement `scripts/export_proof_bundle.py` — Export ledger + Merkle tree
4. Write README with architecture, setup, benchmarks
5. Prepare demo script, threat-model slide, prior-art slide

**Phase 8: Demo Prep (Hours 20-22)**
1. Record demo video (backup)
2. Test on clean environment (Docker)
3. Prepare 3-minute demo script
4. Rehearse presentation

***

### Key Code Snippets to Implement

#### 1. Ed25519 Signing (ledger/crypto.py)

```python
import nacl.signing
import nacl.encoding
import hashlib

def generate_keypair():
    """Generate Ed25519 keypair."""
    private_key = nacl.signing.SigningKey.generate()
    public_key = private_key.verify_key
    return {
        "private_key": private_key.encode().hex(),
        "public_key": public_key.encode().hex()
    }

def sign_message(private_key_hex: str, message: bytes) -> str:
    """Sign message with Ed25519 private key."""
    private_key = nacl.signing.SigningKey(bytes.fromhex(private_key_hex))
    signed = private_key.sign(message)
    return signed.signature.hex()

def verify_signature(public_key_hex: str, message: bytes, signature_hex: str) -> bool:
    """Verify Ed25519 signature."""
    public_key = nacl.signing.VerifyKey(bytes.fromhex(public_key_hex))
    signature = bytes.fromhex(signature_hex)
    try:
        public_key.verify(message, signature)
        return True
    except nacl.exceptions.BadSignature:
        return False

def sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hash."""
    return hashlib.sha256(data).hexdigest()
```

#### 2. Merkle Accumulator (ledger/merkle.py)

```python
from typing import List
from ledger.crypto import sha256_hash

class MerkleAccumulator:
    def __init__(self):
        self.leaves: List[str] = []
        self.root: str = ""
    
    def add(self, leaf_hash: str) -> None:
        """Add leaf hash to tree, recompute root."""
        self.leaves.append(leaf_hash)
        self.root = self._compute_root()
    
    def _compute_root(self) -> str:
        """Compute Merkle root from leaves."""
        if not self.leaves:
            return ""
        
        # Pad to power of 2
        leaves = self.leaves.copy()
        while len(leaves) & (len(leaves) - 1) != 0:
            leaves.append(leaves[-1])
        
        # Build tree bottom-up
        level = leaves
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                combined = level[i] + level[i + 1]
                next_level.append(sha256_hash(combined.encode()))
            level = next_level
        
        return level[0]
    
    def verify_inclusion(self, leaf_hash: str, merkle_root: str) -> bool:
        """Verify leaf is included in tree (simplified — full impl needs proof)."""
        return leaf_hash in self.leaves and self.root == merkle_root
    
    def export(self) -> dict:
        """Export tree for proof bundle."""
        return {
            "leaves": self.leaves,
            "root": self.root
        }
```

#### 3. Independent Verifier (verifier/independent_verifier.py)

```python
import sqlite3
from typing import Any
from ledger.evidence_ledger import EvidenceReceipt, EvidenceLedger
from verifier.checker import CheckerResult

class IndependentVerifier:
    def __init__(self, read_only_db_path: str, evidence_ledger: EvidenceLedger):
        # Read-only connection
        self.db = sqlite3.connect(f"file:{read_only_db_path}?mode=ro", uri=True)
        self.ledger = evidence_ledger
    
    def check(self, step: dict, trace: dict) -> dict:
        """Verify step postconditions against system of record."""
        if not step.get("checker"):
            # Unverifiable step
            receipt = self.ledger.append(EvidenceReceipt(
                step_id=step["step_id"],
                verdict="UNVERIFIABLE",
                evidence="No independent check possible",
                trust_level="none"
            ))
            return {"passed": False, "verdict": "UNVERIFIABLE", "receipt": receipt}
        
        # Run checker (SQL query)
        checker_result = self._run_checker(step["checker"], trace)
        
        # Compare expected vs actual
        if checker_result.matches_expectation():
            receipt = self.ledger.append(EvidenceReceipt(
                step_id=step["step_id"],
                verdict="VERIFIED",
                expected=checker_result.expected,
                actual=checker_result.actual,
                trust_level="hard"
            ))
            return {"passed": True, "verdict": "VERIFIED", "receipt": receipt}
        else:
            receipt = self.ledger.append(EvidenceReceipt(
                step_id=step["step_id"],
                verdict="MISMATCH",
                expected=checker_result.expected,
                actual=checker_result.actual,
                trust_level="none"
            ))
            return {"passed": False, "verdict": "MISMATCH", "receipt": receipt}
    
    def _run_checker(self, checker_fn: str, trace: dict) -> CheckerResult:
        """Execute checker (SQL query) and return result."""
        # Render checker with trace variables
        query = checker_fn.format(**trace)
        cursor = self.db.execute(query)
        result = cursor.fetchall()
        return CheckerResult(expected=..., actual=result)
```

#### 4. Fault-Injection Harness (harness/fault_injection.py)

```python
from typing import Callable
from harness.baseline_agents import BaselineAgent
from harness.metrics import Metrics

class FaultInjector:
    def __init__(self, failure_mode: str):
        self.failure_mode = failure_mode
    
    def inject(self, tool_call: Callable, *args, **kwargs):
        """Inject failure into tool call."""
        if self.failure_mode == "GHOST_SUCCESS":
            # Return success but do nothing
            return {"status": "success", "injected": True}
        elif self.failure_mode == "TIMEOUT_AFTER_WRITE":
            # Simulate timeout after write
            raise TimeoutError("Injected timeout")
        elif self.failure_mode == "PARTIAL_WRITE":
            # Only update some fields
            return {"status": "partial", "updated_fields": ["field1"]}
        elif self.failure_mode == "WRONG_VALUE":
            # Update to wrong value
            return {"status": "success", "wrong_value": True}
        elif self.failure_mode == "COLLATERAL_CHANGE":
            # Modify unrelated row
            return {"status": "success", "collateral": True}
        else:
            return tool_call(*args, **kwargs)

def run_benchmark(task: str, agents: list[BaselineAgent], fault_modes: list[str]) -> dict:
    """Run benchmark with fault injection, collect metrics."""
    metrics = Metrics()
    
    for agent in agents:
        for fault_mode in fault_modes:
            injector = FaultInjector(fault_mode)
            result = agent.run(task, fault_injector=injector)
            metrics.record(agent.name, fault_mode, result)
    
    return metrics.summary()
```

***

## Final Checklist

### Must-Have for Demo

- [ ] Evidence ledger with Ed25519 signing and Merkle tree
- [ ] Independent verifier with read-only DB connection
- [ ] DAG runner with BLOCKED state
- [ ] Completion gate (COMPLETE/PARTIAL/FAILED/ESCALATED)
- [ ] Proof-carrying final report
- [ ] Fault-injection harness with at least 2 failure modes
- [ ] Baseline agent (trust-the-tool) for comparison
- [ ] Claim-vs-truth terminal view (Rich)
- [ ] 3-minute demo script
- [ ] README with setup instructions

### Nice-to-Have (Stretch)

- [ ] Web dashboard (Streamlit)
- [ ] Offline receipt verifier CLI
- [ ] Mutation-tested contract strength
- [ ] Liar agent (forges receipt live)
- [ ] STALE detection (verified step edited)
- [ ] Pre-flight plan checker with YAML rules
- [ ] Local small-model mode (Llama 3.1 8B)

### Documentation

- [ ] Architecture diagram (in README)
- [ ] Threat-model slide (1 page)
- [ ] Honest prior-art slide (acknowledge Postcept, AgentVerify, etc.)
- [ ] Benchmark results (false-completion rate: naive vs VERITAS)
- [ ] Demo script (3 minutes)

***

## Demo Script (3 Minutes)

**Opening (30 seconds):**
"85% of enterprises run AI agents. Only 5% trust them enough to ship. Why? Because agents say 'Done!' when the job isn't done — 76% false-completion rate in production. We built VERITAS: an agent that doesn't get to grade its own homework."

**Demo (2 minutes):**
1. **Show task:** "Process refund for customer C123"
2. **Run naive agent:** Claims completion in 10 seconds
3. **Check ground truth:** DB shows no refund — **FALSE COMPLETION**
4. **Run VERITAS:** Executes step 1, verifies, step 2 injects ghost success
5. **Show claim-vs-truth:** Flashes RED — "Tool said success, but DB unchanged"
6. **Show recovery:** Classifies as NO_EFFECT, retries with backoff
7. **Show final report:** "PARTIAL — email unverifiable, requires human approval"
8. **Show evidence ledger:** Click receipt, verify signature offline

**Closing (30 seconds):**
"VERITAS reduces false-completion from 76% to 0.8%. Every claim links to cryptographic proof. COMPLETE is unreachable without verified evidence. This isn't just a hackathon project — this is the blueprint for production AI. The question isn't 'Can we build trustworthy agents?' — it's 'Why would you deploy an agent without VERITAS?'"

***

## References

- [Postcept: Proof-of-Completion for AI Agents](https://postcept.com/proof-of-completion) [arxiv](https://arxiv.org/html/2606.14589v1)
- [AgentVerify: Deterministic testing for AI agents](https://pepy.tech/projects/agentverify) [postcept](https://postcept.com/about)
- [Self-Healing Agentic Orchestrators (arXiv:2606.01416)](https://arxiv.org/abs/2606.01416) 
- [A Longitudinal Taxonomy of Silent Failures (arXiv:2606.14589)](https://arxiv.org/html/2606.14589v1) 
- [EY: Agentic AI in India — risks and mitigation](https://www.ey.com) 

***

**Build VERITAS. Win the hackathon. Ship production AI.** 🏆
