"""Support Queue environment client."""

from __future__ import annotations

from typing import Any

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from .models import SupportQueueAction, SupportQueueObservation, SupportQueueState


class SupportQueueEnv(
    EnvClient[SupportQueueAction, SupportQueueObservation, SupportQueueState]
):
    """WebSocket client for the Support Queue environment."""

    def _step_payload(self, action: SupportQueueAction) -> dict[str, Any]:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: dict[str, Any]) -> StepResult[SupportQueueObservation]:
        obs = SupportQueueObservation(**payload.get("observation", {}))
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict[str, Any]) -> SupportQueueState:
        return SupportQueueState(**payload)
