# Component Deep-Dive: Local Agentic AI Ensemble

The Agentic AI layer in NEXUS (`agents/evaluation/multi_agent_workflow.py`) integrates locally hosted Large Language Models (Ollama) into an advisory ensemble that collaborates with the Deterministic Decision Engine.

---

## 1. Safety Isolation Principles
1. **Advisory Role Only**: The LLM NEVER directly controls or executes infrastructure actions.
2. **Strict JSON Schema Enforcement**: Every agent output is parsed and validated against strict Pydantic models. Malformed JSON is rejected.
3. **Deterministic Pre- & Post-Validation**: Any action suggested by the LLM is subjected to deterministic constraint solving and digital twin simulation before being presented to operators.
4. **Resilient Local Execution**: If Ollama is offline or experiences latency timeouts, the client automatically falls back to deterministic research agent logic with zero system downtime.

---

## 2. The 5 Specialized Agent Roles

### Role 1: State Analyst Agent
- **Purpose**: Synthesizes noisy, incomplete, and inferred telemetry into an objective natural-language diagnostic assessment.
- **Input**: List of observed vs inferred nodes, current hydraulic pressures, flow rates, and data completeness ratio.
- **Output**: Diagnostic summary, data quality rating (`HIGH`/`MEDIUM`/`LOW`), and anomalous asset list.

### Role 2: Risk Analyst Agent
- **Purpose**: Analyzes topological dependencies to forecast secondary cascade escalations.
- **Input**: Failed node, downstream blast radius, reservoir depletion rates, substation load ratios.
- **Output**: Severity assessment (`CRITICAL`/`HIGH`/`MEDIUM`), list of cascading vulnerabilities, criticality score.

### Role 3: Recovery Planner Agent
- **Purpose**: Formulates physical intervention candidates to restore system equilibrium.
- **Constraint**: Must choose exclusively from validated SOP actions (`ACTIVATE_BACKUP_PUMP`, `OPEN_BYPASS_VALVE`, `ISOLATE_ZONE`, `LOAD_SHEDDING`).
- **Output**: Recommended action, target node IDs, parameter settings, and operational reasoning.

### Role 4: Adversarial Critic Agent
- **Purpose**: Actively challenges the proposed recovery plan, searching for blindspots, physical transient hazards, or power overloads.
- **Output**: Detailed critique, list of constraint warnings, risk flag boolean.

### Role 5: Chief Evaluator Agent
- **Purpose**: Synthesizes the recovery proposal, adversarial critique, and simulated digital twin sandbox outcomes into a final recommendation.
- **Output**: Final action recommendation, validation status (`APPROVED`/`MODIFIED`/`REJECTED`), expected recovery time, and verified blast radius reduction percentage.
