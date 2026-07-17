from __future__ import annotations

import json
import re
from pathlib import Path


def load_profile(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Profile files use JSON syntax stored in .yaml files for zero-dependency portability. "
            f"Could not parse {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Profile must be a YAML mapping: {path}")
    return normalize_profile(data)


def dump_yaml(data: dict) -> str:
    return json.dumps(data, indent=2)


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return cleaned or "showrate"


def normalize_profile(profile: dict) -> dict:
    client = profile.setdefault("client", {})
    client.setdefault("name", "Unnamed ShowRate Guardian")
    client["slug"] = slugify(client.get("slug") or client["name"])
    client.setdefault("timezone", "UTC")

    goal = profile.setdefault("goal", {})
    goal.setdefault("primary_metric", "booked_to_kept")
    goal.setdefault("target_lift", "20-30% relative")

    stack = profile.setdefault("stack", {})
    stack.setdefault("crm", "unknown")
    stack.setdefault("scheduler", "unknown")
    stack.setdefault("calendar", "unknown")
    stack.setdefault("sms", "none")
    stack.setdefault("email", "none")
    stack.setdefault("telephony", "none")

    channels = profile.setdefault("channels", {})
    channels.setdefault("primary", ["email"])
    channels.setdefault("fallback", ["manual"])

    rules = profile.setdefault("rules", {})
    rules.setdefault(
        "reminder_cadence",
        [
            {"timing": "24h", "channels": ["email"], "purpose": "confirm"},
            {"timing": "2h", "channels": ["sms"], "purpose": "remind"},
        ],
    )
    rules.setdefault("confirmation_required", True)
    rules.setdefault("reschedule_window", "allow until 2h before meeting")
    rules.setdefault("working_hours", "09:00-18:00 local closer time")
    rules.setdefault("no_show_grace_minutes", 10)
    rules.setdefault("timezone_policy", "booking timezone, fallback to closer timezone")
    rules.setdefault("escalation", "manual fallback after second failed write")

    reporting = profile.setdefault("reporting", {})
    reporting.setdefault("metrics", ["booked_to_kept", "no_show_rate", "reschedule_rate"])

    research = profile.setdefault("research", {})
    research.setdefault("official_sources", [])
    return profile


def required_env_vars(profile: dict) -> list[dict[str, str]]:
    vars_needed = [
        {
            "name": "SHOWRATE_CRM_TOKEN",
            "prompt": "ShowRate CRM token",
            "help": "Map the selected CRM credential into this generic env var.",
            "required_for": "CRM reads and writes",
        },
        {
            "name": "SHOWRATE_SCHEDULER_TOKEN",
            "prompt": "ShowRate scheduler token",
            "help": "Map the scheduler credential into this generic env var.",
            "required_for": "Booking and reschedule access",
        },
    ]
    if profile["stack"].get("sms") not in {"none", "", None}:
        vars_needed.append(
            {
                "name": "SHOWRATE_SMS_TOKEN",
                "prompt": "ShowRate SMS token",
                "help": "Map the SMS provider credential into this generic env var.",
                "required_for": "SMS reminders and confirmations",
            }
        )
    if profile["stack"].get("email") not in {"none", "", None}:
        vars_needed.append(
            {
                "name": "SHOWRATE_EMAIL_TOKEN",
                "prompt": "ShowRate email token",
                "help": "Map the email provider credential into this generic env var.",
                "required_for": "Email reminders and fallback mail sends",
            }
        )
    return vars_needed


def render_stack_notes(profile: dict) -> str:
    stack = profile["stack"]
    rules = profile["rules"]
    research = profile["research"]
    sources = "\n".join(f"- {url}" for url in research.get("official_sources", [])) or "- Add verified sources here."
    return f"""# Stack Notes

## Stack Summary

- CRM: {stack['crm']}
- Scheduler: {stack['scheduler']}
- Calendar: {stack['calendar']}
- SMS: {stack['sms']}
- Email: {stack['email']}
- Telephony: {stack['telephony']}
- Primary timezone: {profile['client']['timezone']}

## Operating Rules

- Reminder cadence: {json.dumps(rules['reminder_cadence'])}
- Confirmation required: {rules['confirmation_required']}
- Reschedule window: {rules['reschedule_window']}
- Working hours: {rules['working_hours']}
- No-show grace minutes: {rules['no_show_grace_minutes']}
- Timezone policy: {rules['timezone_policy']}
- Escalation: {rules['escalation']}

## Official Sources To Check

{sources}
"""


def render_message_templates(profile: dict) -> str:
    client_name = profile["client"]["name"]
    return f"""# Message Templates

## Confirmation - Email

Subject: Confirming your upcoming call

Hi {{{{first_name}}}},

You are booked for {{{{meeting_time_local}}}} with {client_name}. Please reply YES to confirm or reply RESCHEDULE if you need a different slot.

## Reminder - SMS

Hi {{{{first_name}}}}, quick reminder about your call at {{{{meeting_time_local}}}}. Reply YES to confirm or RESCHEDULE if needed.

## Reschedule Reply

No problem. I can help move this. The current policy is: {profile['rules']['reschedule_window']}. Offer the next approved slots and keep timezone wording explicit.

## No-show Recovery

We missed you today. If you still want to speak, reply RESCHEDULE and I will send the next approved options.
"""


def risk_bucket(event: dict) -> str:
    lead_time = event.get("lead_time_hours", 24)
    prior_no_show = event.get("prior_no_show", False)
    source = str(event.get("source", "")).lower()
    if prior_no_show or lead_time <= 2:
        return "high"
    if lead_time <= 24 or "paid" in source:
        return "medium"
    return "low"


def reminder_actions(profile: dict, event: dict) -> list[str]:
    risk = risk_bucket(event)
    actions = []
    for item in profile["rules"]["reminder_cadence"]:
        channels = ", ".join(item.get("channels", []))
        actions.append(f"{item.get('timing')} via {channels} for {item.get('purpose')}")
    if risk == "high":
        actions.append("extra same-day confirmation check")
    return actions


def simulate_events(profile: dict, events: list[dict]) -> list[dict]:
    results = []
    for event in events:
        kind = event["type"]
        if kind == "booking":
            results.append(
                {
                    "type": kind,
                    "risk": risk_bucket(event),
                    "actions": reminder_actions(profile, event),
                }
            )
        elif kind == "confirmation":
            results.append({"type": kind, "result": "mark confirmed and suppress duplicate nudges"})
        elif kind == "reschedule_request":
            results.append(
                {
                    "type": kind,
                    "result": f"offer next approved slots; honor policy '{profile['rules']['reschedule_window']}'",
                }
            )
        elif kind == "no_show":
            results.append(
                {
                    "type": kind,
                    "result": f"mark no-show after {profile['rules']['no_show_grace_minutes']} minutes and trigger recovery",
                }
            )
        elif kind == "missing_api_key":
            results.append({"type": kind, "result": "degrade gracefully and escalate without sending"})
        elif kind == "crm_failure":
            results.append({"type": kind, "result": f"retry then escalate: {profile['rules']['escalation']}"})
        elif kind == "timezone_mismatch":
            results.append({"type": kind, "result": f"apply timezone policy: {profile['rules']['timezone_policy']}"})
        else:
            results.append({"type": kind, "result": "unsupported test event"})
    return results
