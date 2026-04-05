# I Run Five Claude Code Instances in Parallel — Here Is How I Ship 20 PRs a Day

#### Git worktrees turn Claude Code from a single-threaded assistant into a parallel engineering team

**By Tihomir Manushev**

*Mar 28, 2026 · 5 min read*

---

Last Tuesday I had five pull requests open before my first coffee cooled down. Three were feature work, one was a bug fix a teammate flagged overnight, and one was a test coverage sweep I had been putting off for weeks. None of them touched the same files. None of them conflicted. And I did not write a single line of code in any of them.

Five Claude Code instances ran simultaneously, each in its own isolated copy of the repository. While one agent was building a new API endpoint, another was fixing an off-by-one error in the billing module, and a third was writing integration tests for last week's merge. I reviewed diffs, approved PRs, and moved on.

The feature that makes this possible has been in Claude Code since February 2026, and most developers I talk to either do not know about it or assume it is more complicated than it is.

It is one flag: `--worktree`.

---

### The Problem With Running Two Agents in the Same Directory

Before worktrees, running parallel Claude Code instances meant trouble. Two agents editing files in the same working directory created a mess: one would write to `auth.py` while the other was reading it, changes would overwrite each other silently, and git staging became a minefield of unrelated hunks mixed together.

The bugs were subtle too. Shared shell state caused execution failures. The config file at `~/.claude.json` has no file locking, so concurrent writes from multiple instances could truncate it mid-write, producing invalid JSON that crashed every session. Some developers reported instances freezing entirely when two ran in the same VS Code integrated terminal.

The core issue is simple: git tracks one working tree per checkout. Two agents making unrelated changes in one working tree is like two people typing into the same document without seeing each other's cursor.

---

### What --worktree Actually Does

The `--worktree` flag tells Claude Code to create an isolated copy of your repository before it starts working. Under the hood, it uses git's native worktree mechanism — the same feature that has been in git since 2015, just wrapped into a single flag.

```bash
claude --worktree billing-fix
```

This does three things:

1. Creates a new directory at `.claude/worktrees/billing-fix/` with a full checkout of your files.
2. Creates a new git branch called `worktree-billing-fix` based on your remote's default branch.
3. Starts Claude Code inside that directory, fully isolated from your main checkout.

You can also let Claude Code generate a name for you:

```bash
claude -w
```

This picks a random name like `bright-running-fox`, creates the worktree, and drops you in. Useful when you do not care about the branch name because you will rename it before the PR anyway.

When the session ends, Claude Code checks whether any changes were made. If the agent finished without modifying anything — maybe it was a research task — the worktree and branch get cleaned up automatically. If commits exist, Claude asks whether to keep or remove the worktree. Keep it, and the directory and branch persist for you to review, push, or continue later.

---

### The Five-Terminal Workflow

Here is the pattern I use daily. I open five terminal tabs — or five tmux panes if I am feeling disciplined — and launch a worktree in each:

```bash
# Tab 1: New feature
claude -w api-pagination

# Tab 2: Bug fix from overnight triage
claude -w fix-billing-rounding

# Tab 3: Test coverage for last week's merge
claude -w tests-user-service

# Tab 4: Dependency update
claude -w upgrade-fastapi

# Tab 5: Documentation sweep
claude -w docs-api-reference
```

Each instance gets its own branch, its own files, its own git history. I give each one a clear prompt describing the task, switch to auto-accept mode for the straightforward ones, and cycle between tabs reviewing progress.

The key insight is that I am no longer a writer — I am a reviewer. My job shifted from producing code to evaluating code. I read diffs, check edge cases, approve or redirect, and move to the next tab. The throughput increase is not incremental. It is multiplicative.

Boris Cherny, the creator of Claude Code, runs a version of this workflow himself — five local instances plus additional sessions on claude.ai/code, shipping 50 to 100 PRs per week. He starts each session in Plan Mode to align on approach, then switches to auto-accept for execution.

---

### Environment Setup: The Part Most People Skip

The first time you spin up a worktree, you will hit a wall: your `.env` file is not there. Neither are your installed dependencies. The worktree is a fresh checkout of tracked files only — anything in `.gitignore` does not come along for the ride.

Claude Code solves this with `.worktreeinclude`. Create this file in your project root:

```
.env
.env.local
config/secrets.json
```

Any file listed here that is also gitignored gets copied into every new worktree automatically. Your secrets travel with each instance without being committed to git.

For heavier setup — installing dependencies, running migrations, starting local services — use a `WorktreeCreate` hook. This replaces the default worktree creation logic entirely:

```json
{
  "hooks": {
    "WorktreeCreate": [{
      "type": "command",
      "command": ".claude/hooks/create-worktree.sh"
    }]
  }
}
```

Your script receives the worktree name as JSON on stdin and must print the absolute path to the created directory on stdout. Inside, you can run `npm install`, copy additional config files, seed a test database — whatever your project needs to be functional from a cold start.

One more thing: add `.claude/worktrees/` to your `.gitignore`. Without this, every worktree's contents show up as untracked files in your main checkout, cluttering `git status` into uselessness.

---

### When Not to Parallelize

Five agents are not always better than one. Knowing when to stay single-threaded saves you from coordination headaches that eat the time you thought you were saving.

**Do not parallelize sequential work.** If task B depends on the output of task A, running them simultaneously means B works against a stale version of the code. You will spend more time resolving conflicts than you saved.

**Do not parallelize same-file edits.** Two agents rewriting `routes.py` in parallel will produce two divergent branches that cannot merge cleanly. Split the work by module or file boundary instead.

**Watch your rate limits.** On the Pro plan, two Opus sessions in parallel will hit rate limits within minutes. The Max 5x plan comfortably supports two to three concurrent sessions. Max 20x handles four to five. Beyond that, even the most generous plan starts throttling. The practical ceiling for most developers is five to seven concurrent agents on a laptop before rate limits and system resources become the bottleneck.

**Small tasks are not worth the overhead.** If Claude Code can finish a change in under ten minutes in a single session, the setup cost of creating a worktree, copying environment files, and installing dependencies wipes out the parallelism benefit. Save worktrees for tasks that take thirty minutes or longer.

---

### Scripting It for Maximum Throughput

Once you are comfortable with the manual workflow, you can script it. The `-p` flag runs Claude Code non-interactively — perfect for batch-spawning parallel agents:

```bash
#!/bin/bash
declare -A TASKS=(
  ["fix-auth-bug"]="Fix the JWT expiration bug in auth/tokens.py"
  ["add-rate-limiting"]="Add rate limiting to the /api/v2/users endpoint"
  ["update-tests"]="Add missing unit tests for the billing module"
)

for name in "${!TASKS[@]}"; do
  claude -w "$name" -p "${TASKS[$name]}" \
    --allowedTools "Bash,Read,Edit" &
done

wait
echo "All agents finished."
```

Each agent gets its own worktree, its own task, and runs in the background. The `wait` command blocks until every instance completes. When they finish, you have three branches ready for review.

Add `--output-format json` to capture structured results, including session IDs you can use to resume conversations with `--resume` if an agent needs follow-up.

---

### Conclusion

The `--worktree` flag transforms Claude Code from a tool you watch into a team you manage. Five isolated instances, five independent branches, five PRs that do not know about each other — all converging into your main branch through normal review.

The workflow shift is the real win. You stop being the person who writes code and start being the person who defines tasks, reviews output, and decides what ships. The agents do the typing. You do the thinking.

Start with two worktrees tomorrow. Give each one a clear, scoped task. Review the output. Then try three. By the end of the week, you will wonder how you ever worked with just one.
