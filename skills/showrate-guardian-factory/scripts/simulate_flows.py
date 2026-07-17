from __future__ import annotations

import argparse
import json
from pathlib import Path

from showrate_lib import load_profile, simulate_events


def main(default_profile: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulate ShowRate Guardian flow coverage.")
    parser.add_argument("--profile", default=str(default_profile) if default_profile else None, help="Path to profile yaml")
    parser.add_argument("--events", required=True, help="Path to JSON events fixture")
    args = parser.parse_args()
    if not args.profile:
        raise SystemExit("--profile is required")

    profile = load_profile(Path(args.profile))
    events = json.loads(Path(args.events).read_text(encoding="utf-8"))
    if not isinstance(events, list):
        raise SystemExit("Events file must be a JSON list")

    results = simulate_events(profile, events)
    print(json.dumps({"profile": profile["client"]["slug"], "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

