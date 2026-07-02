---
date: 2026-07-02
persona: platform-engineer
jtbd: "When I start the uFawkesPipe stack with make up, I want to know with certainty that every service is accessible, authenticated, and capable of executing the full golden path (build → scan → deploy), so I can trust that application teams onboarding won't hit silent failures or configuration drift."
riskiest_assumption: "We assume services are correctly configured and reachable — what if authentication, network routing, or service state silently breaks after a compose down/up cycle, giving green Docker status but non-functional services?"
acceptance_criterion: "Given the uFawkesPipe stack is started with make up, when the acceptance test suite runs, then all services respond to health checks, authentication succeeds on all services requiring it, and a simulated golden-path pipeline (stack health → auth → build trigger → scan verification → deploy webhook) completes within 5 minutes with no manual intervention."
dora_ai_capability: "Cap6: User-centric focus"
dora_core_capability: "Continuous Delivery"
metric: "lead_time_for_change"
measurement_source: "uFawkesObs (deployment events from notify-obs)"
baseline: "Unknown — no automated acceptance verification exists today"
prior_art: null
status: ready-for-spec
---

# Discovery Brief: Automated Acceptance Test Suite

## Job to Be Done

When I start the uFawkesPipe stack with `make up`, I want to know with certainty
that every service is accessible, authenticated, and capable of executing the full
golden path (build → scan → deploy), so I can trust that application teams
onboarding won't hit silent failures or configuration drift.

## Riskiest Assumption

We assume services are correctly configured and reachable — what if authentication,
network routing, or service state silently breaks after a compose down/up cycle,
giving green Docker status but non-functional services?

**Why this is risky:** Today, `make up` gives green Docker container status even
when Portainer requires HTTPS first-run setup, SonarQube is still warming up,
and Woodpecker's OAuth config may be incomplete. The only verification is manual
browser testing — no automated guard.

## Acceptance Criterion

Given the uFawkesPipe stack is started with `make up`, when the acceptance test
suite runs, then all services respond to health checks, authentication succeeds
on all services requiring it, and a simulated golden-path pipeline (stack health
→ auth → build trigger → scan verification → deploy webhook) completes within
5 minutes with no manual intervention.

## DORA Outcome Target

- Capability: Cap6 (User-centric focus) — platform reliability is a user need
- Metric: lead time for change (onboarding friction eliminated)
- Current baseline: Unknown — no automated acceptance verification exists
- Target: < 5 min from `make up` to green acceptance suite
- Measurement: uFawkesObs deployment events via notify-obs

## Prior Art

None found in uFawkesPipe. Limited smoke tests exist (`tests/smoke/`) for
Woodpecker and SonarQube health endpoints only — no authentication, no
Portainer, no pipeline simulation.

## Notes

- Stack is currently running (4/4 services). Portainer requires HTTPS on :9443
  and first-run admin password setup. SonarQube on :9001 accessible.
- Woodpecker has `WOODPECKER_OPEN=true` — open access, no OAuth requirement.
  This may change in production; tests should handle both modes.
- Existing `pytest.ini` already has `acceptance` marker and `tests/acceptance/`
  directory with a skeleton `test_full_pipeline.py`.
- Test pattern should follow existing smoke test conventions:
  pytest.mark.acceptance, compose_running fixture that skips if stack is down,
  direct HTTP calls via urllib.request.
- No Gherkin/BDD — pytest is the established convention in this repo.
