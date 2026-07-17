# Stack Notes

## Stack Summary

- CRM: gohighlevel
- Scheduler: calendly
- Calendar: google
- SMS: twilio
- Email: gmail
- Telephony: none
- Primary timezone: Asia/Kolkata

## Operating Rules

- Reminder cadence: [{"timing": "24h", "channels": ["email"], "purpose": "confirm"}, {"timing": "2h", "channels": ["sms"], "purpose": "remind"}]
- Confirmation required: True
- Reschedule window: allow until 2h before meeting
- Working hours: 09:00-18:00 local closer time
- No-show grace minutes: 10
- Timezone policy: booking timezone, fallback to closer timezone
- Escalation: manual fallback after second failed write

## Official Sources To Check

- https://marketplace.gohighlevel.com/docs/
- https://developer.calendly.com/
- https://www.twilio.com/docs/messaging
