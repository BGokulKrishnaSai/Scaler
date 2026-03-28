"""FastAPI app for the Support Queue environment."""

from __future__ import annotations

from openenv.core.env_server.http_server import create_app

try:
    from ..models import SupportQueueAction, SupportQueueObservation
    from .support_queue_environment import SupportQueueEnvironment
except ImportError:  # pragma: no cover
    from models import SupportQueueAction, SupportQueueObservation
    from server.support_queue_environment import SupportQueueEnvironment


app = create_app(
    SupportQueueEnvironment,
    SupportQueueAction,
    SupportQueueObservation,
    env_name="support_queue_env",
    max_concurrent_envs=8,
)


def main(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
