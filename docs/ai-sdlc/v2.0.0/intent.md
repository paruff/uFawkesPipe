# Intent: uFawkesPipe v2.0.0

**Traces to:** the suite release plan,
[Phase 4](https://github.com/paruff/uFawkes.dev/blob/main/docs/ai-sdlc/suite-release/plan.md#phase-4--pipe-20--dojo-04-gate-ac-pipe-01),
and the goal issue paruff/uFawkesPipe#120.

**Who:** a team that wants CI/CD and security scanning on one Docker host, and
the six other suite repos, which call this repo's reusable workflows.

**Job:** run the stack from its README and trust that every feature it names
works.

**Why now:** every release so far is `1.x.y-beta`. `v2.0.0` is the first
stable release, and the first one that passes AC-PIPE-01.

**Outcome:** a real pipeline run on a sample repo, linked from the release
notes, with `notify-obs` verified against a released uFawkesObs.

## Non-goals

Jenkins, Kubernetes deployment (the fawkes track) and new stack features.
