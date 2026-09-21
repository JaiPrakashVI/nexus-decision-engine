"""
NEXUS Multi-Agent Ensemble Workflow
Coordinates State Analyst, Risk Analyst, Recovery Planner, Adversarial Critic, and Evaluator.
Validates candidate actions in the simulation sandbox and enforces strict constraint boundaries.
"""

from typing import Dict, List, Any
import logging
from dataclasses import dataclass, field
import json

from agents.llm.client import llm_client
from agents.prompts.templates import (
    STATE_ANALYST_PROMPT,
    RISK_ANALYST_PROMPT,
    RECOVERY_PLANNER_PROMPT,
    ADVERSARIAL_CRITIC_PROMPT,
    EVALUATOR_PROMPT,
)
from agents.decision_support.engine import deterministic_engine
from simulation.cascading_failures.engine import simulation_engine
from digital_twin.graph.topology import topology

logger = logging.getLogger("nexus.agents.workflow")


@dataclass
class MultiAgentResponse:
    incident_id: str
    root_cause_node: str
    state_analysis: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    recovery_plan: Dict[str, Any]
    critic_review: Dict[str, Any]
    evaluator_decision: Dict[str, Any]
    simulated_outcome: Dict[str, Any]
    constraints_passed: bool


class MultiAgentOrchestrator:
    def __init__(self):
        pass

    async def execute_workflow(
        self,
        incident_id: str,
        root_cause_node: str,
        severity: str = "HIGH"
    ) -> MultiAgentResponse:
        """
        Runs the full 5-agent deliberation and simulation validation loop.
        """
        node = topology.get_node(root_cause_node)
        downstream = topology.get_downstream_blast_radius(root_cause_node)

        # Context summary provided to agents
        context = {
            "incident_id": incident_id,
            "root_cause_node": root_cause_node,
            "node_type": node.node_type if node else "unknown",
            "severity": severity,
            "downstream_blast_radius": downstream,
            "available_assets": list(topology.get_all_nodes().keys()),
        }
        context_str = json.dumps(context, indent=2)

        # 1. State Analyst Agent
        state_resp = await llm_client.generate_structured(
            system_prompt=STATE_ANALYST_PROMPT,
            user_prompt=f"Current digital twin context:\n{context_str}",
            expected_schema_name="StateAnalyst"
        )

        # 2. Risk Analyst Agent
        risk_resp = await llm_client.generate_structured(
            system_prompt=RISK_ANALYST_PROMPT,
            user_prompt=f"Assess cascade risk for:\n{context_str}",
            expected_schema_name="RiskAnalyst"
        )

        # 3. Recovery Planner Agent
        planner_resp = await llm_client.generate_structured(
            system_prompt=RECOVERY_PLANNER_PROMPT,
            user_prompt=f"Propose recovery plan for incident:\n{context_str}",
            expected_schema_name="RecoveryPlanner"
        )
        plan_data = planner_resp.get("data", {})
        action_name = plan_data.get("recommended_action", "ACTIVATE_BACKUP_PUMP")
        targets = plan_data.get("target_nodes", ["pump_03"])

        # 4. Adversarial Critic Agent
        critic_resp = await llm_client.generate_structured(
            system_prompt=ADVERSARIAL_CRITIC_PROMPT,
            user_prompt=f"Critique this recovery plan:\nAction: {action_name}\nTargets: {targets}\nContext:\n{context_str}",
            expected_schema_name="AdversarialCritic"
        )

        # 5. Physics & Simulation Validation
        passed, violations = deterministic_engine._verify_constraints(action_name, targets)
        sim_res = simulation_engine.simulate_intervention(
            trigger_node_id=root_cause_node,
            action_name=action_name,
            target_nodes=targets
        )

        # 6. Evaluator Agent
        eval_resp = await llm_client.generate_structured(
            system_prompt=EVALUATOR_PROMPT,
            user_prompt=(
                f"Evaluate intervention:\nPlan: {action_name} on {targets}\n"
                f"Critic: {critic_resp.get('data')}\n"
                f"Simulation Outcome: {sim_res}\n"
                f"Constraints Passed: {passed}"
            ),
            expected_schema_name="Evaluator"
        )

        return MultiAgentResponse(
            incident_id=incident_id,
            root_cause_node=root_cause_node,
            state_analysis=state_resp.get("data", {}),
            risk_analysis=risk_resp.get("data", {}),
            recovery_plan=plan_data,
            critic_review=critic_resp.get("data", {}),
            evaluator_decision=eval_resp.get("data", {}),
            simulated_outcome=sim_res,
            constraints_passed=passed,
        )


multi_agent_orchestrator = MultiAgentOrchestrator()
