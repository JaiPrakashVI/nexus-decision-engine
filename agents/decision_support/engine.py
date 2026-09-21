"""
NEXUS Deterministic Decision Engine & Constraint Solver
Evaluates incidents, enforces operational constraints, simulates candidate interventions, and produces ranked plans.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

from digital_twin.graph.topology import topology, OperationalState
from simulation.cascading_failures.engine import simulation_engine

logger = logging.getLogger("nexus.decision_engine")


@dataclass
class CandidateIntervention:
    action_name: str
    target_nodes: List[str]
    parameters: Dict[str, Any]
    constraints_satisfied: bool
    constraint_violations: List[str]
    pre_blast_radius: int
    post_blast_radius: int
    mitigated_assets_count: int
    simulated_recovery_time_sec: float
    score: float
    rationale: str


@dataclass
class DecisionPlan:
    incident_id: str
    root_cause_node: str
    severity: str
    affected_nodes: List[str]
    candidate_interventions: List[CandidateIntervention]
    recommended_action: Optional[CandidateIntervention]
    execution_mode: str = "DETERMINISTIC"


class DeterministicDecisionEngine:
    def __init__(self):
        pass

    def evaluate_incident(
        self,
        incident_id: str,
        root_cause_node: str,
        severity: str = "HIGH",
        affected_nodes: Optional[List[str]] = None
    ) -> DecisionPlan:
        """
        Synthesizes candidate actions, verifies constraints, simulates outcomes, and returns ranked decision plan.
        """
        # Determine affected nodes from topology if not provided
        if not affected_nodes:
            affected_nodes = [root_cause_node] + topology.get_downstream_blast_radius(root_cause_node)

        node = topology.get_node(root_cause_node)
        node_type = node.node_type if node else "sensor"

        # Generate candidate interventions based on asset type
        candidates_raw = self._generate_candidates(root_cause_node, node_type, affected_nodes)

        evaluated_candidates: List[CandidateIntervention] = []

        for cand in candidates_raw:
            # 1. Enforce Constraints
            passed, violations = self._verify_constraints(cand["action_name"], cand["target_nodes"])

            # 2. Simulate Outcome in Sandbox
            if passed:
                sim_res = simulation_engine.simulate_intervention(
                    trigger_node_id=root_cause_node,
                    action_name=cand["action_name"],
                    target_nodes=cand["target_nodes"]
                )
                pre_blast = sim_res["pre_intervention_blast_radius"]
                post_blast = sim_res["post_intervention_blast_radius"]
                mitigated = sim_res["mitigated_assets_count"]
                rto = sim_res["simulated_recovery_time_sec"]

                # Multi-objective utility score: higher is better
                score = round((mitigated * 25.0) - (rto * 1.2), 2)
            else:
                pre_blast = len(affected_nodes)
                post_blast = pre_blast
                mitigated = 0
                rto = 999.0
                score = -100.0

            evaluated_candidates.append(
                CandidateIntervention(
                    action_name=cand["action_name"],
                    target_nodes=cand["target_nodes"],
                    parameters=cand["parameters"],
                    constraints_satisfied=passed,
                    constraint_violations=violations,
                    pre_blast_radius=pre_blast,
                    post_blast_radius=post_blast,
                    mitigated_assets_count=mitigated,
                    simulated_recovery_time_sec=rto,
                    score=score,
                    rationale=cand["rationale"],
                )
            )

        # Rank candidates by score descending
        valid_candidates = [c for c in evaluated_candidates if c.constraints_satisfied]
        valid_candidates.sort(key=lambda x: x.score, reverse=True)

        recommended = valid_candidates[0] if valid_candidates else None

        return DecisionPlan(
            incident_id=incident_id,
            root_cause_node=root_cause_node,
            severity=severity,
            affected_nodes=affected_nodes,
            candidate_interventions=evaluated_candidates,
            recommended_action=recommended,
        )

    def _generate_candidates(self, node_id: str, node_type: str, affected: List[str]) -> List[Dict[str, Any]]:
        candidates = []

        if node_type in {"pump", "source"}:
            candidates.append({
                "action_name": "ACTIVATE_BACKUP_PUMP",
                "target_nodes": ["pump_03"],
                "parameters": {"target_rpm": 1750, "target_pressure": 80.0},
                "rationale": "Spin up auxiliary backup pump to restore downstream hydraulic pressure head.",
            })
            candidates.append({
                "action_name": "OPEN_BYPASS_VALVE",
                "target_nodes": ["valve_02"],
                "parameters": {"opening_percentage": 100},
                "rationale": "Open bypass valve to route flow through secondary trunk line B.",
            })
            candidates.append({
                "action_name": "ISOLATE_ZONE",
                "target_nodes": ["valve_01"],
                "parameters": {"closed": True},
                "rationale": "Isolate damaged pump to prevent backflow and cavitation damage.",
            })
        elif node_type == "pipe":
            candidates.append({
                "action_name": "ISOLATE_ZONE",
                "target_nodes": [node_id],
                "parameters": {"isolate": True},
                "rationale": "Close isolation valves upstream and downstream of damaged pipe section.",
            })
            candidates.append({
                "action_name": "OPEN_BYPASS_VALVE",
                "target_nodes": ["valve_02", "valve_03"],
                "parameters": {"reroute": True},
                "rationale": "Reroute district supply around ruptured line via cross-connect.",
            })
        else:
            candidates.append({
                "action_name": "LOAD_SHEDDING",
                "target_nodes": affected[-2:] if len(affected) >= 2 else affected,
                "parameters": {"shed_ratio": 0.5},
                "rationale": "Throttle consumption in non-critical sectors to maintain grid balance.",
            })

        return candidates

    def _verify_constraints(self, action_name: str, target_nodes: List[str]) -> tuple[bool, List[str]]:
        violations = []
        for target in target_nodes:
            target_node = topology.get_node(target)
            if not target_node:
                violations.append(f"Constraint Violation: Target node '{target}' does not exist in topology.")
                continue

            # Cannot target a failed asset for activation
            if action_name == "ACTIVATE_BACKUP_PUMP" and target_node.operational_state == OperationalState.FAILED:
                violations.append(f"Constraint Violation: Backup pump '{target}' is currently marked FAILED.")

            # Power constraint check
            if target_node.node_type == "substation" and target_node.current_power > target_node.capacity:
                violations.append(f"Constraint Violation: Power draw exceeds substation '{target}' rating.")

        return (len(violations) == 0, violations)


deterministic_engine = DeterministicDecisionEngine()
