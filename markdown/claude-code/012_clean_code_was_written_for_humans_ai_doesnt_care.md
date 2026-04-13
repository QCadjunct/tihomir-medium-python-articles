# Clean Code Was Written for Humans. AI Doesn't Care.

#### The 3,167-line function in Claude Code's source changes how we think about software craftsmanship

**By Tihomir Manushev**

*Apr 3, 2026 · 7 min read*

---

Robert C. Martin's "Clean Code" has been gospel for nearly two decades. Keep functions short. One level of abstraction per function. No more than three parameters. Minimize nesting. Every rule exists for one reason: human brains are small. We can hold about seven things in working memory at once, we lose track of logic past three levels of indentation, and we forget what a variable meant if it was declared 200 lines ago.

Then Anthropic accidentally leaked the source code of Claude Code, and developers found a single function spanning 3,167 lines with 12 levels of nesting and a cyclomatic complexity of 486. The file it lived in was 5,594 lines long. That function handled the agent run loop, signal interrupts, rate limiting, authentication, MCP lifecycle, plugin management, model switching, and turn recovery — all in one place.

And it worked. It shipped. It served millions of users daily.

That function was written by AI, for AI to maintain. And it raises a question that the software industry is not ready for: if the writer and reader of code are both machines, does clean code still matter?

---

### Why Clean Code Exists

Every principle in clean code traces back to a cognitive constraint.

**Short functions** exist because humans cannot mentally simulate long sequences of operations. When a function exceeds 20-30 lines, we start scrolling, and scrolling means context switching, and context switching means bugs.

**Low nesting** exists because each level of indentation adds a condition the reader must hold in their head. By level four or five, most developers have lost track of which branch they are in.

**Single responsibility** exists because humans reason about one concept at a time. A function that does authentication and logging and rate limiting forces the reader to juggle three mental models simultaneously.

**Descriptive naming** exists because humans cannot look up a variable's definition instantly. `calculate_monthly_revenue` saves a trip to line 14 where `x` was assigned. Machines do not need this hint — they track every binding in scope with zero effort.

**Small files** exist because humans navigate code visually. A 5,000-line file is not harder for a parser to process. It is harder for a person to scroll through.

Every rule in Clean Code is a patch for a wetware limitation. Remove the wetware, and the rules lose their reason to exist.

---

### What AI Actually Sees

An LLM reading code does not experience it the way you do. It does not scroll. It does not forget what happened 2,000 lines ago. It does not lose track of nested conditions. The entire file lands in the context window as a flat sequence of tokens, and attention mechanisms let the model reference any part of it with equal ease.

A 3,167-line function and thirty well-factored 100-line functions are, to an LLM, the same information arranged differently. The model does not find one easier to reason about than the other. If anything, the monolithic version is slightly easier — all the logic is co-located, no jumping between files, no chasing abstractions through layers of indirection.

This explains why AI-generated code gravitates toward longer functions and fewer files. The AI is not being lazy. It is optimizing for its own cognition. When Claude Code writes Claude Code, it produces structures that make sense to an agent that holds 200,000 tokens in perfect recall. Those structures look alien to humans because they are not designed for humans.

---

### The Uncomfortable Thought Experiment

Imagine a codebase that no human will ever read. Your product is managed entirely by AI agents — they write the code, review the pull requests, debug the failures, deploy the fixes. You interact only through natural language: "Add a payment retry system with exponential backoff." The agent writes it, tests it, deploys it. You never see a line of code.

In that world, does it matter if the code is clean?

The honest answer is no. Clean code is a communication protocol between humans. If no human is in the loop, the protocol serves no one. The code could be a single million-line file with variables named `a` through `zzz` and it would function identically, as long as the AI maintaining it can parse and modify it correctly.

This is not a hypothetical future. It is happening now in narrow domains. GitHub Actions workflows generated and maintained by AI agents. Infrastructure-as-code managed by autonomous deployment pipelines. Glue scripts that connect APIs — written once by AI, modified only by AI, never read by a person.

---

### Why It Still Matters (For Now)

The thought experiment breaks down the moment a human re-enters the picture. And humans re-enter the picture constantly.

**Debugging production incidents at 3 AM.** When the payment system fails and the AI cannot figure out why, a human opens the code. If that code is a 3,000-line function with 12 nesting levels, the human is slower to diagnose the problem. Response time matters during outages. Clean code is not a luxury — it is operational readiness.

**Onboarding new team members.** A developer joining your team needs to understand the system. AI can explain code, but the developer still needs a mental model. Well-structured code provides that model for free. A monolithic function provides noise.

**Auditing for compliance and security.** Regulated industries require human code review. An auditor cannot sign off on code they cannot understand. Clean structure is not about aesthetics — it is about accountability.

**When the AI is wrong.** Language models hallucinate. They introduce subtle bugs that pass tests. When you suspect the AI made a mistake, you read the code. At that moment, every clean code principle exists to save your time.

The transition period is the hardest. We are in a world where AI writes most of the code but humans still bear responsibility for it. Clean code principles are not for the AI — they are for the human who has to step in when the AI falls short.

---

### The Real Question: Who Is the Audience?

The clean code debate was never really about rules. It was about audience. Martin's principles assume the audience is a human developer six months from now who has forgotten the original context. Every rule optimizes for that reader.

If the audience changes, the rules should change too.

Code written by AI for AI to maintain in a fully autonomous pipeline has a different audience. The optimization target shifts from "human readability" to "machine modifiability." Maybe long functions are fine if the AI can modify them reliably. Maybe deep nesting is acceptable if attention mechanisms handle it without degradation. Maybe single-character variable names are tolerable if the model tracks bindings perfectly.

But code written by AI for humans to review, debug, or audit should follow human-centric principles. The writer being an AI does not change the reader being a human.

This means the answer is not "clean code is dead" or "clean code still matters." The answer is: **know your audience.**

If no human will ever read it, optimize for machine efficiency. Let the AI write its alien monoliths. If a human might read it — during an outage, during onboarding, during an audit — enforce clean code principles as a constraint on the AI's output. Most AI coding tools already accept style constraints. Tell them to keep functions short. They will comply. They just will not do it by default, because they do not need to.

---

### What Changes Going Forward

Three shifts are already happening.

**Clean code becomes a configuration, not a discipline.** Instead of training junior developers to write clean code through years of practice and code review, teams will configure their AI agents with style constraints. "Maximum function length: 50 lines. Maximum nesting depth: 3. Maximum file length: 300 lines." The AI follows these constraints mechanically. The craft of clean code becomes a settings file.

**Code review shifts from style to intent.** When AI handles formatting, naming, and structure, human reviewers can focus entirely on whether the code does the right thing. "Is this the correct business logic?" replaces "Should this variable be renamed?" The quality of review goes up even as the volume of code increases.

**Two-tier codebases emerge.** Human-facing code — libraries, APIs, shared modules — stays clean because humans interact with it. Machine-facing code — generated pipelines, glue logic, one-off scripts — is allowed to be messy because no one reads it. The boundary between the two tiers becomes an explicit architectural decision.

---

### Conclusion

Clean code was a brilliant solution to a real problem: humans writing software for other humans to maintain. Every principle in it compensates for a cognitive limitation that AI does not share. The 3,167-line function in Claude Code's source works not despite its size but because its author and maintainer operate without the constraints those rules were designed to address.

But we do not live in a fully autonomous world yet. Humans debug, audit, review, and extend AI-generated code daily. As long as a human might open the file, clean code principles protect that human's time and sanity.

The question is no longer "should code be clean?" It is "will a human read this?" Answer that honestly, and the right level of structure follows naturally.
