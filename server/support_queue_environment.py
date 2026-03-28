"""Environment implementation for real-world support triage."""

from __future__ import annotations

import uuid
from typing import Any

from openenv.core.env_server import Environment
from openenv.core.env_server.types import EnvironmentMetadata

try:
    from ..graders import grade_record, summarize_breakdown
    from ..models import (
        SupportQueueAction,
        SupportQueueObservation,
        SupportQueueState,
        TicketRecord,
    )
    from ..tasks import SupportTaskSpec, pick_task
except ImportError:  # pragma: no cover
    from graders import grade_record, summarize_breakdown
    from models import (
        SupportQueueAction,
        SupportQueueObservation,
        SupportQueueState,
        TicketRecord,
    )
    from tasks import SupportTaskSpec, pick_task


class SupportQueueEnvironment(
    Environment[SupportQueueAction, SupportQueueObservation, SupportQueueState]
):
    """Customer-support triage environment with deterministic grading."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self, max_steps: int = 6):
        super().__init__()
        self.max_steps = max_steps
        self._task: SupportTaskSpec | None = None
        self._state = SupportQueueState(max_steps=max_steps)

    def _get_difficulty_scaled_max_steps(self, difficulty: str) -> int:
        """Scale max_steps by difficulty for fair time budget."""
        difficulty_budgets = {
            "easy": 4,      # Easy tasks: 4 steps (time pressure, but achievable)
            "medium": 6,    # Medium: 6 steps (more time for routing decisions)
            "hard": 8,      # Hard tasks: 8 steps (security reasoning needs time)
        }
        return difficulty_budgets.get(difficulty, self.max_steps)

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="SupportQueueEnvironment",
            description="Customer support ticket triage environment with deterministic grading.",
            version="0.1.0",
            author="OpenAI Codex",
        )

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        task_id: str | None = None,
        **_: Any,
    ) -> SupportQueueObservation:
        self._task = pick_task(seed=seed, task_id=task_id)
        difficulty_scaled_steps = self._get_difficulty_scaled_max_steps(self._task.difficulty)
        self._state = SupportQueueState(
            episode_id=episode_id or str(uuid.uuid4()),
            task_id=self._task.task_id,
            difficulty=self._task.difficulty,
            title=self._task.title,
            max_steps=difficulty_scaled_steps,
            current_record=TicketRecord(),
            score_breakdown=grade_record(TicketRecord(), self._task),
        )
        self._state.last_feedback = (
            "Review the customer issue, use the policy snippets, and patch the support "
            "record. Submit when the case is ready."
        )
        return self._build_observation(reward=0.0, done=False)

    def step(
        self, action: SupportQueueAction, timeout_s: float | None = None, **_: Any
    ) -> SupportQueueObservation:
        del timeout_s
        if self._task is None:
            raise RuntimeError("reset() must be called before step().")
        if self._state.submitted:
            return self._build_observation(
                reward=-0.05,
                done=True,
                feedback="Episode already submitted. Call reset() to start a new task.",
            )

        previous_score = self._state.score_breakdown.get("overall", 0.0)
        changed = self._apply_action(action)
        self._state.step_count += 1
        self._state.score_breakdown = grade_record(self._state.current_record, self._task)
        current_score = self._state.score_breakdown["overall"]

        step_penalty = 0.02
        reward = (current_score - previous_score) * 1.5 - step_penalty
        feedback_parts = [f"Current grade: {summarize_breakdown(self._state.score_breakdown)}."]

        if not changed and not action.submit:
            reward -= 0.05
            feedback_parts.append("No-op action detected; make a meaningful update.")

        if (
            self._task.expected.refund_amount == 0.0
            and self._state.current_record.refund_amount > 0.0
        ):
            reward -= 0.05
            feedback_parts.append("Unexpected refund approval reduced the reward.")

        if action.submit:
            self._state.submitted = True
            self._state.final_score = current_score
            reward += current_score - 0.05
            feedback_parts.append("Ticket submitted and graded.")

        done = action.submit
        if self._state.step_count >= self.max_steps and not done:
            done = True
            self._state.submitted = True
            self._state.final_score = current_score
            reward -= 0.05
            feedback_parts.append("Max step budget reached; episode auto-submitted.")

        self._state.cumulative_reward += reward
        self._state.last_feedback = " ".join(feedback_parts)
        if done and self._state.final_score == 0.0:
            self._state.final_score = current_score

        return self._build_observation(reward=reward, done=done)

    def _apply_action(self, action: SupportQueueAction) -> bool:
        record = self._state.current_record
        before = record.model_dump()
        patch = action.model_dump(exclude_none=True, exclude={"submit", "metadata"})
        if "queue" in patch:
            record.queue = patch["queue"]
        if "priority" in patch:
            record.priority = patch["priority"]
        if "escalation_team" in patch:
            record.escalation_team = patch["escalation_team"]
        if "status" in patch:
            record.status = patch["status"]
        if "refund_decision" in patch:
            record.refund_decision = patch["refund_decision"]
        if "refund_amount" in patch:
            record.refund_amount = float(patch["refund_amount"])
        if "tags" in patch:
            record.tags = sorted({tag.strip().lower() for tag in patch["tags"] if tag.strip()})
        if "internal_notes" in patch:
            record.internal_notes = patch["internal_notes"].strip()
        if "reply_draft" in patch:
            record.reply_draft = patch["reply_draft"].strip()
        return record.model_dump() != before

    def _build_observation(
        self, reward: float, done: bool, feedback: str | None = None
    ) -> SupportQueueObservation:
        assert self._task is not None
        return SupportQueueObservation(
            task_id=self._task.task_id,
            difficulty=self._task.difficulty,
            title=self._task.title,
            objective=self._task.objective,
            customer_message=self._task.customer_message,
            account_snapshot=self._task.account_snapshot,
            policy_snippets=list(self._task.policy_snippets),
            current_record=self._state.current_record.model_copy(deep=True),
            score_breakdown=dict(self._state.score_breakdown),
            feedback=feedback or self._state.last_feedback,
            max_steps=self._state.max_steps,
            reward=reward,
            done=done,
            metadata={
                "episode_id": self._state.episode_id,
                "step_count": self._state.step_count,
                "final_score": self._state.final_score,
            },
        )

    @property
    def state(self) -> SupportQueueState:
        return self._state.model_copy(deep=True)
