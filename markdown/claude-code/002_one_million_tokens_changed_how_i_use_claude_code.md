# One Million Tokens Changed How I Use Claude Code — Here Is What Actually Matters

#### Opus 4.6's 1M context window went GA today — the real impact is not what the changelog says

**By Tihomir Manushev**

*Mar 13, 2026 · 5 min read*

---

You are forty-five minutes into a multi-file refactoring session. Claude Code has read fourteen files, run your test suite twice, and you have just agreed on a migration strategy for the database layer. Then the status bar flickers. Auto-compaction fires. On your next message, Claude Code asks which ORM you are using — a question you answered thirty minutes ago. The session is not ruined, but the momentum is gone. You spend the next five minutes re-establishing context that existed seconds earlier.

This was the reality of working within a 200K token window. Today, Opus 4.6's one-million-token context became generally available at standard pricing — no beta header, no multiplier, no special flags. But the changelog undersells the practical impact and completely ignores the new failure mode this introduces. Larger context windows do not just give you more room. They change how sessions degrade, and managing that degradation is what separates a productive four-hour session from one that quietly falls apart.

---

### What One Million Tokens Actually Buys You

One million tokens is roughly 750,000 words. To put that in project terms: an entire 50,000-line codebase, a full debugging trace with stack frames and log output, and your complete conversation history — all fitting inside a single session without triggering compaction. A refactoring session that used to compact at the 40-minute mark now runs for three to four hours without losing a single token.

Opus 4.6 ships with the 1M window by default. If you are on Sonnet, you opt in explicitly:

```bash
/model sonnet[1m]
```

Pricing is uniform across the entire window. A 900K-token request costs the same per-token rate as a 9K one — $5 per million input tokens, $25 per million output tokens for Opus 4.6. There is no premium tier for using the full capacity.

The output ceiling doubled as well. Opus 4.6 supports 128K output tokens per response, up from 64K on Opus 4.5. Long-form generation — full test suites, multi-file scaffolds, detailed architectural plans — no longer truncates mid-thought.

---

### The Gotcha Nobody Warned You About

More context sounds like a pure upgrade. It is not. There is a phenomenon called **context rot**: as your token count grows, the model's accuracy and recall degrade — even though nothing has been compacted. Attention is not distributed evenly across one million tokens. Information near the beginning and end of the window gets stronger attention than information buried in the middle.

The practical symptom is subtle. Claude Code does not crash or throw an error. Instead, it starts contradicting architectural decisions you agreed on earlier. It re-reads files it already analyzed. It misses constraints you stated clearly an hour ago. You might not even notice until you realize the generated code violates a pattern you established three exchanges back.

Opus 4.6 handles this far better than previous models — it scores 78.3% on the MRCR v2 benchmark at 1M tokens, roughly four times higher than Sonnet 4.5's 18.5%. But 78.3% is not 100%. At maximum capacity, roughly one in five deeply buried details gets missed. The window is massive, but it is not perfect, and trusting it blindly is the fastest way to introduce inconsistencies into a long session.

---

### Strategic Compaction

The fix is not to avoid using the full window. It is to compact **proactively and deliberately** instead of waiting for auto-compaction to make the decision for you. Auto-compaction triggers at roughly 95% capacity, which means by the time it fires, Claude Code has already been operating with degraded recall for a while.

Manual compaction with targeted instructions lets you control exactly what survives:

```bash
/compact Keep all architectural decisions, modified file paths, and test results. Discard raw file contents and exploratory searches.
```

This single command drops the noise — verbose tool output, file reads that already informed decisions — while preserving the critical context that keeps your session coherent.

For sessions where you know you will be working for hours, embed compaction instructions directly in your CLAUDE.md so that auto-compaction also follows your priorities:

```markdown
# Compaction Instructions
When compacting, always preserve:
- Architectural decisions and the reasoning behind them
- File paths that were modified or created
- Test results (pass/fail status, not full output)
Discard: raw file contents, verbose tool output, searches that led nowhere.
```

When auto-compaction eventually fires, it reads these instructions and applies them automatically. You get the safety net without the information loss.

If a session goes sideways — Claude Code takes a wrong architectural turn and you want to backtrack — use `/rewind` to roll back to a specific point. If the session is truly saturated and recovery is not worth it, `/clear` resets everything while your CLAUDE.md instructions reload automatically on the next message.

For short, focused tasks where you do not need the full million tokens, you can disable the extended window entirely:

```bash
export CLAUDE_CODE_DISABLE_1M_CONTEXT=1
```

Smaller context means faster responses and lower cost. Not every task benefits from a four-hour memory.

---

### Rules for Long Sessions

After working with the 1M window for several weeks during the beta period, a few patterns emerged consistently:

**Compact at 60-70% capacity, not 95%.** The status bar shows your current token usage. When it crosses two-thirds, run a targeted `/compact`. Waiting for auto-compaction means accepting degraded recall in the final stretch.

**Put compaction instructions in CLAUDE.md.** You will forget to add custom instructions to every manual `/compact` call. CLAUDE.md makes your preferences the default for both manual and automatic compaction.

**Treat two hours as a soft ceiling.** Even with 1M tokens, sessions that run beyond two hours accumulate enough conversational noise that a fresh start with a summary prompt often produces better results. Use `/clear`, then paste a brief summary of where you left off.

**Watch for the re-read signal.** When Claude Code starts re-reading files it already analyzed earlier in the session, that is context rot in action. Do not wait — compact immediately with instructions that preserve your decisions and discard the stale file contents.

---

### Conclusion

The one-million-token context window does not change what Claude Code can do. It changes how long it can do it without losing the thread. The sessions that benefit most are not the ones where you dump an entire codebase into the window and hope for the best. They are the ones where a complex debugging trace, a multi-file refactor, or a careful architectural discussion can stay in memory from start to finish — without the jarring reset of unexpected compaction. Manage the window actively, compact with intention, and treat the expanded context as a resource to be budgeted, not an invitation to be careless.
