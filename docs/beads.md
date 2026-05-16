# Beads

Beads is adopted lightly in this repository as a queue and dependency graph for
agent work. It does not replace Markdown specs or external tickets.

## Role

- `Specs/` holds implementation contracts: behavior, acceptance criteria,
  constraints, and test plans.
- Beads holds task status, claims, dependencies, blockers, and follow-up links.
- Preflight checks consistency between ready specs and Bead issues when
  available.
- Night Shift uses `bd ready --json` to choose unblocked work before opening the
  linked spec.

## Local Setup

Initialize local-only Bead state with:

```sh
bd init --stealth --non-interactive --skip-agents
```

Stealth mode keeps Bead metadata useful for local coordination without making
`.beads/` visible to collaborators or committing the database.

## Issue Convention

Create one issue per ready spec and link the spec path in the description:

```sh
bd create "Fix reminder scheduling drift" --type task --priority 1 --description "Spec: Specs/fix-reminder-scheduling-drift.md" --json
```

Before implementation:

```sh
bd ready --json
bd update <id> --claim
bd show <id> --json
```

For hard dependencies, use:

```sh
bd dep add <child-id> <parent-id>
```

This means the child is blocked until the parent is complete.

For non-blocking follow-up context, use `discovered-from` or `related` links.

Close Bead issues only after implementation and checks are complete:

```sh
bd close <id> --reason "Implemented and tested"
```

## Fallback

If `bd` is unavailable or `.beads/` is absent, agents should continue from ready
specs in `Specs/`.
