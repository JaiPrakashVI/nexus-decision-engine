# Component Deep-Dive: Deterministic Decision Engine

The Deterministic Decision Engine (`agents/decision_support/engine.py`) provides mathematically verified, constraint-checked operational recovery plans for physical infrastructure disruptions.

---

## 1. Architectural Philosophy
In cyber-physical critical infrastructure, automated decisions must be:
1. **Deterministic**: Identical state inputs must yield identical, reproducible intervention recommendations.
2. **Safe**: Must never violate physical constraints (e.g., closing a valve that creates catastrophic water hammer, or activating a pump whose power draw exceeds substation rating).
3. **Simulated Before Execution**: Every candidate action must be tested inside the digital twin simulation sandbox before recommendation to human operators.

---

## 2. Decision Workflow

1. **Incident Intake**:
   Receives incident definition: `root_cause_node`, `severity`, and computes downstream `affected_nodes` using graph reachability (`nx.descendants`).
2. **Candidate Generation**:
   Generates domain-specific standard operating procedures (SOPs):
   - `ACTIVATE_BACKUP_PUMP`: Spin up auxiliary pump (`pump_03`) to bypass failed primary pump.
   - `OPEN_BYPASS_VALVE`: Reroute transmission flow via cross-connect lines.
   - `ISOLATE_ZONE`: Close isolation valves to contain ruptured pipes and prevent backflow.
   - `LOAD_SHEDDING`: Throttle non-critical demand sectors to prevent substation transformer overload.
3. **Constraint Enforcement**:
   - *Target Availability Constraint*: Target asset must exist and not be in `FAILED` state.
   - *Capacity Constraint*: Substation power draw must not exceed rated capacity.
   - *Pressure Boundary Constraint*: Fluid pressure must remain below burst rating ($< 120\text{ PSI}$).
4. **Sandbox Simulation**:
   Each constraint-compliant candidate is simulated in the sandbox engine (`simulation_engine.simulate_intervention(...)`), measuring:
   - `pre_intervention_blast_radius`
   - `post_intervention_blast_radius`
   - `mitigated_assets_count`
   - `simulated_recovery_time_sec` (Recovery Time Objective)
5. **Multi-Objective Scoring & Ranking**:
   $$\text{Score} = (\text{MitigatedAssets} \times 25.0) - (\text{RecoveryTime} \times 1.2)$$
   The candidate with the highest positive score is selected as the `recommended_action`.
