# Stack Notes

## Stack Summary

- CRM: hubspot
- Scheduler: calendly
- Calendar: google
- SMS: twilio
- Email: gmail
- Telephony: aircall
- Primary timezone: America/Vancouver

## Operating Rules

- Reminder cadence: [{"timing": "24h", "channels": ["email"], "purpose": "confirm"}, {"timing": "4h", "channels": ["sms"], "purpose": "remind"}, {"timing": "30m", "channels": ["sms"], "purpose": "final-check"}]
- Confirmation required: True
- Reschedule window: allow until 1h before meeting
- Working hours: 08:00-17:00 local closer time
- No-show grace minutes: 12
- Timezone policy: scheduler timezone wins unless the CRM owner timezone is explicit
- Escalation: hand off to ops manager after failed CRM write or duplicate booking signal

## Official Sources To Check

- https://developers.hubspot.com/docs/api/overview
- https://developer.calendly.com/
- https://www.twilio.com/docs/messaging
