# I Made Claude Code Say "Deleting Prod DB" and My Team Lost It

#### The three-line settings change that turns your AI assistant into a comedian

**By Tihomir Manushev**

*Mar 20, 2026 · 4 min read*

---

Claude Code shows a spinning indicator while it works. By default, it cycles through generic verbs like "Thinking" and "Reasoning." I stared at those words for months before discovering you can replace them with whatever you want. Mine now says "Deleting prod DB" and "Downloading a virus." My coworkers have questions.

The feature is called **spinnerVerbs**, and it lives in your `settings.json`. Three lines of config turn a forgettable loading screen into something that makes pair programming sessions genuinely entertaining.

---

### Where the Spinner Lives

Every time Claude Code processes your prompt, a small animated indicator appears in your terminal. It picks a random verb from an internal list and displays it in colored text while the model works. Most people never notice it. Fewer people know it is configurable.

The setting that controls this is `spinnerVerbs` in your Claude Code settings file. You can set it at three levels:

- **Global** (`~/.claude/settings.json`) — applies everywhere, every project
- **Project shared** (`.claude/settings.json`) — applies to the project, shared with your team
- **Project local** (`.claude/settings.local.json`) — applies to the project, only for you

For something as personal as humor, global settings make the most sense. Your jokes should follow you across repos.

---

### Replace vs. Append

The `spinnerVerbs` setting takes two fields: `mode` and `verbs`. The mode controls how your custom verbs interact with the defaults.

**Replace mode** throws out every default verb and uses only yours:

```json
{
  "spinnerVerbs": {
    "mode": "replace",
    "verbs": [
      "Hacking NASA",
      "Deleting prod DB",
      "Downloading a virus"
    ]
  }
}
```

With replace mode, Claude Code will never show "Thinking" or "Reasoning" again. It picks exclusively from your list.

**Append mode** adds your verbs to the existing defaults:

```json
{
  "spinnerVerbs": {
    "mode": "append",
    "verbs": [
      "Hacking NASA",
      "Deleting prod DB",
      "Downloading a virus"
    ]
  }
}
```

With append, you get the original verbs plus yours, mixed randomly. This is the safe choice if you want occasional humor without losing the professional defaults entirely.

I use replace. Go big or go home.

---

### A Curated List for the Brave

Here is the full set I run daily. Every verb is designed to make anyone glancing at your screen do a double take:

```json
{
  "spinnerVerbs": {
    "mode": "replace",
    "verbs": [
      "Hacking NASA",
      "Deleting prod DB",
      "Downloading a virus",
      "Deploying to Friday",
      "Pushing to main",
      "Dropping all tables",
      "Ignoring code review",
      "Disabling the firewall",
      "Running rm -rf /",
      "Skipping unit tests",
      "Hardcoding passwords",
      "Committing node_modules",
      "Rewriting in Rust",
      "Blaming the intern",
      "Googling the error",
      "Copying from Stack Overflow",
      "Turning it off and on",
      "Asking ChatGPT",
      "Refactoring everything",
      "Breaking the build"
    ]
  }
}
```

Copy the entire block into your `~/.claude/settings.json` file. If you already have other settings there, add `spinnerVerbs` as a new top-level key alongside them. The change takes effect immediately — no restart needed.

The best verbs share a pattern: they describe something a developer would never admit to doing, phrased as if Claude Code is doing it right now. "Deploying to Friday" hits because every engineer has a Friday deployment horror story. "Committing node_modules" hits because someone on every team has actually done it.

---

### Spinner Tips: The Other Half

While `spinnerVerbs` controls the action word, Claude Code also shows **tips** below the spinner — short hints about features and shortcuts. These are independently configurable.

To disable tips entirely:

```json
{
  "spinnerTipsEnabled": false
}
```

To replace them with your own:

```json
{
  "spinnerTipsOverride": {
    "excludeDefault": true,
    "tips": [
      "Remember: Friday deploys build character",
      "git push --force and pray",
      "Have you tried turning it off and on again?"
    ]
  }
}
```

Set `excludeDefault` to `false` to mix your custom tips with the defaults, similar to append mode for verbs.

Combining custom verbs with custom tips gives you full control over the waiting experience. The spinner says "Dropping all tables" while the tip below reads "Remember: Friday deploys build character." Your terminal becomes a comedy stage.

---

### Practical Uses Beyond Comedy

Custom spinner verbs are not just for laughs. Teams use them for practical purposes too.

**Team identity.** A shared `.claude/settings.json` in your repo can set project-specific verbs. A data pipeline team might use "Transforming," "Ingesting," "Validating." A frontend team might use "Rendering," "Hydrating," "Bundling." It is a small touch that makes the tool feel like it belongs to your team.

**Onboarding cues.** New team members see the spinner constantly during their first days. Verbs like "Reading the codebase" or "Learning the patterns" subtly reinforce that Claude Code is doing real work, not just generating text.

**Conference demos.** Nothing breaks the ice in a live demo faster than your AI assistant claiming to be "Hacking NASA." It gets a laugh, opens a conversation about customization, and shows the audience that Claude Code is configurable at a level they might not expect.

---

### Conclusion

The `spinnerVerbs` setting is a three-line change in `settings.json` that replaces Claude Code's default loading text with whatever you want. Use `"replace"` to go all-in on custom verbs, or `"append"` to mix them with defaults. Pair it with `spinnerTipsOverride` for full control over the waiting experience.

My spinner currently says "Asking ChatGPT." If that does not make you want to customize yours, nothing will.
