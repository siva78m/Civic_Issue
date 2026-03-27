import math
from datetime import datetime
from typing import Optional


# Severity score mapping
SEVERITY_SCORES = {
    "LOW": 2.5,
    "MEDIUM": 5.0,
    "HIGH": 7.5,
    "CRITICAL": 10.0,
}

# Urgency score mapping
URGENCY_SCORES = {
    "LOW": 2.5,
    "MEDIUM": 5.0,
    "HIGH": 7.5,
    "IMMEDIATE": 10.0,
}


def calculate_mcia_priority(
    severity: str,
    urgency: str,
    upvote_count: int = 0,
    created_at: Optional[datetime] = None,
) -> tuple[float, dict]:
    """
    Multimodal Civic Intelligence Algorithm (MCIA) Priority Score Calculator.

    Formula:
        Priority = (Severity × 0.40) + (Urgency × 0.30) + (Community × 0.20) + (Recency × 0.10)

    Weights:
        - Severity (40%): How serious/dangerous the issue is
        - Urgency (30%): How time-critical resolution is
        - Community (20%): Citizen engagement via upvotes (capped at 10)
        - Recency (10%): Exponential decay over 30 days (newer issues get higher scores)

    Returns:
        Tuple of (priority_score: float, breakdown: dict)
    """
    if created_at is None:
        created_at = datetime.now()

    # Component scores
    severity_score = SEVERITY_SCORES.get(severity.upper(), 5.0)
    urgency_score = URGENCY_SCORES.get(urgency.upper(), 5.0)

    # Community score: grows with upvotes, capped at 10
    community_score = min(upvote_count * 0.5, 10.0)

    # Recency score: exponential decay over 30 days
    age_in_days = (datetime.now() - created_at).total_seconds() / 86400
    recency_score = 10.0 * math.exp(-age_in_days / 30.0)

    # Weighted MCIA formula
    priority_score = (
        severity_score * 0.40
        + urgency_score * 0.30
        + community_score * 0.20
        + recency_score * 0.10
    )

    # Round to 2 decimal places
    priority_score = round(priority_score, 2)

    breakdown = {
        "severity_score": round(severity_score, 2),
        "urgency_score": round(urgency_score, 2),
        "community_score": round(community_score, 2),
        "recency_score": round(recency_score, 2),
        "weighted_severity": round(severity_score * 0.40, 2),
        "weighted_urgency": round(urgency_score * 0.30, 2),
        "weighted_community": round(community_score * 0.20, 2),
        "weighted_recency": round(recency_score * 0.10, 2),
        "age_in_days": round(age_in_days, 1),
        "upvote_count": upvote_count,
    }

    return priority_score, breakdown


def get_priority_label(score: float) -> str:
    if score >= 8.0:
        return "Critical Priority"
    elif score >= 6.0:
        return "High Priority"
    elif score >= 4.0:
        return "Medium Priority"
    else:
        return "Low Priority"
