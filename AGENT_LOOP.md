# Night Shift Agent Loop

## Operating Logic

Use the Tractatus-style proposition logic from `~/repositories/.night-shift/HARNESS_PRINCIPLES.md`.

- Treat ready specs as the mission boundary.
- Treat repository docs, tests, templates, and guardrails as functional leverage.
- Report output against both mission fit and functional quality.
- Surface missing environment context instead of guessing strategy or product intent.
- Convert repeated corrections into docs, checks, specs, skills, or guardrails.

## Operating Rules

- Read `AGENTS.md` first.
- Do not work on specs whose filename starts with `draft-`.
- Prefer bugs and production correctness issues over features when priority is otherwise equal.
- Work on one task at a time.
- Before implementation, write a short testing plan.
- Add or update tests before or alongside implementation.
- Run relevant tests.
- Run typecheck, lint, and other mechanical checks when available.
- Commit each completed task separately.
- Use detailed commit messages for human review.
- Update `CHANGELOG.md` after each completed behavior or configuration change.
- Record unrelated observations in `TODO.md`; do not opportunistically fix unrelated issues.
- If blocked, write a concise note in `TODO.md`, commit useful diagnostic work, and move to the next ready task.

## Task Selection

1. If Beads is initialized and `bd ready --json` succeeds, use it as the queue.
2. Claim one Beads issue before starting it with `bd update <id> --claim`.
3. Read the spec path linked from the Beads issue description or notes.
4. Keep behavior, acceptance criteria, and test expectations in the linked spec, not only in the Beads issue.
5. If Beads is unavailable or has no ready issues, inspect `Specs/`.
6. Ignore files starting with `draft-`.
7. Pick the highest-priority ready spec, or the first ready spec if no priority is stated.
8. Complete it fully before starting another.

## Beads Status Updates

When using a Beads issue:

- Use Beads dependencies for ordering and blockers.
- Use `bd dep add <child-id> <parent-id>` for hard dependencies; the child is blocked until the parent is complete.
- Use `discovered-from` or `related` links for non-blocking follow-up context.
- Close the issue only after the linked spec is implemented and checked.
- If review is still required, leave a note in the issue and in the final report.

## Completion Report

When there are no ready tasks left, produce a concise final report containing:

- completed specs or Beads issues
- commits created
- tests run
- unresolved blockers
- follow-up TODOs

Then output:

```text
<promise>NIGHT_SHIFT_COMPLETE</promise>
```
