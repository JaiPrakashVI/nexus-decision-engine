"""
Unit tests for Cascading Failure Simulation and Deterministic Decision Engine.
"""

import pytest
from simulation.cascading_failures.engine import CascadingSimulationEngine
from agents.decision_support.engine import DeterministicDecisionEngine
from digital_twin.graph.topology import topology, OperationalState


def test_cascading_simulation_propagates_blast_radius():
    engine = CascadingSimulationEngine()
    # Simulate failure on primary pump_01
    report = engine.simulate_failure("pump_01", disruption_type="NODE_FAILURE", max_steps=6)
    assert report.trigger_node == "pump_01"
    assert len(report.timeline) > 1
    # Downstream dependencies should be affected
    assert len(report.cascaded_nodes) > 0
    assert report.estimated_unserved_demand > 0.0


def test_intervention_mitigates_cascade():
    engine = CascadingSimulationEngine()
    # Simulate backup pump activation
    sim_res = engine.simulate_intervention(
        trigger_node_id="pump_01",
        action_name="ACTIVATE_BACKUP_PUMP",
        target_nodes=["pump_03"]
    )
    assert sim_res["constraints_passed"] is True
    assert sim_res["mitigated_assets_count"] > 0
    assert sim_res["post_intervention_blast_radius"] < sim_res["pre_intervention_blast_radius"]


def test_deterministic_decision_engine_enforces_constraints():
    decision_engine = DeterministicDecisionEngine()

    # Fail backup pump in topology temporarily
    backup_node = topology.get_node("pump_03")
    assert backup_node is not None
    original_state = backup_node.operational_state
    backup_node.operational_state = OperationalState.FAILED

    try:
        passed, violations = decision_engine._verify_constraints("ACTIVATE_BACKUP_PUMP", ["pump_03"])
        # Should fail constraint because target pump is failed!
        assert passed is False
        assert any("FAILED" in v for v in violations)
    finally:
        backup_node.operational_state = original_state


def test_decision_plan_synthesis_ranks_interventions():
    decision_engine = DeterministicDecisionEngine()
    plan = decision_engine.evaluate_incident("inc_test_01", "pump_01", "HIGH")
    assert len(plan.candidate_interventions) > 0
    assert plan.recommended_action is not None
    assert plan.recommended_action.constraints_satisfied is True
