# Show-Rate Guardian

**Agentic revenue protection at the meeting layer** — score no-show risk, pick channel and timing, follow up without a human babysitting every booking.

[![Portfolio](https://img.shields.io/badge/Portfolio-deekshak.site-0ea5e9?style=for-the-badge)](https://deekshak.site)
[![Author](https://img.shields.io/badge/Author-Deekshak%20SS-1e293b?style=for-the-badge)](https://github.com/Deekshak11)

> **Honest status:** This was a **shadow agent** (no consumer homepage). Runtime was Hermes-based and is **retired**. What remains is the **architecture, skills, and loop** as hire-facing proof — no fake product UI.

---

## Problem

Booked sales calls no-show. Generic reminders ignore risk, lag, lead source, and channel. Every miss is **protected revenue** already paid for in acquisition.

## Agent loop

```text
Calendar / booking event
        │
        ▼
 Pull context (history, source, lag, completeness)
        │
        ▼
 LLM risk score  ──►  high / med / low
        │
        ▼
 Policy: channel + delay + intensity
   (SMS / email / call-class paths)
        │
        ▼
 Send reminder or offer reschedule
        │
        ▼
 Write outcome → log / sheet
        │
        ▼
 Human override if score ambiguous
```

**Metric mapped:** show rate / protected meeting revenue — not “chatbot engagement.”

---

## Architecture

```text
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Booking src  │ ──► │ Agent runtime   │ ──► │ Messaging APIs   │
│ calendar     │     │ risk → action   │     │ SMS / email / …  │
└──────────────┘     └────────┬────────┘     └──────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Run log / sheet │
                     │ ops audit trail │
                     └─────────────────┘
```

| Piece | Role |
|-------|------|
| Skills pack | Risk, channel policy, message drafting |
| Adapters | Calendar / messaging integrations |
| Logs | Decision + outcome for ops review |
| Human path | Override when ambiguous |

---

## Repo layout

```text
docs/           Architecture, consultant prompts
skills/         Skill modules (Python / YAML / MD)
scripts/        Helpers
README.md
```

## Why no live demo URL

There was never a single “open me” product screen. The UI was **calendar notifications and messages recipients already use**. After retiring Hermes, this repo is the portable proof.

Portfolio explanation: [deekshak.site](https://deekshak.site) → Show-Rate Guardian (explained card).

## Related

| Repo | Role |
|------|------|
| [signal-os](https://github.com/Deekshak11/signal-os) | Infra that hosted agent skills |
| [business-os](https://github.com/Deekshak11/business-os) | Live multi-agent product |
| [agency-os](https://github.com/Deekshak11/agency-os) | Outbound factory |

## License

MIT for original code in this repository.
