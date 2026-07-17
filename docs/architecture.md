# Show-Rate Guardian — architecture

## Decision policy (example bands)

| Risk | Action |
|------|--------|
| Low | Light reminder closer to meeting |
| Medium | Earlier reminder + confirm CTA |
| High | Multi-touch + easy reschedule |
| Unknown | Human review queue |

## Adapter model

Core policy is stack-agnostic. **Adapters** map:

- booking webhooks  
- CRM fields for lead context  
- SMS / email / dialer providers  
- status write-back  

See `skills/showrate-guardian-*-*/` for profile-specific skill packs.

## Non-goals

- Not a full CRM replacement  
- Not a multi-tenant SaaS marketing site  
- Not a generic chatbot  
