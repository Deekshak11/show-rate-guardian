from __future__ import annotations

import argparse
from pathlib import Path

from showrate_lib import load_profile


REQUIRED_TOP_LEVEL = ["client", "goal", "stack", "channels", "rules", "reporting"]
REQUIRED_STACK = ["crm", "scheduler", "calendar", "sms", "email", "telephony"]


def validate(profile: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_TOP_LEVEL:
        if key not in profile:
            errors.append(f"Missing top-level section: {key}")

    for key in REQUIRED_STACK:
        if not profile.get("stack", {}).get(key):
            errors.append(f"Missing stack field: stack.{key}")

    cadence = profile.get("rules", {}).get("reminder_cadence", [])
    if not cadence:
        errors.append("rules.reminder_cadence must contain at least one step")

    metrics = profile.get("reporting", {}).get("metrics", [])
    if not metrics:
        errors.append("reporting.metrics must contain at least one metric")

    return errors


def main(default_profile: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a ShowRate Guardian profile.")
    parser.add_argument("--profile", default=str(default_profile) if default_profile else None, help="Path to profile yaml")
    args = parser.parse_args()
    if not args.profile:
        raise SystemExit("--profile is required")

    profile = load_profile(Path(args.profile))
    errors = validate(profile)
    if errors:
        print("Profile validation failed:")
        for item in errors:
            print(f"  - {item}")
        return 1

    print(f"Profile validation passed for {profile['client']['slug']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

