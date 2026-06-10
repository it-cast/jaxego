---
name: gsd:autopilot
description: Drive an entire milestone end-to-end — iterates all incomplete phases running discuss → ui → research → plan → plan-checker → execute → verify → auto-retro. Respects v0.4.0 gates. Successor to /gsd-autonomous.
argument-hint: "<milestone-id> [--from N] [--dry-run] [--text]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - TodoWrite
  - AskUserQuestion
---
<objective>

Run all incomplete phases of a milestone end-to-end, respecting v0.4.0 enforcement gates.

**Difference from `/gsd-autonomous`:**
- `/gsd-autonomous` predates v0.4.0 — does not enforce sprint_ui_matrix, Visual Contract gate, or Security Baseline gate
- `/gsd-autopilot` is v0.4.0-aware — enforces all gates, pauses only on real blocks

**Cycle per phase** (mirrors framework canonical flow):
1. `discuss-phase` (gather context)
2. `ui-phase` (only if phase has_ui=true — gate 2 blocks without tokens.json)
3. `research-phase` (includes Security Baseline for sensitive phases — gate 4)
4. `plan-phase` (produces PLAN.md)
5. `plan-checker` agent (gate 3 — validates skills coverage)
6. `execute-phase` (implementation with internal gates 5, 6, 7)
7. Verification routing (pass / human_needed / gaps)
8. Auto-retrospective generation

**Pauses expected per 4-phase milestone:** 2 mandatory (confirmation, milestone end) + contingent on blocks. Typical: 2-5 pauses total vs. ~30 with manual cycle.

**Retrospectives are auto-generated** with objective data and `[AUTO: fill later]` placeholders for qualitative fields. Review and fill later in `.planning/retros/`.

</objective>

<execution_context>
@./.claude/get-shit-done/workflows/autopilot.md
</execution_context>

<runtime_note>
**VS Code Copilot:** Use `vscode_askquestions` in place of `AskUserQuestion`.
**Non-Claude CLIs:** Pass `--text` to get numbered text prompts instead of interactive questions.
</runtime_note>

<context>
Arguments: $ARGUMENTS

**Required:**
- `<milestone-id>` — positional first argument (e.g., `v1.0`, `M1`, `1.0` — must match a milestone in ROADMAP.md)

**Optional flags** (only active if literal token appears in arguments):
- `--from N` — skip to phase N within the milestone (resume after manual work)
- `--dry-run` — show plan without modifying files
- `--text` — plain-text prompts for non-Claude runtimes

**Required state:**
- `.planning/ROADMAP.md` with the milestone
- `.planning/STATE.md`
- `.planning/config.json`

**Skill() invocations used** (all resolve to existing commands/agents in `.claude/`):
- `gsd-discuss-phase` → `.claude/commands/gsd/discuss-phase.md`
- `gsd-ui-phase` → `.claude/commands/gsd/ui-phase.md`
- `gsd-research-phase` → `.claude/commands/gsd/research-phase.md`
- `gsd-plan-phase` → `.claude/commands/gsd/plan-phase.md`
- `gsd-plan-checker` → `.claude/agents/gsd-plan-checker.md`
- `gsd-execute-phase` → `.claude/commands/gsd/execute-phase.md`
- `gsd-milestone-summary` → `.claude/commands/gsd/milestone-summary.md`

</context>

<process>

Execute the autopilot workflow end-to-end from `@./.claude/get-shit-done/workflows/autopilot.md`.

**Never bypass gates silently.** Gates 2, 3, 4 pause with user options. Bypass logged to `.planning/METRICS.md` when user opts in.

**Verification gap retries are limited to 2** to prevent infinite loops. After 2 failed retries, handle_blocker.

</process>

<recovery>

If autopilot is interrupted:
- State persists per-phase in `.planning/phases/NN-<slug>/`
- Resume with: `/gsd-autopilot <milestone-id> --from <next-incomplete-phase-number>`
- Phases marked complete are skipped automatically on resume

</recovery>
