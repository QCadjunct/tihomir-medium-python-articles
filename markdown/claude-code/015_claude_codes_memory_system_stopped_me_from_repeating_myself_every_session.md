# Claude Code's Memory System Stopped Me From Repeating Myself Every Session

#### The persistent layer between CLAUDE.md and conversation history that makes sessions compound

**By Tihomir Manushev**

*Apr 11, 2026 · 5 min read*

---

Every new Claude Code session used to start the same way. "Use pytest fixtures, not setup methods." "Don't refactor adjacent code while fixing a bug." "We got burned by mocked database tests last quarter — hit the real database." Five to ten minutes of restating preferences before the actual work began.

CLAUDE.md handles the static stuff — your tech stack, directory layout, architectural constraints. Those conventions live in the repo and never change between sessions. But the things you *learn mid-session* — the corrections you give, the approaches you confirm, the project decisions you make in week three — used to vanish the moment the conversation ended. The next session started from zero, and you repeated yourself again.

The memory system stopped that cycle. Corrections stick. Preferences persist. Sessions build on each other instead of starting over.

---

### The File That Remembers

Claude Code's memory is not a database or a hidden API call. It is a directory of markdown files, scoped per project, stored at `.claude/projects/<project-name>/memory/`. Every file in that directory is a standalone memory with YAML frontmatter describing what it is and why it matters.

The system has two layers. **MEMORY.md** is the index — a lightweight file that loads into every conversation automatically. Each line is a one-sentence pointer to a memory file. Think of it as a table of contents that Claude Code scans to decide which memories are relevant to the current task.

The actual memories live in individual files alongside the index. Here is a real one from a project I use daily:

```markdown
---
name: Integration tests must use real database
description: No mocks for DB in integration tests — hit the real database
type: feedback
---

Integration tests must hit a real database, not mocks.

**Why:** Mocked tests passed but the prod migration failed last quarter.
The mock/prod divergence masked a broken schema change.

**How to apply:** When writing or reviewing integration tests, always
configure a real test database. Reserve mocks for unit tests only.
```

I said "don't mock the database" once, after a painful incident. Every integration test Claude Code has written since then uses a real test database without a single reminder. The correction compounded instead of evaporating.

---

### The Four Types That Matter

Not all memories are the same. The system distinguishes four types, and using the right one determines whether a memory helps or clutters.

**User memories** describe who you are — your role, expertise, and how you want to collaborate. A senior backend engineer gets different explanations than a student writing their first API. Save these early. They shape every interaction that follows.

**Feedback memories** capture corrections and confirmations. These are the most valuable type because they record *how you want Claude Code to behave* — both what to stop doing and what to keep doing. "Don't mock the database in integration tests" is a correction. "Yes, the single bundled PR was the right call" is a confirmation. Both matter.

**Project memories** hold decisions and context that code and git history cannot express. "The auth rewrite is driven by legal compliance, not tech debt" changes how Claude Code scopes its suggestions. "Merge freeze starts April 15 for the mobile release cut" prevents it from proposing non-critical PRs after that date.

**Reference memories** point to external systems. "Pipeline bugs are tracked in the Linear project INGEST." "The oncall latency dashboard is at grafana.internal/d/api-latency." These save Claude Code from guessing where information lives.

The discipline is knowing what memory is *not* for. Code conventions belong in CLAUDE.md. In-progress task state belongs in plans and tasks. Anything derivable from `git log` or the current file tree does not need a memory — it already exists in a more authoritative form.

```markdown
---
name: Pipeline bugs tracked in Linear
description: All pipeline bugs are in Linear project "INGEST"
type: reference
---

Pipeline bugs are tracked in the Linear project "INGEST".
Check there for context on any pipeline-related tickets.
```

---

### Write Once, Read Forever

Memory writes happen when Claude Code detects something worth preserving — a correction you give, a preference you state, a project decision you explain. It does not save every conversation turn. It saves the ones that change how future sessions should behave.

Memory reads happen when a topic overlaps with a stored memory. If you ask about testing and a feedback memory says "no mocks for database tests," that memory activates. If you are working on frontend code and the only memories are about backend conventions, they stay dormant. The system is selective, not exhaustive.

The critical caveat is that memories are **frozen snapshots**. A memory that says "the auth middleware lives in `src/middleware/auth.py` at line 42" was true when it was written. After a refactor, that file might not exist. Claude Code is trained to verify before acting on memories that name specific paths or functions — but the safest memories avoid code-level specifics entirely. "Integration tests must hit a real database" ages well. "The database connection is configured in `db/config.py` line 17" does not.

The best memories describe *intent and preference*, not *location and implementation*. Intent survives refactors. Implementation details do not.

---

### The Ritual It Kills

The practical impact is the death of the preamble ritual. Before memory, every session began with a context dump — reminding Claude Code of preferences it had no way to retain. After memory, those preferences are already loaded. The session starts at the task, not at the setup.

The compounding effect is real. A single correction — "don't mock the database in integration tests" — saved after one bad deployment has shaped every test Claude Code has written since. I did not restate it. I did not check whether it was still active. It was just there, applied quietly, session after session.

The signal for when to save a memory is simple: the moment you catch yourself saying something you have said before, that is a memory. If you correct the same behavior twice, it should not need a third time.

---

### Conclusion

CLAUDE.md teaches Claude Code what your project *is*. Memory teaches it what you *learned together*. The first is static — committed to the repo, shared with the team. The second is dynamic — built from corrections, confirmations, and decisions that accumulate over weeks of collaboration.

The setup cost is near zero. The next time you correct Claude Code and think "I already told you this" — say "remember this." That single sentence turns a forgotten correction into a permanent preference. Sessions stop resetting. They start compounding.
