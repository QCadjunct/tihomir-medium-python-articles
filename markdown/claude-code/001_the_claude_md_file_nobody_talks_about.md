# The CLAUDE.md File Nobody Talks About: How I Make Claude Code Actually Understand My Codebase

#### Your project has conventions, constraints, and context — here is how to teach them once and never repeat yourself

**By Tihomir Manushev**

*Mar 12, 2026 · 7 min read*

---

Every Claude Code session starts the same way. You type "use pytest, not unittest." You remind it that tests live next to source files, not in a separate directory. You explain — again — that your project uses the repository pattern and that raw SQL belongs nowhere near a route handler. Ten minutes of preamble before you get to the actual task.

The frustration is not that Claude Code forgets. It does not have memory between sessions — each conversation is a blank slate. The frustration is that you keep solving this problem conversationally when the solution is structural. Your project's conventions do not change between sessions. They should not need to be restated between sessions either.

CLAUDE.md is that structural solution. Most tutorials mention it in passing — "create a CLAUDE.md file in your project root" — and move on. Almost none explain the architecture of a well-structured one: which files go where, what belongs in each, and what to deliberately leave out. That last part matters more than most developers realize, because a poorly written CLAUDE.md is worse than no CLAUDE.md at all.

---

### "The File That Runs Before You Type" — What CLAUDE.md Actually Does

CLAUDE.md is not a README. It is not documentation for humans. It is a set of **project instructions** that Claude Code reads automatically at the start of every session, before you type a single character. When you launch Claude Code in a directory that contains a CLAUDE.md file, its contents become part of the system context — the foundational instructions that shape how Claude Code thinks about everything that follows.

Think of it like onboarding a new senior engineer. You would not repeat the team's naming conventions, testing strategy, and architectural decisions every morning. You would write them down once and point the new hire to the document. CLAUDE.md is that document, except the reader has perfect recall and follows every instruction literally.

You can verify that Claude Code loaded your file by inspecting the system prompt:

```bash
claude --print-system-prompt | grep -A 5 "CLAUDE.md"
```

This prints the section where your CLAUDE.md content appears in the full system context. If your instructions show up, they are active. If they do not, the file is not in the right location or has a naming issue.

Here is the detail that changes how you think about CLAUDE.md: its content counts against your context window. Every line of project instructions is a line that cannot be used for conversation, code analysis, or generation. This means what you *leave out* of CLAUDE.md matters just as much as what you put in. A 500-line CLAUDE.md is not thorough — it is wasteful.

---

### "Three Levels Deep" — The CLAUDE.md Hierarchy

Claude Code does not read a single CLAUDE.md file. It reads up to three, layered in a specific order:

```bash
~/.claude/CLAUDE.md              # Personal preferences (all projects)
./CLAUDE.md                       # Project conventions (this repo)
./src/workers/CLAUDE.md           # Directory-scoped rules (this module)
```

The **personal file** at `~/.claude/CLAUDE.md` applies to every project you open. This is the place for your individual preferences — your favorite test runner, your formatting opinions, how you want Claude Code to communicate. Keep it short. Five to ten lines is usually enough.

The **project file** at the repository root is the workhorse. It describes your tech stack, your directory structure, your architectural patterns, and your non-negotiable constraints. This file gets committed to version control, so every team member shares the same project context. A well-written project CLAUDE.md looks like this:

```markdown
# Project Instructions

FastAPI application with SQLAlchemy ORM and Alembic migrations.
Python 3.12+, all code uses type annotations.

## Layout
- src/api/routes/    — route handlers, grouped by domain
- src/domain/        — business logic and domain models
- src/infra/db/      — database models, repositories, migrations
- tests/             — mirrors src/ structure, pytest with fixtures

## Constraints
- Never use raw SQL — all queries go through repositories
- Async endpoints only — no sync route handlers
- Tests run with: pytest --asyncio-mode=auto
```

The **directory-scoped file** is the one most developers miss entirely. When Claude Code works on files inside a subdirectory that contains its own CLAUDE.md, those instructions get loaded alongside the project and personal files. Crucially, scoped files are **lazy** — they only load when Claude Code actually reads or edits a file in that directory. If you are working on the frontend, a CLAUDE.md in the `api/` directory does not consume any context.

This lazy loading is what makes directory-scoped files powerful for large projects. You can provide detailed, module-specific instructions without paying the context window cost unless Claude Code is actually working in that area.

---

### "What Goes In, What Stays Out" — Content Architecture

This is where most CLAUDE.md files go wrong. The failure modes are opposite extremes: either a single line — "This is a Python project" — that provides no useful context, or a 300-line document that pastes the entire style guide, database schema, and API specification verbatim. The first gives Claude Code nothing to work with. The second buries the important rules in noise, and Claude Code starts ignoring them.

The principle is simple: describe **what** and **why**, not **how**. Claude Code already knows how to write Python, how to format JSON, how to structure imports. What it does not know is your project's specific decisions — the patterns you chose, the constraints you enforce, and where to find the reference implementations.

Compare these two approaches:

```markdown
# Bad: Micromanaging
Always wrap database calls in try/except blocks.
Use structlog for all logging.
Return HTTP 500 on any unhandled exception.
Import models before services.
Use 4-space indentation in all Python files.
```

```markdown
# Good: Providing context
Database operations follow the repository pattern — see src/infra/db/user_repo.py
for the reference implementation. Repositories raise domain exceptions (defined in
src/domain/exceptions.py), and the error middleware in src/api/middleware/errors.py
translates them to HTTP responses. Do not handle database errors in route handlers.
```

The first version tells Claude Code what to type on each line. It wastes context on things Claude Code already knows — like 4-space indentation in Python — and provides no help for situations you did not anticipate. The second version tells Claude Code how your codebase *thinks*. When it encounters a new database operation you never wrote a rule for, it has enough context to follow the established pattern.

A useful rule of thumb: **if Claude Code would get it right without the instruction, leave it out.** You do not need to tell it to use f-strings in Python or to close HTML tags. You *do* need to tell it that your project uses a custom query builder instead of raw ORM calls, because it has no way to infer that.

One common trap: pasting your entire linting configuration into CLAUDE.md. Your `.eslintrc` or `pyproject.toml` already exists in the repository. Claude Code can read those files directly when it needs to. Instead of duplicating the config, write a single line: "Linting rules are in `pyproject.toml` under `[tool.ruff]` — check before suggesting code style changes." This gives Claude Code the same information at a fraction of the context cost.

---

### "Scoped Rules for Monorepos" — Directory-Level CLAUDE.md

A monorepo with a React frontend, a Python API, and Terraform infrastructure has three completely different sets of conventions. Component naming patterns are irrelevant when writing database migrations. Terraform module structure has nothing to do with React state management. Cramming all of this into a single root CLAUDE.md creates a document so long that the important rules for any given task get lost.

The solution is a thin root file with shared constraints, plus directory-scoped files for each module:

```bash
monorepo/
  CLAUDE.md                   # Git workflow, CI conventions, PR format
  apps/web/
    CLAUDE.md                 # React 19, Tailwind, component naming
  apps/api/
    CLAUDE.md                 # FastAPI, repository pattern, async only
  infra/
    CLAUDE.md                 # Terraform modules, naming, no unit tests
```

Each scoped file should be concise — under 20 lines. It only needs to describe what makes that module *different* from the rest of the project. Here is what a realistic `apps/api/CLAUDE.md` looks like:

```markdown
# API Module

FastAPI with async SQLAlchemy. All endpoints are async.

## Patterns
- Route handlers in routes/, one file per domain (users.py, orders.py)
- Business logic in services/, never in route handlers
- Database access through repositories in db/repos/
- Reference implementation: see routes/users.py + services/user_service.py

## Testing
- pytest with httpx.AsyncClient for endpoint tests
- Factory Boy for test data — factories live in tests/factories/
- Run: pytest apps/api/tests/ --asyncio-mode=auto
```

Scoped files can also **override** root-level behavior. If your root CLAUDE.md says "write tests for all changes," a scoped file in `infra/` can clarify: "Infrastructure changes do not have unit tests. Validate with `terraform plan` and `tflint` instead." This is not a contradiction — it is context-appropriate guidance. The root file sets the default, and the scoped file adapts it for a module where the default does not apply.

---

### "The Context Window Tax" — Why Less Is More

Every token in your CLAUDE.md is a token that cannot be used for the actual work. A 200-line CLAUDE.md with detailed instructions for every corner of your project might feel comprehensive, but it means 200 lines less capacity for code analysis, generation, and conversation. In a long session with multiple files open, this tax compounds.

The practical limits I have found effective: **keep your root CLAUDE.md under 50 lines and scoped files under 20 lines.** If you need to convey more detail, use file references. "See `docs/architecture.md` for the full system design" costs one line of context but gives Claude Code access to an entire document — and only when it actually needs it.

I once had a CLAUDE.md that included the complete database schema — every table, every column, every foreign key. Claude Code loaded those 40 lines in every session, whether I was working on the API, the frontend, or writing documentation. Forty lines of table definitions burning context for zero benefit most of the time. Moving the schema description to `db/CLAUDE.md` solved the problem instantly. It still loads when I work on database code, which is the only time it matters.

Treat CLAUDE.md like code: review it periodically, prune what is no longer relevant, and add rules only when you catch yourself repeating an instruction in conversation. If Claude Code keeps making a specific mistake, add a line. If you cannot remember the last time a rule was needed, remove it.

---

### Conclusion

CLAUDE.md is not a configuration file — it is a **communication artifact**. Writing a good one forces you to articulate your project's conventions clearly: which patterns are mandatory, which constraints are non-negotiable, and where the reference implementations live. That exercise has value even beyond Claude Code. Teams that write effective CLAUDE.md files are the ones that already have clear engineering standards — or that develop them through the process of writing one.

The best CLAUDE.md files are not the longest. They are the ones with the highest signal-to-noise ratio — every line earns its place in the context window. Start with five lines. Add a line every time you catch yourself repeating an instruction in conversation. Delete a line every time Claude Code gets something right without it. Your CLAUDE.md should converge, over time, to the minimum effective context for your project.
