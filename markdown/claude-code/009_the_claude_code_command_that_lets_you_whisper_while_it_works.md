# The Claude Code Command That Lets You Whisper While It Works

#### /btw is the side channel your AI pair programmer has been missing

**By Tihomir Manushev**

*Mar 23, 2026 · 4 min read*

---

You are twenty minutes into a refactor. Claude Code is rewriting your authentication layer, three files deep, context loaded with decisions you made earlier in the session. Then a thought hits you: "Wait, did we agree on JWT or session tokens for the mobile endpoints?"

You could type the question into the chat. But that injects a tangent into the conversation history. Claude reads it, shifts focus, answers, and now the context carries that detour for the rest of the session. For a five-second clarification, that is an expensive interruption.

There is a better way. Type `/btw` and ask your question on the side.

---

### What /btw Actually Does

The `/btw` command opens a **side channel** — a one-off question that sees your entire conversation but leaves no trace in it. Think of it as whispering to your pair programmer while they keep typing.

```bash
/btw what auth strategy did we decide on for the mobile API?
```

Claude reads your full conversation context, finds the decision you made earlier, and answers. The answer appears inline, you read it, and the main conversation continues as if nothing happened. No history pollution. No context drift.

Three properties make this work:

1. **Full context visibility.** The side question sees everything — every message, every file read, every decision. It is not a fresh conversation. It knows what you have been building.

2. **No tool access.** `/btw` cannot read files, run commands, or make edits. This is a feature, not a limitation. It forces the answer to come from what is already in context, which keeps it fast and prevents accidental side effects.

3. **Ephemeral by design.** Neither your question nor Claude's answer gets added to the conversation history. The main task never learns about the interruption.

---

### When to Reach for /btw

The command shines in specific situations. Knowing when to use it — and when not to — is the difference between a smooth workflow and a confusing one.

**Recalling earlier decisions.** You agreed on a naming convention in message twelve. By message forty, you have forgotten whether it was `snake_case` or `camelCase`. Instead of scrolling, ask:

```bash
/btw what naming convention are we using for the API response fields?
```

**Checking progress without breaking flow.** Claude is mid-task, working through a multi-file change. You want a quick status check:

```bash
/btw which files have you modified so far in this refactor?
```

Claude can answer from its memory of the conversation without pausing the actual work.

**Clarifying something Claude said earlier.** Maybe Claude mentioned a trade-off three turns back but you did not fully absorb it:

```bash
/btw you mentioned a race condition risk with the caching approach — can you explain that again?
```

You get the explanation without derailing the current task.

**Quick knowledge checks.** You are watching Claude write a database migration and you are not sure about a syntax detail:

```bash
/btw does PostgreSQL support IF NOT EXISTS on ALTER TABLE ADD COLUMN?
```

Claude answers from its training knowledge. No tool call needed, no web search, just a quick answer while the migration continues.

---

### When Not to Use /btw

The command has clear boundaries, and hitting them feels confusing if you do not expect it.

**Do not ask about files that have not been read yet.** Since `/btw` has no tool access, it cannot read files on your behalf. If you ask "what does `config.py` contain?" and that file was never read in the current session, Claude will either say it does not know or hallucinate an answer. Neither is helpful.

**Do not ask it to do things.** Requests like "/btw rename the variable on line 42" will not work. No tool access means no file edits, no shell commands, no actions. It is read-only against your conversation context.

**Do not use it for complex reasoning tasks.** The answer is ephemeral — it vanishes from history. If you need Claude to reason through a design decision that should inform later work, put it in the main conversation so future messages can reference it.

A good mental model: if the answer is something you would jot on a sticky note, glance at, and throw away — use `/btw`. If it is something that should shape the rest of the conversation, type it normally.

---

### The Cost Advantage

Every message in a Claude Code session adds to the context window. The longer the conversation, the more tokens get processed with each new turn. Tangential questions compound this cost.

`/btw` sidesteps the problem entirely. It reuses the parent conversation's **prompt cache** — the context is already loaded and paid for. The side question piggybacks on that cached context, and since neither the question nor answer persists, the main conversation's token count does not grow.

For long sessions — the kind where you are refactoring across ten files over an hour — this adds up. Every avoided tangent keeps the context leaner and the responses faster.

---

### Conclusion

`/btw` is the simplest command in Claude Code and one of the most underused. It gives you a side channel into your AI pair programmer's brain — full context, no tools, no history. Use it to recall decisions, check progress, clarify earlier explanations, or ask quick knowledge questions without polluting your conversation.

Next time you are mid-task and a stray thought hits, do not type it into the main chat. Whisper it.
