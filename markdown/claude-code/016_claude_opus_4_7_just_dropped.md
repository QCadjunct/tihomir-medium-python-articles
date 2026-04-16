# Claude Opus 4.7 Just Dropped — The Benchmarks Are Real, But Three Breaking Changes Will Catch You Off Guard

#### 87.6% on SWE-bench Verified, a new /ultrareview command, and a tokenizer that charges you 35% more per prompt

**By Tihomir Manushev**

*Apr 16, 2026 · 6 min read*

---

Anthropic shipped Claude Opus 4.7 today. The benchmark numbers are the kind that make you reach for the update button without reading further: 87.6% on SWE-bench Verified, triple the production task completion on Rakuten's real-world coding suite, and a 13-point jump over Opus 4.6 on Anthropic's internal 93-task coding benchmark. Low-effort 4.7 now roughly matches medium-effort 4.6 — a meaningful cost-quality shift for anyone running agentic workloads at scale.

But before you bump your model ID and ship, there are three hard API breaking changes and one silent tokenizer shift that will bite you if you upgrade without reading the release notes. Here is what actually changed, what it means for Claude Code users, and what to do about the migration.

---

### The Benchmarks Are Not Just Marketing

Opus 4.7 is the first Claude release in a while where the gains show up where developers actually feel them. On SWE-bench Verified — the benchmark that measures real GitHub issue resolution — it lands at 87.6%, up from 80.8% on Opus 4.6. On the harder SWE-bench Pro, it hits 64.3%, comfortably ahead of GPT-5.4 at 57.7% and Gemini 3.1 Pro at 54.2%.

The number that should matter more to teams is the Rakuten-SWE-Bench result: Opus 4.7 resolves three times as many production engineering tasks as 4.6. That is the kind of gap that changes what you trust the model to do autonomously. Tasks that you previously kept on a short leash — multi-file refactors, cross-module bug hunts, migration work — become candidates for longer-running agentic execution.

The long-context story also improved. The 1M-token window is the same size as 4.6, but 4.7 uses it better. Multi-needle recall — pulling specific facts from deep inside a massive context — holds up further into the window. For codebase-scale exploration in Claude Code, that means fewer hallucinations when the file you need is at position 800K instead of 50K.

---

### What's Actually New

The feature additions are focused and pragmatic.

**`/ultrareview`** is a new Claude Code slash command dedicated to code review sessions. It spins up a review pass with more thorough instruction-following, designed specifically for bug detection. If you use `/simplify` today, `/ultrareview` is its deeper, slower sibling — the one you run on the PR that has to ship to prod tonight.

**`xhigh` effort level** sits between `high` and `max` on the effort slider. Anthropic recommends starting with `xhigh` for coding and agentic use cases where `high` was the previous default. It gives you finer control over the capability-latency trade-off without jumping all the way to `max`.

**Task budgets** enter public beta behind the `task-budgets-2026-03-13` header. Unlike `max_tokens`, which is a hard per-request ceiling the model never sees, a task budget is an advisory target across the full agentic loop that the model watches:

```python
response = client.beta.messages.create(
    model="claude-opus-4-7",
    max_tokens=128000,
    output_config={
        "effort": "xhigh",
        "task_budget": {"type": "tokens", "total": 128000},
    },
    messages=[{"role": "user", "content": "Refactor the billing module."}],
    betas=["task-budgets-2026-03-13"],
)
```

The minimum budget is 20K tokens. Set it too low and the model completes tasks less thoroughly — or refuses outright. Leave it off entirely for open-ended work where quality matters more than cost predictability.

**High-resolution image support** jumps from 1568px to 2576px on the long edge, about 3.75 megapixels — over three times the previous cap. For computer use, screenshot understanding, and UI-heavy workflows, this removes the downsampling step that used to blur the details the model most needed to see.

---

### The Three Breaking Changes

Here is where the careful reading pays off. All three are Messages API breaking changes that will cause 400 errors if you migrate naively.

**Extended thinking budgets are gone.** Setting `thinking: {"type": "enabled", "budget_tokens": N}` now returns a 400 error. Adaptive thinking is the only thinking-on mode, and it is off by default:

```python
# Before (Opus 4.6)
thinking = {"type": "enabled", "budget_tokens": 32000}

# After (Opus 4.7)
thinking = {"type": "adaptive"}
output_config = {"effort": "xhigh"}
```

**Sampling parameters are gone.** `temperature`, `top_p`, and `top_k` all return 400 if set to any non-default value. Remove them from every call. If you were using `temperature=0` for determinism — it never guaranteed identical outputs anyway. Steer behavior through prompting instead.

**Thinking content is hidden by default.** This one is silent — no error, no warning. If your product streams reasoning to users, the first thing you will notice is a long pause before output begins. Thinking blocks still appear in the stream, but their `thinking` field is empty unless you opt in with `display: "summarized"`.

And then the change that is not in the breaking-changes section but will blow up your token budgets anyway: **a new tokenizer**. Opus 4.7 uses between 1x and 1.35x the tokens of Opus 4.6 for the same text — up to 35% more, depending on content shape. Your existing `max_tokens` values may truncate responses that used to fit. Increase the headroom before rolling out, and revisit your compaction triggers.

---

### The Behavior Changes Nobody Talks About

The release notes also flag behavior shifts that are not API errors but will still surprise you.

Opus 4.7 is **more literal**. It will not generalize "and similar items" from a single example — if you want it to handle the whole list, name the list. It uses **fewer tool calls by default**, preferring reasoning to action. Raise the effort level if your workflow depends on aggressive tool use. It spawns **fewer subagents by default**, so if you lean on parallelism, prompt for it explicitly.

The tone shifted too — less validation-forward, fewer emoji, more direct. The warm "Great question!" openers from 4.6 are largely gone. It also gives more frequent progress updates during long traces. If you added scaffolding that forced interim status messages, you can strip it.

---

### Conclusion

Opus 4.7 is a real step up, not a point-release refresh. The coding gains land in the right places for Claude Code users — autonomous long-horizon tasks, codebase-scale reasoning, better file-system memory for agents with scratchpads. The `/ultrareview` command and task budgets give you new tools that were not possible before.

But the upgrade is not free. Three API breaking changes, a silent tokenizer shift that costs up to 35% more per prompt, and half a dozen behavior changes mean you cannot just bump the model ID and ship. Read the migration guide. Update your `max_tokens` headroom. Retest your prompts, especially the ones that relied on the old validation-forward tone or implicit generalizations. The model is stronger — but it also expects you to be more precise.
