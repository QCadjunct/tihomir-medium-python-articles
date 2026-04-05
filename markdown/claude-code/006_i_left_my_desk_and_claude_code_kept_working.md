# I Left My Desk and Claude Code Kept Working — Remote Control Changed Everything

#### Start a refactor at your desk, approve file edits from your phone, and never lose a session again

**By Tihomir Manushev**

*Mar 18, 2026 · 5 min read*

---

You are twelve files into a multi-module refactor. Claude Code is rewriting service interfaces, updating tests, and fixing imports as they break. Then your partner calls you to dinner. Close the laptop and lose the session — thirty minutes of accumulated context, gone. Keep it open and eat with one eye on the terminal — rude and inefficient. There was no middle ground.

Remote Control is that middle ground. It connects your local Claude Code session to claude.ai/code and the Claude mobile app — iOS and Android. Claude keeps running on your machine with full access to your filesystem, MCP servers, and project configuration. Your phone is just a window into the session. You walk away from your desk, and the work continues. When Claude needs permission to edit a file, the prompt appears on your phone. You tap approve, put the phone back in your pocket, and finish dinner.

---

### Three Ways In

Remote Control offers three entry points depending on where you are in your workflow.

**Server mode** starts a dedicated process that waits for remote connections. It stays running in your terminal, displays a session URL and a QR code, and handles multiple concurrent sessions:

```bash
claude remote-control --name "API Refactor"
```

**New session with remote access** launches a full interactive session that is also available remotely. You can type locally and connect from another device simultaneously:

```bash
claude --rc "My Project"
```

**Promote an existing session** is the one you will use most often. You are already mid-conversation, you realize you need to leave, and you want to take the session with you. The conversation history carries over:

```bash
/rc
```

Press spacebar in the terminal to toggle the QR code. Scan it with the Claude app, or open the session URL in any browser. Your session appears at claude.ai/code with a green dot indicating it is online. For permanent setup, run `/config` and enable "Remote Control for all sessions" — every future session becomes remotely accessible automatically.

---

### What Stays Local, What Travels

The architecture matters because it determines what you are trusting and to whom. Remote Control uses **outbound HTTPS only**. Claude Code never opens an inbound port on your machine. When you start a remote session, the local process registers with the Anthropic API and polls for incoming messages. When you connect from your phone, the API routes messages between the remote client and your local session over a streaming connection.

**What stays on your machine**: your files, your MCP servers, your environment variables, your project configuration, and all code execution. Nothing runs on Anthropic's infrastructure.

**What travels through the network**: chat messages and tool results — the same data that flows during any Claude Code session — encrypted via TLS. The connection uses multiple short-lived credentials, each scoped to a single purpose and expiring independently. If one credential is compromised, the blast radius is limited.

This is not Claude Code on the Web, which runs on Anthropic-managed cloud VMs. Remote Control runs on *your* machine. That distinction matters for security-conscious teams and for anyone whose codebase cannot leave their network.

One gotcha: **sandbox is off by default**. The `--sandbox` flag exists for filesystem and network isolation, but you have to opt in. Without it, Claude Code has the same access to your local filesystem as it does in any normal session. If you are making your session remotely accessible, consider whether sandboxing is appropriate for your use case.

---

### The Workflows That Click

**The Walk-Away Pattern.** Start a complex task at your desk — a refactor, a test suite fix, a feature build. When you need to leave, type `/rc` and go. Claude Code keeps working. When it hits a permission request — "Allow Edit to `src/services/auth.py`?" — the prompt appears on your phone. You tap approve without breaking stride. This is the pattern that changes the relationship with long-running tasks. You no longer babysit the terminal waiting for permission dialogs.

**The Couch Review.** Queue up code reviews from your terminal during the workday. In the evening, connect from your browser on the couch. The conversation history is there, the files are accessible, and the reading experience in claude.ai/code is more comfortable than a terminal for reviewing diffs and explanations.

**Server Mode for Teams.** A shared development server running Remote Control in server mode can host multiple developers simultaneously, each in their own isolated git worktree:

```bash
claude remote-control --spawn worktree --capacity 8
```

Eight developers connect from their browsers, each getting a clean branch to work in. The worktrees are created automatically, and each session has full access to the project's tools and configuration. This turns a single powerful machine into a shared Claude Code environment.

**Combining with /loop.** Start a monitoring loop from the previous article — `/loop 5m check deploy status` — then `/rc` and walk away. Periodic status updates appear on your phone. When the deploy fails, you see it immediately, wherever you are.

---

### What It Cannot Do

**The terminal must stay open.** Closing it kills the session. If you need persistence beyond your current shell, run Claude Code inside `tmux` or `screen`. The session survives disconnects, laptop sleep, and SSH drops.

**Network timeouts are real.** If your machine cannot reach the Anthropic API for roughly ten minutes, the session exits. Brief interruptions — laptop sleep, Wi-Fi switching — recover automatically.

**No API key authentication.** Remote Control requires a claude.ai subscription — Pro, Max, Team, or Enterprise. API keys are not supported. Team and Enterprise admins must explicitly enable Claude Code in their admin settings before developers can use Remote Control.

**No permission skipping.** The `--dangerously-skip-permissions` flag is not supported with Remote Control. Every file edit, every bash command, every tool invocation requires explicit approval through the remote interface. This is a security feature, not a limitation — but it means you will be tapping "approve" frequently during active sessions.

**One session per process** unless you use server mode with `--spawn`. For concurrent sessions from a single machine, server mode is required.

Finally, understand how Remote Control differs from headless mode. `claude -p "your prompt"` is for automation — a single prompt, a single response, designed for scripts and CI pipelines. Remote Control is for ongoing interactive sessions across multiple devices. They solve different problems and complement each other.

---

### Conclusion

Remote Control does not change what Claude Code can do. It changes where you can be while it does it. The terminal was the last physical constraint tying you to your desk during long-running tasks. Now it is just one of many windows into your session — alongside your browser, your phone, and your tablet. Type `/rc` at the start of your next long session. Walk away when you need to. Come back to progress, not a stale terminal.
