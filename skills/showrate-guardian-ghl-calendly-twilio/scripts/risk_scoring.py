from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("showrate.risk")


def score_booking(booking: dict, prior_no_shows: int = 0) -> dict:
    lead_time_hours = booking.get("lead_time_hours", 24)
    source = str(booking.get("source", "")).lower()
    prior = booking.get("prior_no_show", False) or prior_no_shows > 0
    day_of_week = booking.get("day_of_week", "")
    hour_local = booking.get("hour_local", 12)

    risk_score = 0
    signals = []

    if lead_time_hours <= 2:
        risk_score += 30
        signals.append("very_short_lead_time")
    elif lead_time_hours <= 6:
        risk_score += 15
        signals.append("short_lead_time")
    elif lead_time_hours <= 24:
        risk_score += 5
        signals.append("moderate_lead_time")

    if prior:
        risk_score += 25
        signals.append("prior_no_show_history")

    if "organic" in source or "referral" in source:
        risk_score -= 10
        signals.append("organic_referral_source")
    elif "paid" in source:
        risk_score += 5
        signals.append("paid_source")
    elif "cold" in source:
        risk_score += 10
        signals.append("cold_source")

    if day_of_week in ("Friday", "Saturday", "Sunday"):
        risk_score += 5
        signals.append("weekend_booking")

    if hour_local < 9 or hour_local > 17:
        risk_score += 5
        signals.append("outside_working_hours")

    risk_score = max(0, min(100, risk_score))

    if risk_score >= 50:
        bucket = "high"
    elif risk_score >= 25:
        bucket = "medium"
    else:
        bucket = "low"

    return {
        "risk_score": risk_score,
        "risk_bucket": bucket,
        "signals": signals,
        "lead_time_hours": lead_time_hours,
        "source": source,
        "prior_no_show": prior,
    }


def determine_reminder_plan(risk: dict, profile: dict) -> list[dict]:
    bucket = risk["risk_bucket"]
    cadence = profile.get("rules", {}).get("reminder_cadence", [])
    plan = []

    for step in cadence:
        timing = step.get("timing", "24h")
        channels = step.get("channels", ["email"])
        purpose = step.get("purpose", "remind")
        plan.append({
            "timing": timing,
            "channels": list(channels),
            "purpose": purpose,
            "triggered": False,
        })

    if bucket == "high":
        plan.append({
            "timing": "1h",
            "channels": ["sms"],
            "purpose": "urgent_confirmation",
            "triggered": False,
        })
        plan.append({
            "timing": "15m",
            "channels": ["sms"],
            "purpose": "last_chance",
            "triggered": False,
        })
    elif bucket == "medium":
        plan.append({
            "timing": "1h",
            "channels": ["sms"],
            "purpose": "confirmation_check",
            "triggered": False,
        })

    return plan


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from common import load_config

    config = load_config()
    test_events = [
        {"lead_time_hours": 1, "source": "paid social", "prior_no_show": False},
        {"lead_time_hours": 30, "source": "organic referral", "prior_no_show": False},
        {"lead_time_hours": 48, "source": "cold email", "prior_no_show": True},
        {"lead_time_hours": 4, "source": "paid ads", "prior_no_show": False, "day_of_week": "Friday", "hour_local": 19},
    ]

    for event in test_events:
        risk = score_booking(event)
        plan = determine_reminder_plan(risk, config)
        print(json.dumps({"event": event, "risk": risk, "plan": plan}, indent=2))
        print("---")
