#!/usr/bin/env python
"""Quick demo of the Support Queue Environment in action."""

from support_queue_env.models import SupportQueueAction
from support_queue_env.server.support_queue_environment import SupportQueueEnvironment
from support_queue_env.graders import summarize_breakdown

print("\n" + "="*70)
print("SUPPORT QUEUE ENVIRONMENT - LIVE DEMO")
print("="*70)

# Initialize environment
env = SupportQueueEnvironment()

# Run easy task
print("\n📋 TASK 1: easy_password_reset")
print("-" * 70)
obs = env.reset(task_id="easy_password_reset", seed=0)
print(f"Task: {obs.title}")
print(f"Difficulty: {obs.difficulty}")
print(f"Objective: {obs.objective}")
print(f"\nCustomer Message:\n{obs.customer_message}")
print(f"\nPolicy Snippets:")
for i, policy in enumerate(obs.policy_snippets, 1):
    print(f"  {i}. {policy}")

print("\n🔧 AGENT ACTION 1: Set queue and priority")
action1 = SupportQueueAction(
    queue="account_access",
    priority="normal",
)
obs = env.step(action1)
print(f"  Reward: {obs.reward:+.3f}")
print(f"  Current Score: {obs.score_breakdown['overall']:.2f}")
print(f"  Feedback: {obs.feedback}")

print("\n🔧 AGENT ACTION 2: Add tags and status")
action2 = SupportQueueAction(
    status="pending_customer",
    tags=["login", "password_reset", "mfa"],
)
obs = env.step(action2)
print(f"  Reward: {obs.reward:+.3f}")
print(f"  Current Score: {obs.score_breakdown['overall']:.2f}")
print(f"  Feedback: {obs.feedback}")

print("\n🔧 AGENT ACTION 3: Draft reply and submit")
action3 = SupportQueueAction(
    escalation_team="none",
    refund_decision="none",
    reply_draft=(
        "Please complete identity verification first. Once that is done, we can issue "
        "a temporary sign-in link. If you still have a backup code available, "
        "you can use it right away."
    ),
    submit=True,
)
obs = env.step(action3)
print(f"  Reward: {obs.reward:+.3f}")
print(f"  Done: {obs.done}")
print(f"  Final Score: {obs.score_breakdown['overall']:.2f}")
print(f"\nFinal Grader Breakdown:")
print(f"  {summarize_breakdown(obs.score_breakdown)}")

state = env.state
print(f"\nEpisode State:")
print(f"  Cumulative Reward: {state.cumulative_reward:+.3f}")
print(f"  Final Score: {state.final_score:.2f}")
print(f"  Submitted: {state.submitted}")

# Run medium task
print("\n\n📋 TASK 2: medium_duplicate_charge")
print("-" * 70)
env = SupportQueueEnvironment()
obs = env.reset(task_id="medium_duplicate_charge", seed=0)
print(f"Task: {obs.title}")
print(f"Difficulty: {obs.difficulty}")
print(f"Objective: {obs.objective}")
print(f"\nCustomer Message:\n{obs.customer_message}")

print("\n🔧 AGENT ACTION: Full submission")
action = SupportQueueAction(
    queue="billing",
    priority="high",
    escalation_team="billing_ops",
    status="escalated",
    refund_decision="full",
    refund_amount=499.0,
    tags=["duplicate_charge", "refund", "invoice"],
    internal_notes="Verified duplicate charge via risk service. Approved full refund per billing policy.",
    reply_draft=(
        "Our billing team has approved the refund for the duplicate charge. "
        "The refund will appear on your card within 3-5 business days. "
        "We apologize for the inconvenience."
    ),
    submit=True,
)
obs = env.step(action)
print(f"  Final Score: {obs.score_breakdown['overall']:.2f}")
print(f"  Grader Breakdown: {summarize_breakdown(obs.score_breakdown)}")

# Run hard task
print("\n\n📋 TASK 3: hard_admin_compromise")
print("-" * 70)
env = SupportQueueEnvironment()
obs = env.reset(task_id="hard_admin_compromise", seed=0)
print(f"Task: {obs.title}")
print(f"Difficulty: {obs.difficulty}")
print(f"Objective: {obs.objective}")
print(f"\nCustomer Message:\n{obs.customer_message}")

print("\n🔧 AGENT ACTION: Security escalation")
action = SupportQueueAction(
    queue="security",
    priority="urgent",
    escalation_team="security_response",
    status="escalated",
    tags=["security_incident", "data_export", "admin_account"],
    internal_notes="SIEM signal flagged. Admin session from anomalous location followed by bulk export. Immediate investigation required.",
    reply_draft=(
        "We've detected suspicious activity on your admin account. "
        "Please immediately revoke all active sessions and rotate your API keys. "
        "Our security team will contact you shortly with investigation details."
    ),
    submit=True,
)
obs = env.step(action)
print(f"  Final Score: {obs.score_breakdown['overall']:.2f}")
print(f"  Grader Breakdown: {summarize_breakdown(obs.score_breakdown)}")

print("\n" + "="*70)
print("✅ All tasks completed successfully!")
print("="*70)
print("\n🚀 Server is running at http://localhost:8000")
print("📚 API docs available at http://localhost:8000/docs")
print("\n")
