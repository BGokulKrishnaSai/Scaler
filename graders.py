"""Deterministic graders for support queue submissions."""

from __future__ import annotations

import math
import re

try:
    from .models import TicketRecord
    from .tasks import SupportTaskSpec
except ImportError:  # pragma: no cover
    from models import TicketRecord
    from tasks import SupportTaskSpec


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _exact(actual: str | None, expected: str) -> float:
    return 1.0 if actual == expected else 0.0


def _refund_score(record: TicketRecord, task: SupportTaskSpec) -> float:
    decision_score = _exact(record.refund_decision, task.expected.refund_decision)
    expected_amount = task.expected.refund_amount
    if expected_amount == 0:
        amount_score = 1.0 if math.isclose(record.refund_amount, 0.0, abs_tol=0.01) else 0.0
    else:
        delta = abs(record.refund_amount - expected_amount)
        amount_score = max(0.0, 1.0 - (delta / expected_amount))
    return 0.5 * decision_score + 0.5 * amount_score


def _tags_score(record: TicketRecord, task: SupportTaskSpec) -> float:
    expected = {tag.lower() for tag in task.expected.tags}
    actual = {tag.lower() for tag in record.tags}
    if not expected and not actual:
        return 1.0
    if not expected:
        return 0.0
    return len(expected & actual) / len(expected)


def _keyword_present(text: str, keyword: str) -> bool:
    """Check if keyword appears in text with word-boundary matching.
    
    Handles: singular/plural, word forms, substrings as words.
    Example: "security team" matches "security teams" and "security team members"
    """
    text_norm = _normalize(text)
    kw_norm = _normalize(keyword)
    
    # Exact substring match is primary (handles "identity verification" in text)
    if kw_norm in text_norm:
        return True
    
    # For single-word keywords, check if word appears with boundaries
    if " " not in kw_norm:
        words = text_norm.split()
        # Exact word match
        if kw_norm in words:
            return True
        # Prefix match (security -> security_incident, securities, etc)
        if any(word.startswith(kw_norm) for word in words):
            return True
    
    return False


def _reply_score(record: TicketRecord, task: SupportTaskSpec) -> float:
    """Score reply draft based on required and forbidden keywords.
    
    Required keywords contribute positively (0-1 range).
    Forbidden keywords penalize heavily (1.0 to 0.0 range).
    """
    reply = _normalize(record.reply_draft)
    if not reply:
        return 0.0
    
    required = task.expected.required_reply_keywords
    forbidden = task.expected.forbidden_reply_keywords
    
    # Required keywords: count matches with semantic keyword detection
    required_hits = sum(1 for keyword in required if _keyword_present(reply, keyword))
    required_score = required_hits / max(1, len(required))
    
    # Forbidden keywords: penalize heavily if any appear
    forbidden_hits = sum(1 for keyword in forbidden if _keyword_present(reply, keyword))
    forbidden_penalty = max(0.0, 1.0 - forbidden_hits / max(1, len(forbidden)))
    
    # Combined score: both required and forbidden matter equally
    return required_score * forbidden_penalty


def grade_record(record: TicketRecord, task: SupportTaskSpec) -> dict[str, float]:
    """Return a deterministic 0-1 score breakdown."""
    breakdown = {
        "queue": _exact(record.queue, task.expected.queue),
        "priority": _exact(record.priority, task.expected.priority),
        "escalation_team": _exact(record.escalation_team, task.expected.escalation_team),
        "status": _exact(record.status, task.expected.status),
        "refund": _refund_score(record, task),
        "tags": _tags_score(record, task),
        "reply": _reply_score(record, task),
    }
    weights = {
        "queue": 0.2,
        "priority": 0.15,
        "escalation_team": 0.15,
        "status": 0.1,
        "refund": 0.15,
        "tags": 0.1,
        "reply": 0.15,
    }
    breakdown["overall"] = sum(breakdown[key] * weights[key] for key in weights)
    return breakdown


def summarize_breakdown(breakdown: dict[str, float]) -> str:
    """Generate a concise human-readable grader summary."""
    important = [
        f"{name}={score:.2f}"
        for name, score in breakdown.items()
        if name != "overall"
    ]
    return f"overall={breakdown.get('overall', 0.0):.2f}; " + ", ".join(important)
