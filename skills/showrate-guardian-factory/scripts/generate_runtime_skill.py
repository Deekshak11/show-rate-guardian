from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from showrate_lib import dump_yaml, load_profile, render_message_templates, render_stack_notes, required_env_vars


REPO_ROOT = Path(__file__).resolve().parents[4]
FACTORY_DIR = Path(__file__).resolve().parents[1]


def format_required_env(profile: dict) -> str:
    lines = []
    for item in required_env_vars(profile):
        lines.extend(
            [
                f"  - name: {item['name']}",
                f"    prompt: {item['prompt']}",
                f"    help: \"{item['help']}\"",
                f"    required_for: \"{item['required_for']}\"",
            ]
        )
    return "\n".join(lines)


def runtime_skill_content(profile: dict) -> str:
    slug = profile["client"]["slug"]
    env_block = format_required_env(profile)
    tags = ", ".join(
        [
            "showrate",
            profile["stack"]["crm"],
            profile["stack"]["scheduler"],
            profile["stack"]["sms"],
        ]
    )
    return f"""---
name: showrate-guardian-{slug}
description: Personalized ShowRate Guardian runtime skill for the {profile['client']['name']} stack. Use when Hermes needs to operate, audit, or schedule no-show prevention, reminders, reschedules, and status sync against this exact CRM, scheduler, and messaging profile.
version: 1.0.0
author: Signal OS
license: MIT
metadata:
  hermes:
    tags: [{tags}]
    category: operations
    requires_toolsets: [terminal]
required_environment_variables:
{env_block}
---
# ShowRate Guardian - {profile['client']['name']}

## Operating Profile

- Client slug: `{slug}`
- Primary timezone: `{profile['client']['timezone']}`
- CRM: `{profile['stack']['crm']}`
- Scheduler: `{profile['stack']['scheduler']}`
- Calendar: `{profile['stack']['calendar']}`
- SMS: `{profile['stack']['sms']}`
- Email: `{profile['stack']['email']}`
- Goal: `{profile['goal']['primary_metric']}` with target `{profile['goal']['target_lift']}`

## Procedure

1. Read `references/profile.yaml`, then `references/stack-notes.md`, then `templates/messages.md`.
2. Verify the current runtime still matches the documented stack before taking write actions.
3. If live integrations are involved, confirm the provider-specific behavior against official docs before depending on webhook ordering, retries, or timezone semantics.
4. For a new booking:
   - normalize the event into the profile contract
   - score no-show risk using lead time, prior behavior, and source context
   - schedule reminders from the configured cadence
5. For confirmations:
   - mark confirmed
   - suppress unnecessary duplicate reminders
6. For reschedule requests:
   - enforce the reschedule window from the profile
   - keep timezone wording explicit
   - write the new status back to the source of truth only after validation
7. For no-shows:
   - wait for the documented grace period
   - mark no-show in the tracking system
   - trigger the recovery sequence
8. For failures:
   - degrade safely
   - log what was skipped
   - follow the escalation rule in the profile
9. For nightly optimization:
   - run in a fresh cron session
   - compare kept-call, no-show, and reschedule metrics
   - patch only the message templates or heuristics that have clear evidence

## Pitfalls

- Do not assume provider token names; use the generic `SHOWRATE_*` env vars and map real credentials into them outside the skill.
- Do not treat scheduler timezone and calendar timezone as identical without checking.
- Do not write to CRM or scheduler state if the runtime profile no longer matches the live environment.
- Use `python3` explicitly — `python` may not be available on the runtime host.
- The simulation step requires `tests/fixtures/events/core-flow.json` in the repo root. If missing, skip simulation gracefully.

## Verification

- Run `python3 scripts/validate_profile.py`
- Run `python3 scripts/simulate_flows.py --events ../../../tests/fixtures/events/core-flow.json` (skip if fixtures not yet created)
- Confirm the stack summary in `references/stack-notes.md` still matches the live environment
"""


def wrapper_script(module_name: str) -> str:
    return f"""from __future__ import annotations

import sys
from pathlib import Path

FACTORY_SCRIPTS = Path(__file__).resolve().parents[2] / "showrate-guardian-factory" / "scripts"
sys.path.insert(0, str(FACTORY_SCRIPTS))

from {module_name} import main  # type: ignore


if __name__ == "__main__":
    default_profile = Path(__file__).resolve().parents[1] / "references" / "profile.yaml"
    raise SystemExit(main(default_profile=default_profile))
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a personalized ShowRate Guardian runtime skill.")
    parser.add_argument("--profile", required=True, help="Path to normalized profile yaml")
    parser.add_argument("--output-root", default=str(REPO_ROOT / "skills" / "showrate"), help="Output root for generated runtime skills")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing generated skill directory")
    args = parser.parse_args()

    profile_path = Path(args.profile).resolve()
    profile = load_profile(profile_path)
    slug = profile["client"]["slug"]
    output_root = Path(args.output_root).resolve()
    skill_dir = output_root / f"showrate-guardian-{slug}"

    if skill_dir.exists():
        if not args.force:
            raise SystemExit(f"Runtime skill already exists: {skill_dir}")
        shutil.rmtree(skill_dir)

    for child in ["references", "templates", "scripts"]:
        (skill_dir / child).mkdir(parents=True, exist_ok=True)

    (skill_dir / "SKILL.md").write_text(runtime_skill_content(profile), encoding="utf-8")
    (skill_dir / "references" / "profile.yaml").write_text(dump_yaml(profile), encoding="utf-8")
    (skill_dir / "references" / "stack-notes.md").write_text(render_stack_notes(profile), encoding="utf-8")
    (skill_dir / "templates" / "messages.md").write_text(render_message_templates(profile), encoding="utf-8")
    (skill_dir / "scripts" / "validate_profile.py").write_text(wrapper_script("validate_profile"), encoding="utf-8")
    (skill_dir / "scripts" / "simulate_flows.py").write_text(wrapper_script("simulate_flows"), encoding="utf-8")

    print(f"Generated runtime skill: {skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
