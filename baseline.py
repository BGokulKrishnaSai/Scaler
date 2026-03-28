"""Baseline inference script using the OpenAI Python client."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from openai import OpenAI

from support_queue_env.graders import summarize_breakdown
from support_queue_env.models import SupportQueueAction
from support_queue_env.server.support_queue_environment import SupportQueueEnvironment
from support_queue_env.tasks import TASKS

SYSTEM_PROMPT = """You are a senior SaaS customer-support triage specialist.
You must return JSON only.
Fill the support record carefully, follow the policy snippets, and avoid unsafe promises.
Use submit=true only when the record is ready for grading."""


def build_prompt(observation) -> str:
    return json.dumps(
        {
            "task_id": observation.task_id,
            "difficulty": observation.difficulty,
            "title": observation.title,
            "objective": observation.objective,
            "customer_message": observation.customer_message,
            "account_snapshot": observation.account_snapshot,
            "policy_snippets": observation.policy_snippets,
            "current_record": observation.current_record.model_dump(),
            "score_breakdown": observation.score_breakdown,
            "feedback": observation.feedback,
            "required_output_schema": {
                "queue": "optional string",
                "priority": "optional string",
                "escalation_team": "optional string",
                "status": "optional string",
                "refund_decision": "optional string",
                "refund_amount": "optional number",
                "tags": "optional array of strings",
                "internal_notes": "optional string",
                "reply_draft": "optional string",
                "submit": "boolean",
            },
        },
        indent=2,
    )


def parse_action(content: str) -> SupportQueueAction:
    payload = json.loads(content)
    return SupportQueueAction(**payload)


def run_episode(client: OpenAI, model: str, task_id: str, max_agent_steps: int = 3) -> dict:
    env = SupportQueueEnvironment()
    observation = env.reset(task_id=task_id, seed=0)
    trajectory = []

    for step_idx in range(max_agent_steps):
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(observation)},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        action = parse_action(raw)
        if step_idx == max_agent_steps - 1:
            action.submit = True
        observation = env.step(action)
        trajectory.append(
            {
                "step": step_idx + 1,
                "action": action.model_dump(),
                "reward": observation.reward,
                "done": observation.done,
                "score_breakdown": observation.score_breakdown,
                "feedback": observation.feedback,
            }
        )
        if observation.done:
            break

    state = env.state
    return {
        "task_id": task_id,
        "difficulty": observation.difficulty,
        "final_score": state.final_score,
        "cumulative_reward": state.cumulative_reward,
        "summary": summarize_breakdown(state.score_breakdown),
        "trajectory": trajectory,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4.1-mini-2025-04-14")
    parser.add_argument("--output", default="outputs/evals/baseline_scores.json")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to run the baseline.")

    client = OpenAI()
    results = [run_episode(client, args.model, task.task_id) for task in TASKS]
    average_score = sum(item["final_score"] for item in results) / len(results)

    report = {
        "model": args.model,
        "task_count": len(results),
        "average_score": average_score,
        "results": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
