# Two Ways to Loop in Claude Code — And Why You Need Both

#### One polls blindly on a timer. The other iterates until the job is done. Knowing which to use changes everything.

**By Tihomir Manushev**

*Mar 17, 2026 · 5 min read*

---

You kicked off a deploy at five in the afternoon and went to make coffee. Twenty minutes later you check back — the deploy failed at minute three. You spent seventeen minutes waiting for nothing, staring at a terminal that could have told you immediately.

Now picture a different scenario. You have a test suite with eight failing tests after a refactor. You could sit there fixing them one by one, running the suite after each change. Or you could tell Claude Code to keep iterating — fix a test, run the suite, fix the next failure, repeat — and come back when everything is green.

Two different problems. Two different kinds of automation. Claude Code has a loop for each one, and most developers do not know either exists.

---

### /loop: The Watchdog

The built-in `/loop` skill runs a prompt on a recurring timer. You give it an interval and a task, and it repeats that task at the specified frequency for the duration of your session. The syntax is minimal:

```bash
/loop 2m Check the deploy status with `gh run view --log-failed`. If it failed, summarize the error.
```

The interval supports seconds, minutes, hours, and days — `30s`, `5m`, `2h`, `1d`. If you omit it, the default is ten minutes. The prompt can be anything: a natural language instruction, a shell command to run, or even another slash command like `/loop 20m /review-pr 1234`.

The key characteristic of `/loop` is that it **repeats blind**. Each iteration runs the same prompt with no memory of previous runs. There is no "last time the deploy was fine, this time it failed" — each cycle is independent. This makes it perfect for monitoring: check a status, report what you see, wait, check again.

```bash
/loop 15m Check open PRs with `gh pr list`. If any have new review comments, summarize them.
```

A few practical details: loops fire only when Claude Code is idle between turns, so they will not interrupt you mid-conversation. They are session-scoped — close the terminal and every loop dies. And they accumulate responses in your context window, so a verbose loop on a short interval will eventually trigger compaction. Keep prompts concise and intervals reasonable.

---

### Ralph Loop: The Builder

Ralph Loop solves the opposite problem. Instead of watching the same thing repeatedly, it **works toward a goal iteratively** — and each iteration builds on the last.

Ralph Loop is a plugin from the official Claude Code marketplace, inspired by the Ralph Wiggum technique: a simple feedback loop where an AI agent keeps working on a task until it is done. It works by installing a Stop hook that intercepts Claude Code's exit. Every time Claude Code tries to finish, the hook feeds the same prompt back, and Claude sees its previous work in files and git history. Each iteration is not a blind repeat — it is a continuation.

```bash
/ralph-loop "Implement a REST API for todos with CRUD operations and tests. Run pytest after each change. Output <promise>COMPLETE</promise> when all tests pass." --max-iterations 20 --completion-promise "COMPLETE"
```

The `--completion-promise` flag defines an exact string that signals genuine completion. Claude must only output it when the statement is truly satisfied — the plugin uses exact string matching, and the prompt explicitly instructs Claude not to fake completion to escape the loop. The `--max-iterations` flag is your safety net. Always set it. An unbounded loop on an impossible task will run until your API budget or your patience runs out.

The results from the community are striking. Teams have reported completing entire contract projects for a fraction of the expected cost by letting Ralph Loop iterate overnight. The technique works best for tasks with **automatic verification** — test suites, linters, type checkers — where Claude can objectively measure its own progress.

---

### When to Use Which

The decision is straightforward once you see the pattern.

**Use `/loop`** when you need periodic monitoring with no state between runs. Deploy status checks, CI pipeline watching, PR review notifications, log file scanning. The prompt is the same every time, and each run is independent. You are asking Claude Code to be a watchdog — look at something, report what you see, go back to sleep.

**Use Ralph Loop** when you need iterative convergence toward a goal. Building features, fixing test suites, refactoring code, implementing specifications. Each iteration produces artifacts — files, commits, test results — that the next iteration reads and builds on. You are asking Claude Code to be a builder — work on something, check your progress, keep going until it is done.

The gotcha is using the wrong loop for the wrong problem. Running `/loop` for a convergence task wastes money — blind repeats do not build on each other, so you pay for the same incomplete work over and over. Running Ralph Loop for monitoring is overkill — you do not need iteration history and completion promises to check whether a deploy succeeded.

Cost matters here. A `/loop` running every five minutes with Opus costs roughly fourteen dollars a day in API calls. Ralph Loop with twenty iterations on a complex feature can cost five to fifteen dollars per run. Neither is free, and neither survives a session restart. For persistence beyond your current terminal, run Claude Code inside `tmux` or `screen`. For truly headless recurring tasks, use system cron with `claude -p` to invoke Claude Code non-interactively.

---

### Prompt Patterns That Work

For `/loop`, keep prompts **self-contained**. Every iteration starts fresh with no memory, so "check if the status changed since last time" will not work — there is no last time. Instead, write prompts that are meaningful in isolation: "Run `gh run view` and report the current status. If the status is failure, include the error summary." Add a condition when possible: "Only notify me if something requires attention." This prevents a wall of "everything is fine" messages cluttering your context.

For Ralph Loop, define **clear completion criteria**. Vague prompts like "make the code better" produce infinite loops. Specific prompts with automatic verification work best: "Run the test suite. If any tests fail, read the failure output, fix the code, and run the suite again. Output the completion promise only when all tests pass." Break complex tasks into phases — authentication first, then CRUD operations, then validation — so Claude has intermediate goals to hit.

For both loops, watch your **context window**. Every iteration's output accumulates in the session. A `/loop` checking deploy status every two minutes for an hour generates thirty responses. Ralph Loop with fifteen iterations on a feature generates fifteen full conversation turns. Both will eventually trigger compaction. If you are running long loops, keep individual responses short, and consider running `/compact` manually between intensive stretches.

---

### Conclusion

Two loops, two purposes. `/loop` watches — periodic, stateless, fire-and-forget. Ralph Loop builds — iterative, cumulative, goal-directed. Start with `/loop` for monitoring because it requires zero setup and comes built in. Graduate to Ralph Loop when you need Claude Code to work autonomously toward a defined outcome. The combination covers both sides of unattended automation: vigilance and persistence. The deploy check that catches a failure at minute three, and the test fixer that turns eight red tests green while you are making coffee.
