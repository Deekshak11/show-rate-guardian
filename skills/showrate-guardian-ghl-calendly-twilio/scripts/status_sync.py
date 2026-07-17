from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from common import load_config, GHLClient

logger = logging.getLogger("showrate.status_sync")


STATUS_SHOW = "show"
STATUS_NO_SHOW = "no_show"
STATUS_RESCHEDULED = "rescheduled"
STATUS_CONFIRMED = "confirmed"
STATUS_BOOKED = "booked"
STATUS_CANCELLED = "cancelled"

TAG_MAP = {
    STATUS_SHOW: "showrate-show",
    STATUS_NO_SHOW: "showrate-no-show",
    STATUS_RESCHEDULED: "showrate-rescheduled",
    STATUS_CONFIRMED: "showrate-confirmed",
    STATUS_BOOKED: "showrate-booked",
    STATUS_CANCELLED: "showrate-cancelled",
}


class StatusSync:
    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.ghl = GHLClient(lazy=True)
        self.grace_minutes = self.config.get("rules", {}).get("no_show_grace_minutes", 10)
        self.metrics = self.config.get("reporting", {}).get("metrics", [])

    def mark_status(self, contact_id: str, status: str, event_id: str = "", notes: str = "") -> dict:
        tag = TAG_MAP.get(status)
        if not tag:
            return {"success": False, "error": f"Unknown status: {status}"}

        actions = []

        tag_result = self.ghl.add_tag(contact_id, tag)
        actions.append({"action": "add_tag", "tag": tag, "success": tag_result})

        for old_status, old_tag in TAG_MAP.items():
            if old_status != status:
                remove_result = self.ghl.remove_tag(contact_id, old_tag)
                if remove_result:
                    actions.append({"action": "remove_tag", "tag": old_tag, "success": True})

        timestamp = datetime.now(timezone.utc).isoformat()
        note_body = f"[ShowRate Guardian] Status: {status} | Event: {event_id} | Time: {timestamp}"
        if notes:
            note_body += f"\n{notes}"
        note_result = self.ghl.add_note(contact_id, note_body)
        actions.append({"action": "add_note", "success": note_result})

        custom_fields = {}
        if "booked_to_kept" in self.metrics or "no_show_rate" in self.metrics:
            custom_fields["showrate_last_status"] = status
            custom_fields["showrate_last_updated"] = timestamp
        if custom_fields:
            update_result = self.ghl.update_contact(contact_id, custom_fields)
            actions.append({"action": "update_custom_fields", "success": update_result})

        return {"success": True, "contact_id": contact_id, "status": status, "actions": actions}

    def check_no_show(self, contact_id: str, event_time: str, checked_in: bool, event_id: str = "") -> dict:
        from common import hours_until

        hours = hours_until(event_time)
        if hours > 0:
            return {"decision": "pending", "reason": f"Event hasn't happened yet ({hours:.1f}h remaining)"}

        if checked_in:
            return self.mark_status(contact_id, STATUS_SHOW, event_id, "Prospect checked in")

        grace_h = self.grace_minutes / 60
        if abs(hours) < grace_h:
            return {
                "decision": "pending",
                "reason": f"Within grace period ({self.grace_minutes} min)",
                "minutes_past": round(abs(hours) * 60, 1),
            }

        return self.mark_status(
            contact_id, STATUS_NO_SHOW, event_id,
            f"No-show detected after {self.grace_minutes} min grace period",
        )

    def sync_booking_created(self, contact_id: str, event_id: str = "", source: str = "") -> dict:
        return self.mark_status(contact_id, STATUS_BOOKED, event_id, f"Booking created from {source}")

    def sync_confirmed(self, contact_id: str, event_id: str = "") -> dict:
        return self.mark_status(contact_id, STATUS_CONFIRMED, event_id, "Prospect confirmed via reply")

    def sync_rescheduled(self, contact_id: str, old_event_id: str = "", new_event_id: str = "") -> dict:
        return self.mark_status(
            contact_id, STATUS_RESCHEDULED, new_event_id,
            f"Rescheduled from {old_event_id} to {new_event_id}",
        )


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

    config = load_config()
    sync = StatusSync(config)

    results = [
        sync.sync_booking_created("test_contact_1", source="calendly"),
        sync.sync_confirmed("test_contact_1"),
        sync.check_no_show("test_contact_1", "2026-04-25T10:00:00Z", checked_in=False, event_id="evt_1"),
    ]
    for r in results:
        print(json.dumps(r, indent=2))
        print("---")
