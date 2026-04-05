# Claude Code Hooks: Automate Everything Between Your Commits

#### Hooks guarantee that your rules run every time — CLAUDE.md only asks nicely

**By Tihomir Manushev**

*Mar 14, 2026 · 5 min read*

---

You added "never modify database migration files" to your CLAUDE.md. Claude Code followed the instruction — for weeks. Then one long session, one context-heavy moment where the model's attention was stretched thin, and it edited a file inside `alembic/versions/` without hesitation. The migration broke staging. The instruction was right there in the project root, but "right there" is not the same as "enforced."

CLAUDE.md instructions are suggestions. The model follows them reliably, but "reliably" is not "always." When the difference between those two words matters — when a wrong edit breaks a deployment pipeline or overwrites a protected config — you need something stronger. That is what hooks are. They are shell commands that fire at specific points in Claude Code's lifecycle, and they execute deterministically. Every time, no exceptions.

---

### The Mental Model

Hooks respond to **lifecycle events**. Claude Code emits events at key moments: before a tool runs, after it finishes, when a session starts, when the model stops generating. You attach shell commands to these events, and they fire automatically whenever the event occurs.

The community has settled on a clean decision framework: if it is a suggestion, put it in CLAUDE.md. If it is a requirement, use a hook. If it needs an external service, use MCP. Hooks occupy the enforcement layer — the things that must happen regardless of how the model is feeling about your instructions today.

Claude Code supports four hook types: **command** (shell scripts), **HTTP** (POST to an endpoint), **prompt** (single-turn LLM evaluation), and **agent** (multi-turn subagent with tool access). Command hooks are the workhorse. They cover ninety percent of real-world use cases and are the focus of this article.

Configuration lives in `.claude/settings.json` at your project root. This file is committable — your entire team shares the same hooks. For personal hooks that should not be shared, use `~/.claude/settings.json` instead.

---

### Your First Hook: Blocking a Tool Call

The most immediately useful hook pattern is **blocking a tool call before it executes**. The `PreToolUse` event fires every time Claude Code is about to use a tool — Edit, Write, Bash, Read, anything. You attach a command that inspects the tool's input, decides whether to allow it, and either proceeds or blocks with a feedback message.

Here is the migration file blocker that would have prevented the incident in the introduction:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path // empty' | grep -q 'alembic/versions' && echo 'Blocked: migration files are read-only' >&2 && exit 2 || exit 0"
          }
        ]
      }
    ]
  }
}
```

The `matcher` field is a regex that filters which tools trigger the hook — here, only `Edit` and `Write` calls. The command receives the full tool input as JSON on stdin. It extracts the file path with `jq`, checks whether it matches the protected directory, and makes a binary decision. Exit code **0** means proceed. Exit code **2** means block, and whatever you write to stderr becomes the feedback message Claude Code sees. Any other exit code is treated as a non-blocking error.

One gotcha: matchers are **case-sensitive** and use PascalCase. The tool is `Edit`, not `edit`. `Bash`, not `bash`. Get the casing wrong and your hook silently never fires.

---

### Three Hooks That Changed My Workflow

**Auto-format after every write.** Claude Code generates well-structured code, but it does not always match your project's exact formatting rules. This PostToolUse hook runs your formatter automatically after every file edit:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "FILE=$(jq -r '.tool_input.file_path // empty') && [[ \"$FILE\" == *.py ]] && $HOME/.local/bin/ruff format \"$FILE\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

Every time Claude Code writes or edits a Python file, Ruff formats it immediately. Notice the full path `$HOME/.local/bin/ruff` — hooks run in a shell environment that may not include your user-installed tools on `PATH`. If you installed Ruff with `uv tool`, `pipx`, or a similar method, the bare command `ruff` will silently fail and the hook will do nothing. Always use absolute paths for tools that are not system-wide. The `2>/dev/null || true` ensures the hook never fails — a formatting error should not block the session. Swap `ruff format` for `prettier --write` in JavaScript projects.

**Desktop notification when Claude Code stops.** Long-running tasks — multi-file refactors, test suite fixes, architectural changes — take minutes. Instead of watching the terminal, let the system tell you when it is done:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Task completed' 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

An empty `matcher` means the hook fires on every Stop event. On macOS, replace `notify-send` with `osascript -e 'display notification \"Task completed\" with title \"Claude Code\"'`.

**Context preservation after compaction.** The `PostCompact` event fires after auto-compaction summarizes your conversation. You can use it to re-inject critical context that compaction might have dropped — project-specific constraints, in-progress decisions, or file paths that need to stay visible. This pairs naturally with the compaction instructions in CLAUDE.md from our earlier article on the 1M context window.

---

### Gotchas That Will Bite You

**The infinite Stop loop.** A Stop hook can cause Claude Code to produce additional output, which triggers another Stop event, which fires the hook again. Always check the `stop_hook_active` field in the input JSON — if it is true, your hook is being called recursively and should exit immediately.

**Shell profile corruption.** Hooks execute in a shell that sources your profile. If your `.bashrc` or `.zshrc` contains bare `echo` statements, their output gets mixed into the JSON stdin and breaks parsing. Wrap any profile output in an interactive-shell guard: `if [[ $- == *i* ]]; then echo "welcome"; fi`.

**PostToolUse cannot undo.** By the time PostToolUse fires, the tool has already executed. The file is already written, the command has already run. If you need to prevent an action, use PreToolUse. PostToolUse is for reactions — formatting, logging, notifications — not prevention.

**jq is not optional.** Hooks receive structured JSON on stdin. Parsing it with `grep` and `sed` is fragile and will break on edge cases. Install `jq`. It turns hook scripts from brittle string matching into reliable JSON queries.

**Hooks load at session start.** If you create or modify `.claude/settings.json` during a session, the changes will not take effect until you restart Claude Code. This is easy to miss — you add a new hook, test it, nothing happens, and you spend twenty minutes debugging a config that is perfectly valid but simply not loaded yet. Save yourself the trouble: restart after any hook change.

**Timeouts are real.** Command hooks default to a 10-minute timeout. If your hook hangs — waiting for a network call, stuck on a file lock — Claude Code waits with it. Keep hooks fast. If you need a long-running side effect, launch it in the background.

---

### Conclusion

Hooks fill the gap between "Claude Code should do this" and "Claude Code must do this." CLAUDE.md handles the first category well. Hooks handle the second. Start with one — the migration blocker, the auto-formatter, or the stop notification — and add more as you discover which parts of your workflow need guarantees instead of suggestions. The configuration lives in `.claude/settings.json`, which means your hooks are committable, reviewable, and shared across the team. Guardrails that travel with the project, not with the developer.
