# Agent Progress Rules

## Purpose
These rules define how the AI agent tracks and reports its progress during development sessions on the ScrapeWerse project.

---

## Progress Tracking Principles

1. **Always update `.state/` files** at the start and end of every session.
2. **Mark tasks in `.state/TASK_QUEUE.md`** as `[/]` (in progress) when starting, `[x]` (done) when complete.
3. **Update `.state/CURRENT_PHASE.md`** when moving between development phases.
4. **Log decisions in `.state/DECISIONS.md`** — any non-trivial architectural or design choice must be recorded with rationale.
5. **Record known issues in `.state/KNOWN_ISSUES.md`** immediately when discovered — never silently work around a problem.

---

## Session Start Checklist

Before any coding work, the agent MUST:
- [ ] Read `.state/CURRENT_PHASE.md` to understand where we are
- [ ] Read `.state/DEVELOPMENT_STATUS.md` for the big picture
- [ ] Read `.state/TASK_QUEUE.md` to find the next task
- [ ] Read `.state/KNOWN_ISSUES.md` to avoid working around known bugs

## Session End Checklist

After every coding session, the agent MUST:
- [ ] Update `.state/DEVELOPMENT_STATUS.md` with what was accomplished
- [ ] Update `.state/TASK_QUEUE.md` — mark completed tasks, add new ones
- [ ] Update `.state/CURRENT_PHASE.md` if the phase changed
- [ ] Commit any decisions to `.state/DECISIONS.md`

---

## Phase Transitions

When completing a phase:
1. Update `docs/phases/PHASE_NN.md` with a completion summary
2. Update `.state/CURRENT_PHASE.md` to the new phase
3. Update `.state/DEVELOPMENT_STATUS.md` phase table
