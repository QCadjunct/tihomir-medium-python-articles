# Python's super() Doesn't Call Your Parent Class

#### How method resolution order turns a simple function call into a dynamic dispatch chain

**By Tihomir Manushev**

*Feb 28, 2026 · 7 min read*

---

Call `super().__init__()` in a subclass, and you expect it to invoke the parent class's initializer. With single inheritance, that assumption holds. Add a second parent, and `super()` starts routing calls to classes you never directly inherited from — siblings, cousins, classes that exist only because someone else combined them into the same hierarchy.

This behavior catches developers off guard when they treat `super()` as shorthand for "call my parent." It is not. `super()` means "call the *next* class in the Method Resolution Order," and the MRO depends on the concrete class of the instance at runtime, not on the class where `super()` appears in source code. Once you internalize this distinction, multiple inheritance in Python shifts from unpredictable to deliberate. You stop guessing where calls go and start reading the MRO like a dispatch table.

---

### What super() Actually Returns

`super()` does not return a reference to a parent class. It returns a **proxy object** that delegates attribute lookups to the next class in the calling instance's MRO. Two pieces of information determine where that delegation lands: the class that contains the `super()` call, and the runtime type of the object receiving the method call.

Python 3 made the syntax deceptively simple. You write `super()` with no arguments, and the bytecode compiler fills in the details — the enclosing class and `self` — behind the scenes. The Python 2 equivalent, `super(CurrentClass, self)`, at least hinted that two parameters were in play. The modern zero-argument form is cleaner, but it hides the mechanism that makes `super()` powerful.

The **Method Resolution Order** is a tuple of classes stored in every class's `__mro__` attribute. Python computes it using the **C3 linearization algorithm** at class creation time. For single inheritance, the MRO is a straight line from child to parent to `object`. For multiple inheritance, C3 produces a flattened sequence that respects two constraints: children appear before parents, and the left-to-right order of bases in each `class` statement is preserved.

```python
class Vehicle:
    pass


class Electric(Vehicle):
    pass


class Autonomous(Vehicle):
    pass


class RoboTaxi(Electric, Autonomous):
    pass


print([cls.__name__ for cls in RoboTaxi.__mro__])
# ['RoboTaxi', 'Electric', 'Autonomous', 'Vehicle', 'object']
```

When `super()` runs inside `Electric` and the instance is a `RoboTaxi`, the proxy skips past `Electric` in the MRO and delegates to `Autonomous` — not `Vehicle`. The direct parent gets bypassed because a sibling sits between them in the linearized order.

---

### Watching super() Chain Through a Diamond

A **diamond** forms whenever two classes share a common ancestor and a fourth class inherits from both. The diamond is where `super()` proves its worth — and where the "call my parent" mental model falls apart.

Here is a notification system that demonstrates the effect:

```python
class Notifier:
    """Base notification handler."""

    def send(self, message: str) -> list[str]:
        """Return a log of every channel that fired."""
        return []


class EmailNotifier(Notifier):
    """Delivers via email."""

    def send(self, message: str) -> list[str]:
        log = super().send(message)
        log.append(f"email: {message}")
        return log


class SlackNotifier(Notifier):
    """Delivers via Slack."""

    def send(self, message: str) -> list[str]:
        log = super().send(message)
        log.append(f"slack: {message}")
        return log


class MultiNotifier(EmailNotifier, SlackNotifier):
    """Broadcasts across all channels."""

    def send(self, message: str) -> list[str]:
        log = super().send(message)
        log.append(f"broadcast: {message}")
        return log
```

Call `send` on a `MultiNotifier` and trace the result:

```python
alert = MultiNotifier()
print(alert.send("server is down"))
# ['slack: server is down', 'email: server is down', 'broadcast: server is down']
```

Every notifier in the hierarchy fired exactly once. The chain unfolded like this:

1. `MultiNotifier.send()` calls `super().send()` → dispatches to `EmailNotifier.send()`
2. `EmailNotifier.send()` calls `super().send()` → dispatches to `SlackNotifier.send()`
3. `SlackNotifier.send()` calls `super().send()` → dispatches to `Notifier.send()`
4. `Notifier.send()` returns `[]`, and each class appends its entry as the stack unwinds

Step 2 is the key insight. `EmailNotifier` inherits directly from `Notifier`, yet its `super()` call routes to `SlackNotifier`. This happens because the MRO of the *instance's* class places `SlackNotifier` between `EmailNotifier` and `Notifier`:

```python
print([cls.__name__ for cls in MultiNotifier.__mro__])
# ['MultiNotifier', 'EmailNotifier', 'SlackNotifier', 'Notifier', 'object']
```

The proxy that `super()` creates inside `EmailNotifier.send()` inspects this tuple, finds `EmailNotifier` at index 1, and delegates to index 2: `SlackNotifier`. The shared ancestor `Notifier` sits at the end, called exactly once, preventing the duplicate invocations that plagued naive C++ multiple inheritance designs.

---

### The Same Code, Different Destination

Here is the most mind-bending consequence of MRO-aware dispatch: the *same* `super()` call in `EmailNotifier.send()` resolves to different classes depending on which concrete type created the instance.

```python
solo = EmailNotifier()
print(solo.send("disk full"))
# ['email: disk full']

combined = MultiNotifier()
print(combined.send("disk full"))
# ['slack: disk full', 'email: disk full', 'broadcast: disk full']
```

When `solo.send()` executes, the MRO is `[EmailNotifier, Notifier, object]`. The `super()` inside `EmailNotifier.send()` goes straight to `Notifier.send()`. Slack never enters the picture.

When `combined.send()` triggers the identical `EmailNotifier.send()` method body, the MRO expands to `[MultiNotifier, EmailNotifier, SlackNotifier, Notifier, object]`. Now `super()` routes to `SlackNotifier.send()` instead.

The code did not change. The runtime context did. `super()` resolves its target at call time based on the instance's `__mro__`, making it a form of **dynamic dispatch** rather than a static reference to a parent class. Every `super()` call is a question asked at runtime: "Given this object's full class hierarchy, who comes next?"

---

### Why Hardcoding the Parent Breaks Everything

Developers who distrust `super()` sometimes call the parent class by name:

```python
class BrokenBroadcaster(EmailNotifier, SlackNotifier):
    """Calls each parent directly — produces duplicates."""

    def send(self, message: str) -> list[str]:
        email_log = EmailNotifier.send(self, message)
        slack_log = SlackNotifier.send(self, message)
        return email_log + slack_log + [f"broadcast: {message}"]
```

This looks reasonable — call each parent, merge the results. But `EmailNotifier.send()` still calls `super().send()` internally, and since `self` is a `BrokenBroadcaster`, the MRO still routes through `SlackNotifier`. Slack fires once inside the email branch. Then the explicit `SlackNotifier.send()` call fires Slack *again*:

```python
broken = BrokenBroadcaster()
print(broken.send("alert"))
# ['slack: alert', 'email: alert', 'slack: alert', 'broadcast: alert']
```

Slack delivered the notification twice. The explicit parent call broke the cooperative chain, creating a tangled mix of MRO-based and direct dispatch within the same call stack. In production, this pattern leads to duplicate database writes, double-sent messages, and subtle race conditions that only surface under specific inheritance arrangements.

Hardcoding also creates a maintenance trap. If you rename a base class, insert a new one in the hierarchy, or reorder the bases, every explicit call needs manual updating. `super()` adapts automatically because it reads the MRO at runtime — the dispatch table rewrites itself whenever the class hierarchy changes.

---

### Writing Methods That Cooperate Across the Chain

For `super()` chains to work correctly, every class in the hierarchy must follow the same calling convention. Three rules keep things predictable.

**Every non-root override must call super().** If one class in the chain drops the `super()` call, every class after it in the MRO goes silent. This is the most common source of bugs in cooperative inheritance — a single missing `super()` severs the entire chain downstream.

**Signatures must stay compatible.** You cannot predict which class `super()` will dispatch to at runtime, so every method in the chain needs to accept the same arguments. For regular methods, this is usually straightforward. For `__init__`, the cleanest pattern uses keyword-only arguments with `**kwargs` forwarding:

```python
class DatabaseConfig:
    """Extracts database settings from kwargs."""

    def __init__(self, *, db_host: str = "localhost", db_port: int = 5432, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.db_host = db_host
        self.db_port = db_port


class CacheConfig:
    """Extracts cache settings from kwargs."""

    def __init__(self, *, cache_ttl: int = 300, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.cache_ttl = cache_ttl


class AppSettings(DatabaseConfig, CacheConfig):
    """Combines database and cache configuration."""

    def __init__(self, *, app_name: str = "service", **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.app_name = app_name


config = AppSettings(db_host="db.prod.internal", cache_ttl=600, app_name="api")
print(f"{config.app_name} → {config.db_host}:{config.db_port}, ttl={config.cache_ttl}")
# api → db.prod.internal:5432, ttl=600
```

Each class consumes the keyword arguments it owns and forwards the rest via `**kwargs`. By the time `super().__init__()` reaches `object.__init__()`, the kwargs dictionary is empty and no `TypeError` is raised. If a caller passes a misspelled argument, it survives the entire chain and `object.__init__()` raises a `TypeError` — surfacing the mistake immediately rather than swallowing it.

**Root classes anchor the chain.** The base class at the top of the hierarchy should *not* call `super()` for the cooperative method unless it intentionally extends `object`'s default behavior. In the notification example, `Notifier.send()` returns an empty list without calling `super().send()`, giving the recursion a clean termination point. Without this anchor, the chain would eventually call `object.send()` and raise an `AttributeError`.

---

### Conclusion

`super()` is not `parent()`. It delegates to the next class in the instance's MRO — a sequence that Python computes once via C3 linearization at class creation time but resolves dynamically at every call site. The same `super()` expression in the same method body can route to entirely different classes depending on which concrete type instantiated the object.

Three principles keep cooperative inheritance reliable: every override calls `super()`, every method in the chain accepts a compatible signature, and root classes terminate the chain cleanly. Follow these rules, and `super()` transforms from a source of confusion into a precise orchestration mechanism — one where each class contributes its behavior exactly once, in a deterministic order, without needing to know which other classes share the hierarchy.
