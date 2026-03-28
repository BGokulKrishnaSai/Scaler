from support_queue_env.graders import grade_record
from support_queue_env.models import SupportQueueAction, TicketRecord
from support_queue_env.server.support_queue_environment import SupportQueueEnvironment
from support_queue_env.tasks import get_task


def test_grader_returns_perfect_score_for_expected_submission():
    task = get_task("medium_duplicate_charge")
    record = TicketRecord(
        queue=task.expected.queue,
        priority=task.expected.priority,
        escalation_team=task.expected.escalation_team,
        status=task.expected.status,
        refund_decision=task.expected.refund_decision,
        refund_amount=task.expected.refund_amount,
        tags=list(task.expected.tags),
        reply_draft=(
            "Our billing team has approved the refund. You will receive the refund "
            "for the duplicate charge, and card processing usually takes 3-5 business days."
        ),
    )
    breakdown = grade_record(record, task)
    assert breakdown["overall"] == 1.0


def test_environment_rewards_progress_and_submission():
    env = SupportQueueEnvironment()
    initial = env.reset(task_id="easy_password_reset")
    first = env.step(
        SupportQueueAction(
            queue="account_access",
            priority="normal",
            status="pending_customer",
            tags=["login", "password_reset"],
            submit=False,
        )
    )
    second = env.step(
        SupportQueueAction(
            escalation_team="none",
            refund_decision="none",
            refund_amount=0.0,
            tags=["login", "password_reset", "mfa"],
            reply_draft=(
                "Please start identity verification first. Once completed, we can issue "
                "a temporary sign-in link. If you still have a backup code available, "
                "you can use it right away."
            ),
            submit=True,
        )
    )
    assert first.reward is not None
    assert first.reward > -0.1
    assert second.done is True
    assert second.score_breakdown["overall"] > initial.score_breakdown["overall"]
