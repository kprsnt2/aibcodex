# How we reduced support response time by 47% with an AI triage assistant

## Context
We handle ~1,800 support messages per week. Manual triage was the bottleneck and delayed first response.

## Data points
- Baseline median first response: 8.5 hours
- After rollout: 4.5 hours
- After second prompt iteration: 3.6 hours
- Human escalation rate remained stable at 22%

## What we built
- Classifier (billing, product bug, account access, feedback)
- Urgency scoring using simple heuristic + LLM sentiment/context
- Suggested draft response for agent review

## Evidence
![Weekly response trend](./images/support-response-trend.png)
![Queue volume by type](./images/queue-volume-by-type.png)
- Demo video: https://www.loom.com/share/example-demo

## Caveats
- Model occasionally over-prioritized emotional language.
- We improved this by adding policy examples and confidence thresholds.

## Desired blog outcome
- Teach founders how to start with small automation.
- Share practical architecture and prompt evolution.
- Include a section on what failed first.
