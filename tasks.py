"""Seeded real-world support tasks for the environment."""

from __future__ import annotations

import random
from dataclasses import dataclass

try:
    from .models import Difficulty
except ImportError:  # pragma: no cover
    from models import Difficulty


@dataclass(frozen=True)
class ExpectedOutcome:
    queue: str
    priority: str
    escalation_team: str
    status: str
    refund_decision: str
    refund_amount: float
    tags: tuple[str, ...]
    required_reply_keywords: tuple[str, ...]
    forbidden_reply_keywords: tuple[str, ...]


@dataclass(frozen=True)
class SupportTaskSpec:
    task_id: str
    difficulty: Difficulty
    title: str
    objective: str
    customer_message: str
    account_snapshot: str
    policy_snippets: tuple[str, ...]
    expected: ExpectedOutcome


TASKS: tuple[SupportTaskSpec, ...] = (
    SupportTaskSpec(
        task_id="easy_password_reset",
        difficulty="easy",
        title="Locked Out After MFA Device Change",
        objective=(
            "Triage an account-access request and draft a safe first response that "
            "follows the account recovery runbook."
        ),
        customer_message=(
            "Subject: Can't log in after switching phones\n\n"
            "Hi team, I got a new phone this morning and my authenticator app didn't "
            "transfer over. Now I can't get into AcmeCloud and I need to review "
            "tomorrow's deployment checklist today. Can you please help me get back in?"
        ),
        account_snapshot=(
            "Plan: Growth annual\n"
            "Workspace: northstar-analytics\n"
            "Role: Workspace admin\n"
            "Last successful login: 2026-03-22 08:14 UTC\n"
            "No billing holds. No prior security incidents."
        ),
        policy_snippets=(
            "Account recovery policy: never ask the customer to share a password or current MFA code.",
            "For lost authenticator access, instruct the user to start identity verification before issuing a temporary sign-in link.",
            "Recommend backup codes if previously generated, and remind the user to re-enroll MFA after access is restored.",
        ),
        expected=ExpectedOutcome(
            queue="account_access",
            priority="normal",
            escalation_team="none",
            status="pending_customer",
            refund_decision="none",
            refund_amount=0.0,
            tags=("login", "password_reset", "mfa"),
            required_reply_keywords=(
                "identity verification",
                "temporary sign-in link",
                "backup code",
            ),
            forbidden_reply_keywords=(
                "share your password",
                "disable 2fa permanently",
            ),
        ),
    ),
    SupportTaskSpec(
        task_id="medium_duplicate_charge",
        difficulty="medium",
        title="Duplicate Renewal Charge Needs Refund",
        objective=(
            "Route the ticket to billing operations, approve the refund, and send a "
            "realistic customer reply that sets the right expectations."
        ),
        customer_message=(
            "Subject: We were charged twice for the same renewal\n\n"
            "Hello, our finance team says invoice INV-4018 and INV-4018A both posted "
            "today for the same Pro renewal. We only intended to renew once after "
            "removing an extra workspace last week. Please reverse the duplicate charge "
            "as soon as possible because our controller is closing books tomorrow."
        ),
        account_snapshot=(
            "Plan: Pro monthly\n"
            "Workspace count: 3 active\n"
            "Duplicate payment detected by risk service: yes\n"
            "Duplicate charge amount: $499.00\n"
            "Account health: good standing"
        ),
        policy_snippets=(
            "Billing policy: confirmed duplicate charges can be refunded in full without additional approval.",
            "Billing operations owns refund execution and receipt issuance.",
            "Support agents must not guarantee same-day bank settlement; state that card refunds usually appear in 3-5 business days.",
        ),
        expected=ExpectedOutcome(
            queue="billing",
            priority="high",
            escalation_team="billing_ops",
            status="escalated",
            refund_decision="full",
            refund_amount=499.0,
            tags=("duplicate_charge", "refund", "invoice"),
            required_reply_keywords=(
                "billing team",
                "refund",
                "3-5 business days",
            ),
            forbidden_reply_keywords=(
                "guarantee immediate bank posting",
                "file a chargeback",
            ),
        ),
    ),
    SupportTaskSpec(
        task_id="hard_admin_compromise",
        difficulty="hard",
        title="Potential Admin Account Compromise",
        objective=(
            "Handle a possible security incident: assign the correct queue and urgency, "
            "escalate immediately, and draft a containment-focused response without "
            "making unsafe promises."
        ),
        customer_message=(
            "Subject: Suspicious admin login and unknown data export\n\n"
            "Urgent. We saw an admin login from a country where none of our team is "
            "located, followed by a bulk CSV export about 20 minutes later. The admin "
            "now can't explain the activity and we think the session may have been "
            "hijacked. What should we do right now?"
        ),
        account_snapshot=(
            "Plan: Enterprise\n"
            "SSO enabled: yes\n"
            "Admin users: 4\n"
            "SIEM signal: anomalous session flagged at 2026-03-25 11:42 UTC\n"
            "Recent data export job id: exp_88219"
        ),
        policy_snippets=(
            "Security runbook: suspected compromise is always urgent and must be escalated to Security Response immediately.",
            "First-response guidance should instruct the customer to revoke active sessions, rotate API keys, and review recent privileged actions.",
            "Never ask the customer to send passwords or promise that no data was accessed until the investigation is complete.",
        ),
        expected=ExpectedOutcome(
            queue="security",
            priority="urgent",
            escalation_team="security_response",
            status="escalated",
            refund_decision="none",
            refund_amount=0.0,
            tags=("security_incident", "data_export", "admin_account"),
            required_reply_keywords=(
                "security team",
                "revoke active sessions",
                "rotate api keys",
            ),
            forbidden_reply_keywords=(
                "send us your password",
                "we guarantee no data left the system",
            ),
        ),
    ),
)

TASK_INDEX = {task.task_id: task for task in TASKS}


def _generate_context_variant(task_id: str, seed: int) -> dict:
    """Generate procedural context variations while preserving expected outcomes.
    
    This allows infinite task variety while keeping deterministic grading.
    Uses seed for reproducibility.
    """
    rng = random.Random(seed)
    base_task = TASK_INDEX[task_id]
    
    if task_id == "easy_password_reset":
        # Vary devices: phones, laptops, tablets
        devices = ["new phone", "new laptop", "new tablet", "new device"]
        device = rng.choice(devices)
        
        # Vary authentication method names
        auth_names = ["authenticator app", "MFA app", "2FA authenticator", "authentication tool"]
        auth_name = rng.choice(auth_names)
        
        # Vary urgency context
        urgencies = [
            "and I need to review tomorrow's deployment checklist today",
            "and I have a meeting in 30 minutes",
            "and I need to access critical files",
            "and my team is waiting for my approval"
        ]
        urgency = rng.choice(urgencies)
        
        customer_msg = (
            f"Subject: Can't log in after switching {device}\n\n"
            f"Hi team, I got a {device} this morning and my {auth_name} didn't transfer over. "
            f"Now I can't get into AcmeCloud {urgency}. Can you please help me get back in?"
        )
        
        return {
            "customer_message": customer_msg,
            "account_snapshot": base_task.account_snapshot,  # Keep consistent
            "policy_snippets": base_task.policy_snippets,    # Keep consistent
        }
    
    elif task_id == "medium_duplicate_charge":
        # Vary charge amounts (but keep similar scale)
        amounts = [399.0, 449.0, 499.0, 549.0, 599.0]
        amount = rng.choice(amounts)
        
        # Vary invoice IDs
        inv_num = rng.randint(4000, 5000)
        inv_ids = f"INV-{inv_num} and INV-{inv_num}A"
        
        # Vary urgency context
        contexts = [
            "our controller is closing books tomorrow",
            "our accounting team needs this resolved today",
            "we're reconciling with our bank",
            "our CFO is reviewing this"
        ]
        context = rng.choice(contexts)
        
        customer_msg = (
            f"Subject: We were charged twice for the same renewal\n\n"
            f"Hello, our finance team says invoice {inv_ids} both posted today for the same Pro renewal. "
            f"We only intended to renew once after removing an extra workspace last week. "
            f"Please reverse the duplicate charge as soon as possible because {context}."
        )
        
        account_snapshot = (
            f"Plan: Pro monthly\n"
            f"Workspace count: 3 active\n"
            f"Duplicate payment detected by risk service: yes\n"
            f"Duplicate charge amount: ${amount:.2f}\n"
            f"Account health: good standing"
        )
        
        return {
            "customer_message": customer_msg,
            "account_snapshot": account_snapshot,
            "policy_snippets": base_task.policy_snippets,
        }
    
    elif task_id == "hard_admin_compromise":
        # Vary locations
        locations = ["a country where none of our team is located",
                    "an unusual geographic location",
                    "outside our normal business region",
                    "an unexpected international location"]
        location = rng.choice(locations)
        
        # Vary export types
        exports = ["bulk CSV export", "data export", "bulk data dump", "export job"]
        export_type = rng.choice(exports)
        
        # Vary time frames
        timeframes = ["20 minutes later", "15 minutes later", "immediately after", "shortly after"]
        timeframe = rng.choice(timeframes)
        
        customer_msg = (
            f"Subject: Suspicious admin login and unknown data export\n\n"
            f"Urgent. We saw an admin login from {location}, "
            f"followed by a {export_type} about {timeframe}. "
            f"The admin now can't explain the activity and we think the session may have been "
            f"hijacked. What should we do right now?"
        )
        
        return {
            "customer_message": customer_msg,
            "account_snapshot": base_task.account_snapshot,
            "policy_snippets": base_task.policy_snippets,
        }
    
    # Default: return base task as-is
    return {
        "customer_message": base_task.customer_message,
        "account_snapshot": base_task.account_snapshot,
        "policy_snippets": base_task.policy_snippets,
    }


def apply_context_variant(task: SupportTaskSpec, variant: dict) -> SupportTaskSpec:
    """Apply procedural context variant to a task."""
    from dataclasses import replace
    return replace(
        task,
        customer_message=variant.get("customer_message", task.customer_message),
        account_snapshot=variant.get("account_snapshot", task.account_snapshot),
        policy_snippets=variant.get("policy_snippets", task.policy_snippets),
    )


def get_task(task_id: str) -> SupportTaskSpec:
    """Return a specific task by id."""
    return TASK_INDEX[task_id]


def pick_task(seed: int | None = None, task_id: str | None = None, use_procedural: bool = True) -> SupportTaskSpec:
    """Select a deterministic task either by id or seed.
    
    Args:
        seed: Random seed for task selection (0-2 for base tasks, >2 for procedural variants)
        task_id: Specific task ID to load
        use_procedural: If True and seed provided, generate procedural context variants
    
    Returns:
        SupportTaskSpec with potentially procedurally-varied context
    """
    if task_id is not None:
        task = get_task(task_id)
    else:
        rng = random.Random(seed)
        task = rng.choice(list(TASKS))
        task_id = task.task_id
    
    # If seed provided and use_procedural is True, apply context variations
    if seed is not None and use_procedural and seed >= 0:
        variant = _generate_context_variant(task_id, seed)
        task = apply_context_variant(task, variant)
    
    return task
