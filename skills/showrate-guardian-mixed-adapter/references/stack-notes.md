# Stack Notes

## Stack Summary

- CRM: custom-crm-adapter
- Scheduler: mixed-scheduler-adapter
- Calendar: microsoft-365
- SMS: twilio
- Email: outlook
- Telephony: custom-dialer
- Primary timezone: Europe/London

## Operating Rules

- Reminder cadence: [{"timing": "48h", "channels": ["email"], "purpose": "confirm"}, {"timing": "3h", "channels": ["sms"], "purpose": "remind"}]
- Confirmation required: True
- Reschedule window: allow until close of business on the previous day
- Working hours: 09:00-17:30 operator timezone
- No-show grace minutes: 15
- Timezone policy: store both scheduler timezone and operator timezone, prefer scheduler for customer-facing copy
- Escalation: escalate to human router if adapters disagree on current event state

## Official Sources To Check

- https://learn.microsoft.com/graph/api/resources/event
- https://www.twilio.com/docs/messaging
- https://learn.microsoft.com/graph/api/resources/mail-api-overview
