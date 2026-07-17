# Runtime Skill Contract

Every generated ShowRate Guardian runtime skill must contain:

- `SKILL.md`
- `references/profile.yaml`
- `references/stack-notes.md`
- `templates/messages.md`
- `scripts/validate_profile.py`
- `scripts/simulate_flows.py`

## Runtime Expectations

- Read local profile first.
- Use generic repo-owned environment variable names rather than vendor-secret names when possible.
- Treat official docs as the final authority for stack-specific details.
- Stay cron-safe: runtime instructions must work in a fresh agent session.

