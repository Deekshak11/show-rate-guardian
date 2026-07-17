from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from common import load_config, CalendlyClient, GHLClient, hours_until

logger = logging.getLogger("showrate.reschedule")


INTENT_RESCHEDULE = "reschedule"
INTENT_CONFIRM = "confirm"
INTENT_CANCEL = "cancel"
INTENT_UNKNOWN = "unknown"


def parse_intent(body: str) -> str:
    text = body.strip().lower()
    reschedule_keywords = ["reschedule", "move", "change time", "different time", "can't make", "cannot make", "need another", "rebook", "switch"]
    confirm_keywords = ["yes", "confirm", "confirmed", "still on", "coming", "will be there", "see you", "on my way"]
    cancel_keywords = ["cancel", "cancelled", "not interested", "stop", "unsubscribe"]

    for kw in cancel_keywords:
        if kw in text:
            return INTENT_CANCEL
    for kw in reschedule_keywords:
        if kw in text:
            return INTENT_RESCHEDULE
    for kw in confirm_keywords:
        if kw in text:
            return INTENT_CONFIRM
    return INTENT_UNKNOWN


def check_reschedule_allowed(booking_time: str, profile: dict) -> dict:
    rules = profile.get("rules", {})
    window = rules.get("reschedule_window", "allow until 2h before meeting")
    hours = hours_until(booking_time)

    cutoff_hours = 2
    match = re.search(r"(\d+)\s*h", window)
    if match:
        cutoff_hours = int(match.group(1))

    allowed = hours > cutoff_hours
    return {
        "allowed": allowed,
        "hours_until_booking": round(hours, 1),
        "cutoff_hours": cutoff_hours,
        "window_description": window,
    }


class RescheduleHandler:
    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.calendly = CalendlyClient(lazy=True)
        self.ghl = GHLClient(lazy=True)

    def handle_sms_reply(self, from_number: str, body: str, booking: dict) -> dict:
        intent = parse_intent(body)
        result = {"from": from_number, "intent": intent, "actions": []}

        if intent == INTENT_CONFIRM:
            result["actions"].append({"type": "mark_confirmed", "status": "confirmed"})
            if booking.get("ghl_contact_id"):
                self.ghl.add_tag(booking["ghl_contact_id"], "showrate-confirmed")
            return result

        if intent == INTENT_CANCEL:
            result["actions"].append({"type": "cancel_booking", "status": "cancelled"})
            if booking.get("calendly_uri"):
                self.calendly.cancel_event(booking["calendly_uri"], "Cancelled by prospect via SMS")
            if booking.get("ghl_contact_id"):
                self.ghl.add_tag(booking["ghl_contact_id"], "showrate-cancelled")
            return result

        if intent == INTENT_RESCHEDULE:
            check = check_reschedule_allowed(booking.get("event_time", ""), self.config)
            if not check["allowed"]:
                result["actions"].append({
                    "type": "reschedule_denied",
                    "reason": f"Outside reschedule window ({check['window_description']})",
                    "hours_until": check["hours_until_booking"],
                })
                return result

            result["actions"].append({
                "type": "reschedule_initiated",
                "status": "rescheduling",
                "hours_until": check["hours_until_booking"],
            })
            if booking.get("ghl_contact_id"):
                self.ghl.add_tag(booking["ghl_contact_id"], "showrate-rescheduling")
            return result

        result["actions"].append({"type": "unknown_intent", "body": body})
        return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

    config = load_config()
    handler = RescheduleHandler(config)

    test_replies = [
        ("+919876543210", "yes confirmed!", {"event_time": "2026-04-26T15:00:00+05:30", "ghl_contact_id": "test1"}),
        ("+919876543210", "can we reschedule?", {"event_time": "2026-04-26T15:00:00+05:30", "ghl_contact_id": "test2"}),
        ("+919876543210", "cancel please", {"event_time": "2026-04-26T15:00:00+05:30", "ghl_contact_id": "test3"}),
        ("+919876543210", "maybe later", {"event_time": "2026-04-26T15:00:00+05:30"}),
    ]

    for number, body, booking in test_replies:
        result = handler.handle_sms_reply(number, body, booking)
        print(json.dumps(result, indent=2))
        print("---")
