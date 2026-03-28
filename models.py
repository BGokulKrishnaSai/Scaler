"""Typed models for the Support Queue environment."""

from __future__ import annotations

from typing import Literal

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field

QueueName = Literal["account_access", "billing", "security", "technical"]
PriorityName = Literal["low", "normal", "high", "urgent"]
EscalationTeam = Literal["none", "billing_ops", "tech_support", "security_response"]
TicketStatus = Literal["open", "pending_customer", "escalated", "resolved"]
RefundDecision = Literal["none", "partial", "full"]
Difficulty = Literal["easy", "medium", "hard"]


class TicketRecord(State):
    """The mutable support record being edited by the agent."""

    queue: QueueName | None = Field(default=None, description="Primary queue assignment")
    priority: PriorityName | None = Field(default=None, description="Ticket urgency")
    escalation_team: EscalationTeam = Field(
        default="none", description="Specialist team handling escalation"
    )
    status: TicketStatus = Field(default="open", description="Current ticket status")
    refund_decision: RefundDecision = Field(
        default="none", description="Refund disposition for the case"
    )
    refund_amount: float = Field(
        default=0.0, ge=0.0, description="Refund amount approved in USD"
    )
    tags: list[str] = Field(default_factory=list, description="Structured ticket tags")
    internal_notes: str = Field(
        default="", description="Internal triage summary for the support team"
    )
    reply_draft: str = Field(
        default="", description="Customer-facing reply drafted by the agent"
    )


class SupportQueueAction(Action):
    """Patch-style action for triaging and submitting a support ticket."""

    queue: QueueName | None = Field(default=None)
    priority: PriorityName | None = Field(default=None)
    escalation_team: EscalationTeam | None = Field(default=None)
    status: TicketStatus | None = Field(default=None)
    refund_decision: RefundDecision | None = Field(default=None)
    refund_amount: float | None = Field(default=None, ge=0.0)
    tags: list[str] | None = Field(default=None)
    internal_notes: str | None = Field(default=None)
    reply_draft: str | None = Field(default=None)
    submit: bool = Field(
        default=False, description="Finalize the ticket and trigger grading"
    )


class SupportQueueObservation(Observation):
    """Observation shown to the agent after each step."""

    task_id: str = Field(description="Unique task identifier")
    difficulty: Difficulty = Field(description="Task difficulty level")
    title: str = Field(description="Short task title")
    objective: str = Field(description="What the agent should accomplish")
    customer_message: str = Field(description="Raw inbound customer email or message")
    account_snapshot: str = Field(description="Relevant CRM and account context")
    policy_snippets: list[str] = Field(
        default_factory=list, description="Relevant policy or runbook excerpts"
    )
    current_record: TicketRecord = Field(description="Current editable support record")
    score_breakdown: dict[str, float] = Field(
        default_factory=dict, description="Current grader component scores"
    )
    feedback: str = Field(default="", description="Environment feedback on the last step")
    max_steps: int = Field(default=6, description="Episode step budget")


class SupportQueueState(State):
    """Internal episode state exposed through state()."""

    task_id: str = Field(default="")
    difficulty: Difficulty = Field(default="easy")
    title: str = Field(default="")
    max_steps: int = Field(default=6)
    submitted: bool = Field(default=False)
    final_score: float = Field(default=0.0)
    cumulative_reward: float = Field(default=0.0)
    last_feedback: str = Field(default="")
    current_record: TicketRecord = Field(default_factory=TicketRecord)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
