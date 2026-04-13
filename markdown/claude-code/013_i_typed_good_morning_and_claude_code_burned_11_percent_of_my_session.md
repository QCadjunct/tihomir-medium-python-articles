# I Typed "Good Morning" and Claude Code Burned 11% of My Session

#### The invisible cache expiration that makes resuming sessions the most expensive thing you do

**By Tihomir Manushev**

*Apr 6, 2026 · 6 min read*

---

I had been building a feature for five hours. The session was deep — files read, decisions made, code written across eight modules. The context window sat at 40% of Opus 4.6's million-token limit. End of the work day. I closed my laptop and went home.

Next morning, I opened the same session and typed a simple question: "Did we push the changes we made yesterday?" Claude answered in seconds. Straightforward response, nothing unusual. Then I glanced at my usage meter. It had jumped from 0% to 11% on that single question. One sentence consumed more of my daily quota than the first hour of yesterday's session combined.

I thought it was a bug. It was not. It was the prompt cache doing exactly what it is designed to do — and it caught me completely off guard.

---

### How Prompt Caching Works (When It Works)

Every time you send a message in Claude Code, the entire conversation context travels to the API — system prompt, tool definitions, CLAUDE.md, every previous message, every file read, every command output. On Opus 4.6 with a deep session, that can easily be 300,000 to 500,000 tokens.

Reprocessing half a million tokens from scratch on every turn would be ruinously expensive. **Prompt caching** solves this by storing a hash of the prompt content up to a breakpoint. On the next request, if the prefix has not changed, the API reads the cached version instead of reprocessing it.

The cost difference is dramatic. On Opus 4.6:

| Operation | Cost per million tokens |
|-----------|----------------------|
| Base input (no caching) | $5.00 |
| Cache write (storing new cache) | $6.25 |
| Cache read (hitting existing cache) | **$0.50** |

A cache read is **10x cheaper** than base input and **12.5x cheaper** than a cache write. During an active coding session where you send messages every minute or two, every turn after the first hits the cache. The conversation feels cheap because it is cheap — 90% of your input tokens cost a tenth of their base price.

This is why Claude Code works at scale. The million-token context window sounds expensive until you realize that most of it is served from cache on every turn.

---

### The Five-Minute Cliff

The default cache TTL is **five minutes**. Every cache hit resets the timer. So an active session keeps the cache warm indefinitely — as long as you keep talking, the cache lives. But the moment you stop for more than five minutes, the cache expires silently. No warning. No notification. Just gone.

There is an extended TTL option of one hour, but it costs 2x base input on writes instead of 1.25x. Claude Code uses the five-minute default.

Here is what happened to my session overnight:

**During active work (yesterday):**
- Context: ~400K tokens
- Each turn: ~400K cache reads at $0.50/MTok = ~$0.20
- Fast, cheap, responsive

**First message the next morning:**
- Context: still ~400K tokens
- Cache: expired 13 hours ago
- All ~400K tokens reprocessed as cache writes at $6.25/MTok = ~$2.50
- A single "good morning" cost **12.5x** what a normal turn cost yesterday

That is where the 11% came from. Not from the complexity of my question. Not from Claude's answer. From rebuilding the cache of everything we had discussed the day before.

---

### The Math Gets Worse With Scale

The problem compounds with session size. A shallow session with 50K tokens of context barely notices a cache rebuild — it costs maybe $0.31. But developers who work in long sessions with deep context hit a wall.

At 400K tokens of context, here is the cost comparison:

| Scenario | Token operation | Cost |
|----------|----------------|------|
| Active session (cache hit) | 400K × $0.50/MTok | $0.20 |
| Resumed session (cache miss) | 400K × $6.25/MTok | $2.50 |

That is a single turn. If you resume and then ask three or four follow-up questions in quick succession, only the first one pays the full rebuild cost — subsequent turns hit the fresh cache. But that first turn is always the expensive one.

On Max plans where usage is measured in session time rather than raw dollars, the impact shows up differently but feels the same. Users have reported that resuming a large session consumed 15% of their five-hour window on a single prompt. One user watched their quota hit 80% with no input at all — just the overhead of the session loading and rebuilding its cache.

---

### It Was Even Worse Than Natural Expiration

The community discovered that the problem was not limited to natural cache expiration. A detailed analysis of 8,794 API requests revealed multiple bugs in Claude Code's cache handling.

The standalone binary's custom Bun fork was corrupting cache prefixes during string replacement, dropping cache read rates to 4-17% even during active sessions. The `--resume` and `--continue` flags stripped metadata from the session that shifted the internal message array, breaking cache hash alignment entirely. This caused a roughly 20x cost multiplier per resume — far worse than the natural TTL expiration alone.

Fixes shipped in versions 2.1.90 and 2.1.91, but the natural five-minute TTL behavior remains unchanged. Leaving a session overnight will always trigger a full cache rebuild on the first message back.

---

### What You Can Do About It

The overnight cache rebuild is not a bug — it is an inherent property of how TTL-based caching works. But you can manage its impact.

**Compact before you leave.** Run `/compact` with focused instructions before ending your work day. Tell it what to preserve:

```bash
/compact focus on the auth refactor decisions and the list of modified files
```

This reduces context from 400K tokens down to maybe 50K-80K. The cache rebuild the next morning is proportionally cheaper.

**Watch for the "new task?" prompt.** Claude Code detects when you shift to a different task and suggests `/clear` with the exact token savings — something like "new task? /clear to save 229.1k tokens." That number is the context you are about to carry forward and pay to re-cache. When you see it, take the hint. Clearing 229K tokens saves you roughly $1.43 on the next cache rebuild.

**Start fresh instead of resuming.** A well-structured CLAUDE.md gives a new session most of the context it needs. Instead of paying $2.50 to rebuild yesterday's cache, start a clean session for free and let CLAUDE.md carry the essential decisions forward. Use `/resume` only when the conversation history itself is critical — not just out of habit.

**Save key context to files before closing.** If you made important architectural decisions during the session, ask Claude to write them to a markdown file or update your CLAUDE.md. Files persist for free. Conversation history persists at the cost of a cache rebuild.

**Use `/compact` at 60% context proactively.** Do not wait until Claude Code auto-compacts at 95%. At 60%, you still have enough room for the compacted summary to be high quality. At 95%, the summarizer is racing against a wall.

**Delegate verbose operations to subagents.** Large file reads and grep results that inflate your context can live in a subagent's window instead of yours. The subagent returns a concise summary. Your context stays lean, and a cache rebuild the next morning costs less.

---

### The Mental Model That Helps

Think of your session context like a hotel room. While you are staying there (sending messages), the room is yours — warm, ready, cheap to maintain. The moment you check out (stop sending messages for five minutes), housekeeping clears it. If you come back the next morning, you are not returning to your room — you are checking in again, and you pay the full check-in price for every piece of luggage you bring.

The solution is the same as with real hotels: do not leave your entire wardrobe in the room if you are checking out. Pack light. Carry only what you need into the next stay. Leave the rest in long-term storage — CLAUDE.md, notes files, git history — where it costs nothing to keep.

---

### Conclusion

The prompt cache is the invisible engine that makes Claude Code affordable during active sessions — 90% cheaper token processing as long as you keep talking. But the five-minute TTL means that every break longer than five minutes triggers a full cache rebuild on your next message. Overnight breaks are the worst case: hundreds of thousands of tokens reprocessed at 12.5x the cached price.

The fix is not technical. It is behavioral. Compact before you leave. Start fresh when you can. Save decisions to files, not conversation history. Your context window is a rental, not a purchase — and checkout is always five minutes away.
