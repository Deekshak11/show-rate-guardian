# Stack Best Practices

Use repo research plus official vendor docs. Prefer primary sources over blogs for implementation details.

## General Rules

- Confirm webhook retry behavior and idempotency rules before relying on writes.
- Confirm timezone behavior at the scheduler and calendar layer separately.
- Prefer read-only verification before enabling production writes.
- Keep provider credentials abstracted behind repo or container env vars.

## Official Source Map

- GoHighLevel: official API docs and webhook docs
- HubSpot: developer docs for CRM objects, workflows, and app auth
- Calendly: scheduling and webhook docs
- Twilio: messaging status callbacks, messaging service setup, rate limits, and error codes
- Google Calendar: API docs for event updates and timezone fields
- Gmail or Microsoft 365: official mail API docs if email writes are part of the loop

## Research Checklist

- Verify auth model: API key, OAuth, private app token, or webhook signature
- Verify rate limits and retry expectations
- Verify event ordering and stale-event handling
- Verify how cancellations and reschedules appear in each system
- Verify where the source of truth lives for `booked`, `confirmed`, `rescheduled`, `kept`, and `no-show`

