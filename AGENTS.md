# Agent Router

Before implementing, read:

- `AGENT_LOOP.md` for the night shift workflow
- `docs/architecture.md` for system structure
- `docs/testing.md` for test commands and expectations
- `docs/domain.md` for product/domain concepts
- `docs/style-guide.md` for code style
- `docs/common-pitfalls.md` for known traps
- `../.night-shift/HARNESS_PRINCIPLES.md` for the operating principles behind the workflow
- `../.night-shift/SANDCASTLE.md` for how Sandcastle runs this workflow
- `../.night-shift/SANDBOX_PROFILES.md` for repo container and service profiles
- `../.night-shift/SPEC_PREFLIGHT.md` for the spec readiness gate

Work items live in:

- `Specs/`
- `TODO.md`

Ignore any spec whose filename starts with `draft-`.

For every completed task:

1. Add or update tests.
2. Run relevant tests.
3. Run typecheck/lint when available.
4. Commit with a detailed message.
5. Update `CHANGELOG.md` when the task changes behavior.

Record unrelated observations in `TODO.md`; do not opportunistically fix unrelated issues.

## Repo-local skills

- For dbt, Kimball dimensional modeling, warehouse layer design, surrogate key
  patterns, mart design, and warehouse model testing in this repo, use
  `docs/skills/data-warehousing/SKILL.md`.
- This data-warehousing skill is repo-local by policy. Do not install or use it
  from global Codex skills, and do not apply it to `~/repositories/work/**` or
  Databricks workspaces.
- Load the skill only when the task is explicitly about warehouse/dbt/modeling
  work; do not load it for ordinary Python, Beads, or application tasks.

<!-- workspace-agent-baseline:start -->
## Workspace Agent Baseline

## Tractatus-Style Operating Logic

This repository follows the Tractatus-style operating logic in `~/repositories/.night-shift/HARNESS_PRINCIPLES.md`: classify the work, preserve dependencies, distinguish mission fit from functional quality, and surface what must not be inferred.

Clarification is a guardrail:

- If the next action depends on an unstated proposition, do not infer it silently.
- During interactive work, ask a concise clarification question.
- During unattended work, mark the task `needs-clarification` or `blocked` and leave the exact question in the preflight report or `TODO.md`.
- After review, encode the missing proposition into specs, docs, tests, or guardrails.

Before implementation, also read:

- `AGENT_LOOP.md` for the Night Shift workflow
- `docs/beads.md` for the Bead queue and dependency conventions
- `~/repositories/.data-guardrails/docs/agent-integration.md` for workspace Databricks guardrails when this repo contains data work

Use Beads as the operational queue when available:

1. Check `bd ready --json`.
2. Claim one ready issue with `bd update <id> --claim`.
3. Read the spec path or external ticket linked from the issue.
4. Keep behavior and acceptance criteria in specs or tickets; use Beads for status, claims, blockers, and dependencies.
5. Close the Bead issue only after implementation and checks pass.

For any new agent-executed Databricks operation, write a structured plan under
`.guardrails/plans/` and verify it before execution:

```sh
UV_CACHE_DIR=~/repositories/.data-guardrails/.uv-cache uv run --project ~/repositories/.data-guardrails python -m data_guardrails verify .guardrails/plans/<task-name>.json
```

Legacy Databricks code is report-only. Do not block unrelated work because an
existing notebook, script, SQL, or Terraform file contains historical writes.

Production mutations require explicit human approval.
<!-- workspace-agent-baseline:end -->


<!-- BEGIN BEADS INTEGRATION v:1 profile:full hash:f65d5d33 -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Dolt-powered version control with native sync
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update <id> --claim --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task atomically**: `bd update <id> --claim`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Quality
- Use `--acceptance` and `--design` fields when creating issues
- Use `--validate` to check description completeness

### Lifecycle
- `bd defer <id>` / `bd supersede <id>` for issue management
- `bd stale` / `bd orphans` / `bd lint` for hygiene
- `bd human <id>` to flag for human decisions
- `bd formula list` / `bd mol pour <name>` for structured workflows

### Auto-Sync

bd automatically syncs via Dolt:

- Each write auto-commits to Dolt history
- Use `bd dolt push`/`bd dolt pull` for remote sync
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

<!-- END BEADS INTEGRATION -->
