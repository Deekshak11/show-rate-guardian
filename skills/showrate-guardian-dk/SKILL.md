---
name: showrate-guardian-dk
description: Personalized ShowRate Guardian runtime skill for the DK stack. Use when Hermes needs to operate, audit, or schedule no-show prevention, reminders, reschedules, and status sync against this exact CRM, scheduler, and messaging profile.
version: 1.0.0
author: Signal OS
license: MIT
metadata:
  hermes:
    tags: [showrate, custom, calendly, gohighlevel]
    category: operations
    requires_toolsets: [terminal]
required_environment_variables:
  - name: SHOWRATE_CRM_TOKEN
    prompt: ShowRate CRM token
    help: "Map the selected CRM credential into this generic env var."
    required_for: "CRM reads and writes"
  - name: SHOWRATE_SCHEDULER_TOKEN
    prompt: ShowRate scheduler token
    help: "Map the scheduler credential into this generic env var."
    required_for: "Booking and reschedule access"
  - name: SHOWRATE_SMS_TOKEN
    prompt: ShowRate SMS token
    help: "Map the SMS provider credential into this generic env var."
    required_for: "SMS reminders and confirmations"
  - name: SHOWRATE_EMAIL_TOKEN
    prompt: ShowRate email token
    help: "Map the email provider credential into this generic env var."
    required_for: "Email reminders and fallback mail sends"
---
# ShowRate Guardian - DK

## Operating Profile

- Client slug: `dk`
- Primary timezone: `Asia/Kolkata`
- CRM: `custom`
- Scheduler: `calendly`
- Calendar: `google`
- SMS: `gohighlevel`
- Email: `gmail`
- Goal: `booked_to_kept` with target `80% relative (from 50% to 90%)`

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

## Verification

- Run `python scripts/validate_profile.py`
- Run `python scripts/simulate_flows.py --events ../../../tests/fixtures/events/core-flow.json`
- Confirm the stack summary in `references/stack-notes.md` still matches the live environment
