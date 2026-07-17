# Show-Rate Guardian

**Agentic no-show reduction for B2B sales** — interview the operator’s stack, score risk, orchestrate multi-channel reminders and recovery. First product wedge of Signal OS / Agentic OS.

| | |
|---|---|
| **Author** | [Deekshak SS](https://deekshak.site) |
| **Portfolio** | [deekshak.site](https://deekshak.site) |
| **Runtime history** | Hermes agent skills (runtime retired on my desk; skills preserved) |

---

## Problem

Booked meetings no-show. Generic reminders ignore **risk**, **lag-to-meeting**, and **channel**. Each miss burns pipeline revenue sales already tracks as **show rate**.

## What it is

A **shadow agent system** — not a consumer app:

```
Booking event (CRM / Calendly / calendar)
        ↓
Context (lead, source, hours until meeting)
        ↓
Risk score + reasons (LLM, structured)
        ↓
Policy → channel + delay (SMS / email / multi-touch)
        ↓
Reminder | confirm CTA | reschedule path
        ↓
Log outcome (CRM / sheet) + recovery if no-show
```

The “UI” is the **prospect’s SMS/email** and the **ops log** — not a SaaS homepage.

## What’s in this repo

| Path | Purpose |
|------|---------|
| `skills/showrate-guardian-factory/` | Factory skill: interviews operator, generates a client-specific runtime skill |
| `skills/showrate-guardian-dk/` | Demo client skill (custom CRM + Calendly + GHL SMS style stack) |
| `skills/showrate-guardian-hubspot-calendly-twilio/` | Adapter profile: HubSpot + Calendly + Twilio |
| `skills/showrate-guardian-ghl-calendly-twilio/` | Adapter profile: GoHighLevel stack |
| `skills/showrate-guardian-mixed-adapter/` | Mixed CRM/scheduler adapter |
| `docs/consultant-prompt.md` | Full AI consultant interview + recommendation prompt |
| `docs/architecture.md` | Decision policy sketch |

## Factory pattern

1. **Discover** — CRM, scheduler, SMS/email, timezone, reminder policy  
2. **Analyze** — stack gaps, quick wins, full automation opportunity  
3. **Generate** — client-specific skill / adapter config  
4. **Run** — event-driven agent on Hermes (or any tool-using runtime)

This is how one “product” adapts to many operator stacks without rewriting core policy.

## Why no live product screenshot

- No single public web UI for the core loop  
- Hermes host for this project is retired / not the hire surface  
- Real executions contain private calendar and lead data  

Architecture + skills + consultant prompt **are** the proof.

## Related

- [signal-os](https://github.com/Deekshak11/signal-os) — Mission Control / agentic infrastructure  
- [agency-os](https://github.com/Deekshak11/agency-os) — outbound production factory  

## License

MIT for original skills and docs in this public snapshot.
