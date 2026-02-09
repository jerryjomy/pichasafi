from __future__ import annotations

import logging
from app import database as db

logger = logging.getLogger(__name__)


def check_usage(phone: str) -> dict:
    """
    Check if user can create an image.
    Returns dict with allowed, used, limit, remaining, tier.
    """
    user = db.get_user_by_phone(phone)
    if not user:
        return {"allowed": False, "used": 0, "limit": 0, "tier": "none", "remaining": 0}

    used = user["images_created_this_month"]
    limit = user["monthly_limit"]
    tier = user["subscription_tier"]

    return {
        "allowed": used < limit,
        "used": used,
        "limit": limit,
        "tier": tier,
        "remaining": max(0, limit - used),
    }


def record_usage(phone: str) -> dict | None:
    """Increment image count after successful generation."""
    return db.increment_image_count(phone)


def get_usage_message(phone: str) -> str:
    """Human-readable usage status."""
    usage = check_usage(phone)
    if usage["tier"] == "none":
        return "No account found. Send any message to get started!"

    return (
        f"*Usage this month:*\n"
        f"Images created: {usage['used']}/{usage['limit']}\n"
        f"Remaining: {usage['remaining']}\n"
        f"Plan: {usage['tier'].title()}"
    )


def get_limit_reached_message() -> str:
    """Message shown when user hits their free limit."""
    return (
        "You've used all your free images this month!\n\n"
        "Upgrade to continue creating:\n"
        "*Starter* — 30 images/month — TZS 15,000\n"
        "*Pro* — 100 images/month — TZS 35,000\n"
        "*Business* — Unlimited — TZS 75,000\n\n"
        "Type *subscribe* to upgrade."
    )
