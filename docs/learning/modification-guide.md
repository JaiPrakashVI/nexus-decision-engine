# Developer Modification & Extension Guide

This guide explains how to safely modify, extend, and adapt NEXUS without breaking architectural invariants.

---

## 1. How to Add a New Telemetry Sensor Field

To add a new measurement field (e.g. `ph_level` or `turbidity_ntu` for water quality):

1. **Update Pydantic Schema** (`gateway/schemas/telemetry.py`):
   ```python
   ph_level: float = Field(default=7.0, ge=0.0, le=14.0, description="Water pH acidity index")
   ```
2. **Update Database Model** (`database/schemas/models.py`):
   ```python
   # In class TelemetryReading:
   ph_level = Column(Float, default=7.0)
   ```
3. **Update Database Migration** (`database/migrations/init.sql`):
   ```sql
   ALTER TABLE telemetry ADD COLUMN IF NOT EXISTS ph_level DOUBLE PRECISION DEFAULT 7.0;
   ```
4. **Update Sensor Simulator** (`simulator/device_simulator.py`):
   Generate realistic physical values for `ph_level` in `generate_reading()`.
5. **Update Unit Tests** (`tests/unit/test_gateway_validation.py`):
   Verify valid ranges and rejection of out-of-bounds inputs.

---

## 2. How to Add a New API Endpoint

To expose a new analytical endpoint in the Digital Twin API:

1. **Open `digital_twin/api.py`**.
2. **Define request/response schemas** using Pydantic if accepting a body.
3. **Define route handler**:
   ```python
   @app.get("/api/v1/analytics/water-quality")
   async def get_water_quality():
       # Query database or digital twin
       return {"average_ph": 7.2, "status": "NOMINAL"}
   ```
4. **Update Frontend API Client** (`dashboard/src/App.tsx` or new component).
5. **Add Integration Test** (`tests/integration/test_pipeline.py`).

---

## 3. How to Add a New Anomaly Detector

To implement a new detection algorithm (e.g. Seasonal Trend Decomposition or CUSUM):

1. **Create detector file** in `anomaly_detection/diagnostics/` (e.g. `cusum_detector.py`).
2. **Implement standard interface**:
   ```python
   class CUSUMDetector:
       def check_reading(self, device_id: str, value: float) -> Tuple[bool, str, float, str]:
           # Returns: (is_anomaly, anomaly_type, anomaly_score, severity)
           ...
   ```
3. **Register in Evaluator** (`anomaly_detection/diagnostics/evaluator.py`) to benchmark its precision, recall, and latency against labeled synthetic test datasets.
4. **Add Unit Test** in `tests/unit/test_anomaly_and_missing_events.py`.

---

## 4. How to Add a New Candidate Intervention

To enable a new operational action (e.g. `THROTTLE_PRESSURE_REDUCING_VALVE`):

1. **Update Permitted Actions List** in `agents/prompts/templates.py`:
   Add `THROTTLE_PRESSURE_REDUCING_VALVE` to `RECOVERY_PLANNER_PROMPT`.
2. **Implement Physical Action Logic** in `simulation/cascading_failures/engine.py`:
   Define how throttling the valve reduces downstream pressure head and alleviates line stress.
3. **Add Constraint Rules** in `agents/decision_support/engine.py:DeterministicDecisionEngine._verify_constraints`:
   Ensure the target valve is operational and not stuck/jammed.
4. **Verify via Simulation** in `tests/unit/test_simulation_and_decisions.py`.

---

## 5. How to Add a New Specialized Agent Role

To add a new agent (e.g. `EnvironmentalComplianceAgent`):

1. **Define Role Prompt** in `agents/prompts/templates.py` with explicit role description, reasoning constraints, and output JSON schema.
2. **Add Workflow Step** in `agents/evaluation/multi_agent_workflow.py:MultiAgentOrchestrator.execute_workflow`:
   ```python
   compliance_resp = await llm_client.generate_structured(
       system_prompt=COMPLIANCE_AGENT_PROMPT,
       user_prompt=f"Review intervention for environmental compliance:\n{context_str}",
       expected_schema_name="ComplianceAgent"
   )
   ```
3. **Include Feedback in Chief Evaluator Prompt**:
   Feed compliance feedback into the final evaluation step so non-compliant actions are rejected.
