from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from common import load_config, hours_until, TwilioClient

logger = logging.getLogger("showrate.reminder")


def render_sms_reminder(template: str, first_name: str, meeting_time_local: str) -> str:
    body = template.replace("{{first_name}}", first_name)
    body = body.replace("{{meeting_time_local}}", meeting_time_local)
    return body[:1600]


def render_email_subject(template: str) -> str:
    lines = template.strip().splitlines()
    for line in lines:
        if line.lower().startswith("subject:"):
            return line.split(":", 1)[1].strip()
    return "Confirming your upcoming call"


def render_email_body(template: str, first_name: str, meeting_time_local: str) -> str:
    body = template.replace("{{first_name}}", first_name)
    body = body.replace("{{meeting_time_local}}", meeting_time_local)
    lines = body.strip().splitlines()
    if lines and lines[0].lower().startswith("subject:"):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines = lines[1:]
    return "\n".join(lines)


class ReminderDispatcher:
    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.twilio = TwilioClient(lazy=True)
        self._email_client = None
        self.sms_template = ""
        self.email_template = ""
        self.reschedule_template = ""
        self.noshow_template = ""
        self._load_templates()

    def _load_templates(self):
        templates_path = __import__("pathlib").Path(__file__).resolve().parent.parent / "templates" / "messages.md"
        if not templates_path.exists():
            return
        content = templates_path.read_text(encoding="utf-8")
        sections = content.split("## ")
        for section in sections:
            if section.startswith("Reminder - SMS"):
                self.sms_template = section.split("\n", 1)[1] if "\n" in section else ""
            elif section.startswith("Confirmation - Email"):
                self.email_template = section
            elif section.startswith("Reschedule Reply"):
                self.reschedule_template = section.split("\n", 1)[1] if "\n" in section else ""
            elif section.startswith("No-show Recovery"):
                self.noshow_template = section.split("\n", 1)[1] if "\n" in section else ""

    def send_sms(self, to: str, first_name: str, meeting_time_local: str, purpose: str = "remind") -> dict | None:
        if purpose == "urgent_confirmation":
            body = f"Hi {first_name}, URGENT: please confirm your call at {meeting_time_local}. Reply YES or RESCHEDULE."
        elif purpose == "last_chance":
            body = f"Hi {first_name}, your call at {meeting_time_local} is in 15 min. Still on? Reply YES or RESCHEDULE."
        elif purpose == "noshow_recovery":
            body = render_sms_reminder(self.noshow_template, first_name, meeting_time_local)
        else:
            body = render_sms_reminder(self.sms_template, first_name, meeting_time_local)

        if not body:
            logger.warning("No SMS template for purpose: %s", purpose)
            return None
        return self.twilio.send_sms(to, body)

    def send_email(self, to: str, first_name: str, meeting_time_local: str, purpose: str = "confirm") -> dict | None:
        subject = render_email_subject(self.email_template)
        body = render_email_body(self.email_template, first_name, meeting_time_local)
        logger.info("Would send email to %s: %s", to, subject)
        return {"status": "logged", "to": to, "subject": subject}

    def dispatch_plan(self, phone: str, email: str, first_name: str, meeting_time_local: str, plan: list[dict]) -> list[dict]:
        results = []
        for step in plan:
            channels = step.get("channels", [])
            purpose = step.get("purpose", "remind")
            step_result = {"timing": step.get("timing"), "purpose": purpose, "sent": []}

            if "sms" in channels and phone:
                result = self.send_sms(phone, first_name, meeting_time_local, purpose)
                step_result["sent"].append({"channel": "sms", "result": result})
            if "email" in channels and email:
                result = self.send_email(email, first_name, meeting_time_local, purpose)
                step_result["sent"].append({"channel": "email", "result": result})

            results.append(step_result)
        return results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))

    config = load_config()
    dispatcher = ReminderDispatcher(config)
    plan = [
        {"timing": "24h", "channels": ["email"], "purpose": "confirm"},
        {"timing": "2h", "channels": ["sms"], "purpose": "remind"},
    ]
    results = dispatcher.dispatch_plan(
        phone="+919876543210",
        email="test@example.com",
        first_name="Demo",
        meeting_time_local="Tomorrow at 3:00 PM IST",
        plan=plan,
    )
    print(json.dumps(results, indent=2))
