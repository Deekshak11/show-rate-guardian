---
name: showrate-guardian-factory
description: Interview the operator, normalize their CRM, scheduler, messaging, and timezone rules into a structured profile, research current best practices for the detected stack, then generate or refresh a personalized ShowRate Guardian runtime skill under skills/showrate/. Use when Hermes needs to replace an ad hoc agent prompt with a reusable stack-specific no-show reduction skill.
version: 1.0.0
author: Signal OS
license: MIT
metadata:
  hermes:
    tags: [showrate, factory, scheduling, crm, skills]
    category: operations
    requires_toolsets: [terminal]
    config:
      - key: showrate.repo_root
        description: Absolute path to the Agentic-OS repo on the runtime host
        default: /workspace/Agentic-OS
        prompt: Agentic-OS repo root
      - key: showrate.profile_dir
        description: Directory for draft runtime profiles
        default: /workspace/Agentic-OS/state/runtime-profiles
        prompt: ShowRate Guardian profile directory
---
# ShowRate Guardian Factory

Use this skill to create or refresh a personalized ShowRate Guardian runtime skill.

## Procedure

1. Read:
   - [references/discovery-questionnaire.md](references/discovery-questionnaire.md)
   - [references/stack-best-practices.md](references/stack-best-practices.md)
   - [references/runtime-skill-contract.md](references/runtime-skill-contract.md)
2. Collect the minimum discovery data needed to fill `state/runtime-profiles/<slug>.yaml`.
3. For the detected stack, research official vendor docs and current best practices before finalizing assumptions.
4. Save the normalized profile YAML.
5. Validate it:

```bash
python skills/showrate/showrate-guardian-factory/scripts/validate_profile.py \
  --profile state/runtime-profiles/<slug>.yaml
```

6. Generate the runtime skill:

```bash
python skills/showrate/showrate-guardian-factory/scripts/generate_runtime_skill.py \
  --profile state/runtime-profiles/<slug>.yaml \
  --force
```

7. Simulate the critical flows:

```bash
python skills/showrate/showrate-guardian-factory/scripts/simulate_flows.py \
  --profile state/runtime-profiles/<slug>.yaml \
  --events tests/fixtures/events/core-flow.json
```

8. Review the generated runtime skill and patch only what the generator could not safely infer.

## Pitfalls

- Do not hard-code a stack if the operator has a mixed toolchain.
- Do not skip official vendor docs when webhook semantics, rate limits, or timezone behavior matter.
- Do not ship a runtime skill without a valid `references/profile.yaml`.
- Use `python3` explicitly — `python` may not be available on the runtime host.
- The simulation step requires `tests/fixtures/events/core-flow.json` in the repo root. If missing, skip simulation gracefully and note it as a pending item for repo setup.

## Verification

- Generated skill contains `SKILL.md`, `references/profile.yaml`, `references/stack-notes.md`, `templates/messages.md`, and local validation wrappers.
- The validation script passes.
- The simulation covers booking, confirmation, reschedule, no-show, missing credentials, CRM failure, and timezone mismatch.

