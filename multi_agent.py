"""Multi-agent support coordination framework (optional extension).

This module demonstrates how the Support Queue Environment can be extended
to support multi-agent scenarios where agents coordinate on complex cases.

Example: Routing agent + Specialist agents
--------
Scenario: Complex case requiring cross-team coordination
- Routing Agent: Receives customer case, decides initial queue/priority
- Specialist Agents: Handle specialized aspects (billing, security, etc)
- Coordinator: Aggregates responses into final customer reply

This is a v2 extension pattern; not required for single-agent evaluation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from support_queue_env.models import SupportQueueAction, SupportQueueObservation


@dataclass
class AgentPerspective:
    """What a specialist agent sees of the case."""
    agent_id: str
    specialty: str  # "billing", "security", "technical", "account_access"
    observation: SupportQueueObservation
    local_action: SupportQueueAction | None = None


class SupportAgent(ABC):
    """Base class for support agents (single or multi-agent)."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    
    @abstractmethod
    def process(self, observation: SupportQueueObservation) -> SupportQueueAction:
        """Process an observation and return an action."""
        pass


class RoutingAgent(SupportAgent):
    """Primary agent that routes incoming cases to specialists."""
    
    def process(self, observation: SupportQueueObservation) -> SupportQueueAction:
        """Route incoming case based on content analysis."""
        # Implement routing logic:
        # 1. Parse customer_message for keywords
        # 2. Check account_snapshot for context
        # 3. Route to appropriate queue/escalation_team
        # 4. Set initial priority
        raise NotImplementedError("Implement routing logic for your domain")


class SpecialistAgent(SupportAgent):
    """Specialist agent handling specific domain (billing, security, etc)."""
    
    def __init__(self, agent_id: str, specialty: str):
        super().__init__(agent_id)
        self.specialty = specialty
    
    def process(self, perspective: AgentPerspective) -> SupportQueueAction:
        """Process case from specialist perspective."""
        # Implement specialist logic:
        # - Billing agent: check refund policies, compute amounts
        # - Security agent: assess threat level, recommend escalation
        # - Account agent: verify identity, check recovery options
        raise NotImplementedError(f"Implement {self.specialty} specialist logic")


class MultiAgentCoordinator:
    """Coordinates multi-agent responses into final ticket submission."""
    
    def __init__(self, agents: dict[str, SupportAgent]):
        """Initialize with dictionary of agent_id -> agent."""
        self.agents = agents
        self.history: list[dict[str, Any]] = []
    
    def coordinate(self, observation: SupportQueueObservation, 
                   max_rounds: int = 3) -> SupportQueueAction:
        """Run multi-agent coordination loop.
        
        Args:
            observation: Initial case observation
            max_rounds: Maximum number of coordination rounds
        
        Returns:
            Final action to submit to environment
        """
        current_observation = observation
        
        for round_num in range(max_rounds):
            # Collect perspectives from all agents
            perspectives = {}
            for agent_id, agent in self.agents.items():
                if isinstance(agent, SpecialistAgent):
                    perspective = AgentPerspective(
                        agent_id=agent_id,
                        specialty=agent.specialty,
                        observation=current_observation,
                    )
                    perspectives[agent_id] = perspective
            
            # Let agents process their perspectives
            actions = {}
            for agent_id, agent in self.agents.items():
                if agent_id in perspectives:
                    actions[agent_id] = agent.process(perspectives[agent_id])
            
            # Merge actions into consolidated action
            final_action = self._merge_actions(actions, round_num == max_rounds - 1)
            
            # Record coordination step
            self.history.append({
                "round": round_num,
                "perspectives": perspectives,
                "actions": actions,
                "consolidated": final_action,
            })
            
            # Return on final round
            if round_num == max_rounds - 1:
                return final_action
        
        raise RuntimeError("Coordination loop didn't complete")
    
    def _merge_actions(self, actions: dict[str, SupportQueueAction], 
                       is_final: bool) -> SupportQueueAction:
        """Merge specialist agent actions into final action.
        
        Strategy: Union of non-None fields, with conflict resolution.
        """
        merged = SupportQueueAction()
        
        # Merge all non-None fields, prioritizing by specificity
        field_priority = {
            "queue": 1,           # Most critical
            "priority": 2,
            "escalation_team": 3,
            "status": 4,
            "refund_decision": 5,
            "refund_amount": 6,
            "tags": 7,
            "internal_notes": 8,
            "reply_draft": 9,
            "submit": 10,  # Only set during final round
        }
        
        for agent_id, action in actions.items():
            for field, priority in field_priority.items():
                value = getattr(action, field, None)
                if value is not None:
                    current = getattr(merged, field, None)
                    if current is None:
                        setattr(merged, field, value)
        
        # Set submit flag on final round
        if is_final:
            merged.submit = True
        
        return merged


# Example Usage Pattern:
# ====================
#
# from support_queue_env.client import SupportQueueEnv
# from support_queue_env.multi_agent import (
#     MultiAgentCoordinator, RoutingAgent, SpecialistAgent
# )
#
# # Create specialized agents
# routing_agent = MyRoutingAgent(agent_id="router")
# billing_agent = MyBillingSpecialist(agent_id="billing", specialty="billing")
# security_agent = MySecuritySpecialist(agent_id="security", specialty="security")
#
# # Create coordinator
# coordinator = MultiAgentCoordinator({
#     "router": routing_agent,
#     "billing": billing_agent,
#     "security": security_agent,
# })
#
# # Run multi-agent episode
# with SupportQueueEnv(base_url="http://localhost:8000").sync() as env:
#     obs = env.reset(task_id="medium_duplicate_charge")
#
#     # Multi-agent coordination
#     final_action = coordinator.coordinate(obs, max_rounds=2)
#
#     result = env.step(final_action)
#     print(f"Score: {result.observation.score_breakdown['overall']:.2f}")
#     print(f"Coordination history: {coordinator.history}")
