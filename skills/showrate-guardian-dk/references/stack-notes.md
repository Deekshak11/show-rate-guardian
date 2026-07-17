# Stack Notes

## Stack Summary

- CRM: custom
- Scheduler: calendly
- Calendar: google
- SMS: gohighlevel
- Email: gmail
- Telephony: none
- Primary timezone: Asia/Kolkata

## Operating Rules

- Reminder cadence: [{"timing": "24h", "channels": ["email", "sms"], "purpose": "confirm_and_prep", "message_style": "friendly_check_in"}, {"timing": "2h", "channels": ["sms"], "purpose": "remind"}, {"timing": "15m", "channels": ["sms"], "purpose": "final_nudge"}]
- Confirmation required: True
- Reschedule window: allow until 2h before meeting
- Working hours: 10:00-21:00 Asia/Kolkata
- No-show grace minutes: 7
- Timezone policy: client booking timezone, display in IST
- Escalation: manual fallback after second failed write

## Official Sources To Check

- https://developer.calendly.com/
- https://developers.gohighlevel.com/
- https://developers.google.com/gmail/api
