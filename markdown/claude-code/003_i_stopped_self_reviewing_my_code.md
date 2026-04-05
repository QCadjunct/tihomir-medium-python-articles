# I Stopped Self-Reviewing My Code — Claude Code's /simplify Does It Better

#### Three parallel agents tear apart your changes for reuse, quality, and efficiency — before your teammates even see them

**By Tihomir Manushev**

*Mar 14, 2026 · 5 min read*

---

You know the PR comment. "There is already a utility for this in `src/utils/formatting.py`." You wrote a helper function, tested it, felt good about it — and then a teammate points out that the exact same logic has existed in the codebase for six months. The code works. The embarrassment is free.

This happens because self-review is the step everyone skips. You just spent two hours building the feature. Your eyes are glazed. You skim the diff, convince yourself it looks fine, and push. The structural issues — duplicated logic, unnecessary complexity, a database query inside a loop — survive because you are too close to the code to see them.

Claude Code has a single command that replaces that step entirely. `/simplify` reads your recent changes, spawns three specialized review agents in parallel, and applies fixes directly to your working copy. One command, no setup, and it catches the things you stopped looking for twenty minutes ago.

---

### Not a Linter, Not a Formatter

The first thing to understand about `/simplify` is what it is not. It does not replace Ruff, ESLint, Prettier, or any other linting and formatting tool. Those tools enforce syntax rules and style conventions — consistent indentation, import ordering, unused variable warnings. `/simplify` operates at a higher level. It catches the kind of issues a senior engineer flags during code review: structural decisions, missed abstractions, algorithmic inefficiency.

It only reviews **changed files**, identified through `git diff`. It does not scan your entire codebase looking for problems. The scope is deliberately narrow — your recent work, nothing else. The usage is as simple as it gets:

```bash
/simplify
```

That single command reads your diff, launches the review agents, and starts fixing. There is no configuration step, no setup file, no flags. When it finishes, your working copy contains the fixes. Review what changed with `git diff` before you commit.

---

### Three Agents, Three Angles

The mechanism behind `/simplify` is what makes it effective. It does not run a single pass over your code. It spawns **three independent agents in parallel**, each analyzing the same diff through a different lens:

The **reuse agent** searches for existing utilities in your codebase that you could have used instead of writing new code. It catches duplicate functions, hand-rolled implementations of logic that already exists in a shared module, and inline patterns that ignore established abstractions. This is the agent that prevents the "we already have a utility for this" PR comment.

The **quality agent** looks at structure and readability. It flags redundant state, parameter sprawl, copy-paste variations between similar functions, leaky abstractions, and naming issues. It catches the kind of code that works but makes the next developer pause and re-read three times.

The **efficiency agent** hunts for performance problems. Database queries inside loops, expensive operations that could be batched, missed opportunities for concurrency, and TOCTOU anti-patterns where a check and its corresponding action are separated by code that could invalidate the check.

Here is the gotcha: `/simplify` applies fixes **automatically with no approval step**. It does not ask permission. It edits your files directly. This is a feature, not a bug — it keeps the workflow fast — but it means you must review the diff before committing. Always run `git diff` after `/simplify` finishes.

---

### Steering the Review

The optional text argument lets you focus the agents on specific concerns. Instead of a general review, you can direct attention exactly where you want it:

```bash
/simplify focus on error handling
/simplify check for duplicated logic
/simplify look at the database query patterns
```

This is especially useful on large diffs where a general review might surface twenty findings but you care most about one category. Narrowing the focus produces deeper analysis in that area.

`/simplify` also reads your CLAUDE.md file. If your project defines coding standards, the agents enforce them against your diff. A CLAUDE.md like this:

```markdown
# Code Standards
- All database access through repository classes, never raw queries in handlers
- Prefer batch operations over loops for database writes
- Use domain exceptions from src/domain/errors.py, not generic ValueError
```

When `/simplify` encounters a handler that runs a raw SQL query or raises a plain `ValueError`, it rewrites the code to follow the project's conventions — using the repository layer, importing the correct domain exception. The standards you wrote once in CLAUDE.md become the standards that every `/simplify` run enforces.

One integration worth knowing: `/simplify` also runs automatically inside `/batch` workflows. When `/batch` spawns background agents in isolated worktrees, each worker runs `/simplify` on its own changes before committing. Large-scale refactors get a quality pass built in.

---

### When to Run It

The ideal time to run `/simplify` is after you finish a feature and before you open a PR. This is the gap where self-review was supposed to happen — the gap most developers skip. Let the three agents fill it.

Other good moments: after a bug fix, because quick patches often introduce shortcuts that survive into production. After accepting AI-generated code — yes, Claude Code reviewing its own output sounds recursive, but the review agents catch issues the generation pass missed. After prototyping, when experimental code is about to become permanent and needs tightening.

What `/simplify` should not replace: your formatter, your linter, or a full codebase refactor. For formatting and linting, use dedicated tools. For codebase-wide changes, `/batch` is the right command — it spawns multiple implementation agents across isolated worktrees, each of which runs `/simplify` before committing. Different tools for different scopes.

Early adopters report that `/simplify` consistently catches three to five issues per feature branch that would have surfaced during human review. Some teams have seen fifteen to forty percent reductions in total lines of code after running it on feature branches. Those are not lines of functionality lost — they are lines of duplication, unnecessary abstraction, and accidental complexity removed.

---

### Conclusion

`/simplify` is the self-review you always intended to do but never had the patience for. Three agents, three angles, one command. It catches the duplicate utility you forgot about, the parameter list that grew too long, and the database query hiding inside a loop. The best time to run it is right after you think your code is finished — because it probably is not. Run `/simplify`, review the diff, then push. Your reviewers will wonder why your PRs suddenly need fewer comments.
