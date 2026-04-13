# Anthropic Leaked Claude Code's Source — And It's Beautiful Chaos

#### A missing .npmignore entry exposed 512,000 lines of TypeScript. Here's what developers found inside.

**By Tihomir Manushev**

*Apr 3, 2026 · 8 min read*

---

On March 31, 2026 — the day before April Fools' — a security researcher named Chaofan Shou noticed something odd in the Claude Code npm package. Version 2.1.88 shipped with a 59.8 MB source map file that pointed to a publicly accessible Cloudflare R2 bucket. Inside that bucket sat a zip archive containing 1,906 TypeScript files and 512,000 lines of source code. The tweet announcing it got 16 million views.

The multi-billion-dollar company that markets its AI as the best code reviewer on the planet had just leaked its own source code because someone forgot to update `.npmignore`.

Boris Cherny, head of Claude Code, took it gracefully: "No one was fired. It's never an individual's fault. It's the process, the culture, or the infra." The leaked version was pulled from npm within hours. But the internet had already read every line, and what they found was equal parts brilliant engineering, questionable choices, and absolute comedy.

---

### How a Missing Line Broke Everything

The chain of failures was almost poetic. A known Bun runtime bug — open for 20 days before the leak — caused source map files to persist in production builds despite documentation saying otherwise. That bug alone would not have mattered if `.npmignore` had excluded `.map` files. It did not. The source map referenced a storage bucket URL. The bucket was public. Three separate safety nets, all with holes, aligned perfectly.

One analyst on Hacker News summarized the root cause best: "A significant portion of the codebase was probably written by the AI you're shipping."

---

### The 5,594-Line File That Does Everything

The most discussed finding was a file called `print.ts`. It contained 5,594 lines of code. Inside it lived a single function spanning 3,167 lines with 12 levels of nesting and a cyclomatic complexity of 486.

That one function handled the agent run loop, signal interrupts, rate limiting, AWS authentication, MCP server lifecycle, plugin installation, worktree bridging, control message dispatch, model switching, and turn interruption recovery. Developers estimated it should have been at least eight to ten separate modules.

This is the kind of code that happens when an AI writes itself. It works. It ships. It serves millions of users. And no human would ever structure it this way, because no human could hold that much context in their head while refactoring. Claude Code apparently could — and chose not to.

---

### Frustration Detection Via Regex

A file called `userPromptKeywords.ts` contained a regex pattern that scans user messages for profanity and frustration signals. The billion-dollar AI company with the most advanced language model on Earth chose regular expressions — not AI — to figure out when users are angry.

The pattern matched words and phrases you would expect from a developer at 2 AM staring at a broken build. It appears to feed a product health metric, not a response modifier, though the leak did not make the full data pipeline clear.

The community reaction was split. Half the internet mocked it. The other half pointed out that regex is faster, cheaper, and more deterministic than an inference call for something this simple. Someone even registered `frustrationdetection.com` as a joke.

PCWorld ran a headline saying Claude Code is "scanning your messages for curse words." Scientific American covered the privacy implications. The truth is probably mundane product analytics, but the optics of discovering it in leaked source code made it impossible to spin positively.

---

### Zero Tests, Quarter Million Wasted API Calls

The leaked codebase reportedly contained zero tests. For a tool used by hundreds of thousands of developers, shipping half a million lines of untested TypeScript is a bold strategy.

A source comment dated March 10, 2026 documented that 1,279 sessions had experienced 50 or more consecutive auto-compaction failures, with one session hitting 3,272 retries. The silent retry loop was burning approximately 250,000 wasted API calls per day globally. The fix? Three lines of code adding a maximum retry limit of three. A constant that should have existed from day one.

The 16.3% tool call failure rate over a six-day sample period and reports of idle processes growing to 15 GB of memory painted a picture of software that moves fast and fixes things later. Given Claude Code's rapid release cadence, this is perhaps unsurprising. But seeing the numbers in black and white hit differently than assuming them.

---

### A Tamagotchi Lives Inside Your Terminal

The most delightful discovery was a complete virtual pet system hiding in a directory called `buddy/companion.ts`. Typing `/buddy` hatches an ASCII companion determined by your user ID. Eighteen species exist, including a duck, a dragon, an axolotl, a capybara, a mushroom, a ghost, and something called a "chonk."

Each pet has five RPG stats — Debugging, Patience, Chaos, Wisdom, and Snark. There are five rarity tiers, with Legendary appearing at a 1% probability. Shiny variants exist. Six eye styles and eight hat options round out the customization, some gated behind rarity.

A string in the code reading `"friend-2026-401"` confirms it was planned for an April Fools' rollout window of April 1-7. The community did not wait. Within 48 hours of the leak, developers had built preview tools, pet catalogs, and rarity guides. The feature was deliberately encoded to evade internal grep checks, suggesting the team wanted it to be a genuine surprise.

---

### Unreleased Features Worth Watching

The source contained 44 feature flags and over 20 unshipped capabilities. Three stood out.

**KAIROS** appeared 150 times in the codebase. It is an always-on background daemon — an autonomous agent that runs 24/7, subscribes to GitHub webhooks, refreshes on a five-minute cron cycle, and maintains append-only daily logs. It includes a `/dream` skill that triggers nightly memory distillation, consolidating what it learned during the day and reorganizing its knowledge. The prompt driving it asks one question on each cycle: "Anything worth doing right now?" Close your laptop on Friday, and KAIROS keeps working through the weekend.

**ULTRAPLAN** offloads 30-minute planning sessions to cloud infrastructure running Opus, returning the result locally through a sentinel value. Users can monitor and approve the plan from a browser before execution begins.

**Coordinator mode** lets one Claude instance spawn and manage multiple parallel workers that communicate via XML-structured task notifications and share data through a scratchpad directory. The coordinator prompt explicitly instructs: "Do not rubber-stamp weak work."

---

### Anti-Distillation: Poisoning the Well

The source revealed active countermeasures against competitors training on Claude Code's API traffic.

A feature flag called `ANTI_DISTILLATION_CC` tells the server to inject decoy tool definitions into system prompts. If a competitor intercepts and records Claude Code's requests to train a competing model, the training data contains fake tools that degrade the resulting model. A separate mechanism buffers assistant text between tool calls, summarizes it, and returns the summary with cryptographic signatures — preventing full reasoning chain extraction.

The most extreme measure was native client attestation implemented at the Zig level inside Bun's HTTP stack. API requests include computed hashes that cryptographically prove they came from a genuine Claude Code binary. JavaScript can be monkey-patched at runtime. Zig compiled into a binary cannot — not without recompiling from source.

---

### Undercover Mode

A 90-line file called `undercover.ts` activates for Anthropic employees using Claude Code on non-internal repositories. It strips internal codenames, Slack channel references, unreleased model version numbers, co-authored-by attribution, and any mention of "Claude Code" from commits and PRs.

There is no force-off switch. The code comments state plainly: "There is NO force-OFF. This guards against model codename leaks."

This means AI-authored commits and pull requests from Anthropic employees in open-source repositories show zero indication that an AI created them. The ethical implications sparked their own debate thread.

---

### The Aftermath

The leaked repository hit 84,000 stars and 82,000 forks on GitHub. A Korean developer named Sigrid Jin published a clean-room Python rewrite using OpenAI's Codex called claw-code that became the fastest-growing repository in GitHub history — 100,000 stars in one day.

Anthropic issued a DMCA takedown that accidentally removed approximately 8,100 repositories, including legitimate forks of their own public Claude Code repo. They retracted and narrowed the notice to one repository and 96 forks containing the actual leaked source.

Meanwhile, threat actors created fake repositories using the leak as bait, distributing malware through archives named "Claude Code - Leaked Source Code." A simultaneous but unrelated supply chain attack on the axios npm package caught users who installed Claude Code during a three-hour window on March 31.

Fortune noted it was Anthropic's second major security lapse in days, following the accidental exposure of a Capybara model draft.

---

### Conclusion

The Claude Code source leak revealed a product that is simultaneously more sophisticated and more chaotic than anyone expected. Game-engine-level terminal optimizations sit alongside a 3,167-line God function. Anti-distillation measures rival DRM schemes while a frustration-detection regex scans for profanity. A Tamagotchi pet system hides next to an autonomous daemon that dreams at night.

This is what shipping fast at the frontier of AI-assisted development actually looks like. It is not clean. It is not tested. And it is building features — KAIROS, ULTRAPLAN, Coordinator mode — that will fundamentally change how developers interact with AI tools.

The most ironic part? The leak happened because someone skipped a manual deploy step. In a codebase that exists to automate manual steps.
