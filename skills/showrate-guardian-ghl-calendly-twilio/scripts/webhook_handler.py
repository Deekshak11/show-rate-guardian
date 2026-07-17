from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from common import load_config, verify_calendly_signature, CalendlyClient, GHLClient
from risk_scoring import score_booking, determine_reminder_plan
from reminder_dispatcher import ReminderDispatcher
from status_sync import StatusSync

logger = logging.getLogger("showrate.webhook")


def handle_calendly_webhook(payload: dict, config: dict | None = None) -> dict:
    config = config or load_config()
    event = payload.get("event", "")
    payload_data = payload.get("payload", {})

    dispatcher = ReminderDispatcher(config)
    status_sync = StatusSync(config)
    calendly = CalendlyClient(lazy=True)
    ghl = GHLClient(lazy=True)

    result = {"event": event, "actions": [], "errors": []}

    invitee = payload_data.get("invitee", {})
    event_data = payload_data.get("event", {})
    tracking = payload_data.get("tracking", {})

    invitee_email = invitee.get("email", "")
    invitee_name = invitee.get("name", "")
    invitee_phone = ""
    for question in invitee.get("questions", []):
        if question.get("name", "").lower() in ("phone", "phone number", "mobile"):
            invitee_phone = str(question.get("answer", "")).strip()

    event_time = event_data.get("start_time", "")
    event_uri = event_data.get("uri", "")
    event_id = event_uri.split("/")[-1] if event_uri else ""

    utm_source = tracking.get("utm_source", "unknown")
    lead_time_hours = 24
    if event_time:
        from common import hours_until
        lead_time_hours = hours_until(event_time)

    booking_data = {
        "lead_time_hours": lead_time_hours,
        "source": utm_source,
        "prior_no_show": False,
    }

    ghl_contact_id = ""
    if invitee_email:
        try:
            search = ghl._search_contact_by_email(invitee_email)
            if search:
                ghl_contact_id = search.get("id", "")
        except Exception:
            pass

    if event == "invitee.created":
        risk = score_booking(booking_data)
        plan = determine_reminder_plan(risk, config)

        result["risk"] = risk
        result["reminder_plan"] = plan

        sync_result = status_sync.sync_booking_created(
            ghl_contact_id or "pending", event_id, utm_source,
        )
        result["actions"].append({"type": "status_sync", "result": sync_result})

        first_name = invitee_name.split()[0] if invitee_name else "there"
        meeting_local = event_time

        dispatch_results = dispatcher.dispatch_plan(
            phone=invitee_phone,
            email=invitee_email,
            first_name=first_name,
            meeting_time_local=meeting_local,
            plan=plan,
        )
        result["actions"].append({"type": "reminders_dispatched", "results": dispatch_results})

    elif event == "invitee.canceled":
        reason = payload_data.get("cancellation_reason", "Cancelled by prospect")
        if ghl_contact_id:
            sync_result = status_sync.mark_status(ghl_contact_id, "cancelled", event_id, reason)
            result["actions"].append({"type": "status_sync", "result": sync_result})

    else:
        result["actions"].append({"type": "ignored", "reason": f"Unhandled event: {event}"})

    return result


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

    test_payload = {
        "event": "invitee.created",
        "payload": {
            "invitee": {
                "email": "test@example.com",
                "name": "Test User",
                "questions": [{"name": "Phone", "answer": "+919876543210"}],
            },
            "event": {
                "start_time": "2026-04-26T15:00:00+05:30",
                "uri": "https://api.calendly.com/scheduled_events/test-event-123",
            },
            "tracking": {"utm_source": "paid social"},
        },
    }

    result = handle_calendly_webhook(test_payload)
    print(json.dumps(result, indent=2, default=str))
