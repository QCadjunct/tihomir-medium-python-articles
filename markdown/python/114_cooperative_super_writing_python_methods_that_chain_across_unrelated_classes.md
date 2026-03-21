# Cooperative super(): Writing Python Methods That Chain Across Unrelated Classes

#### Not every method in a class needs to call super() — and the ones that don't reshape the entire activation sequence

**By Tihomir Manushev**

*Mar 06, 2026 · 7 min read*

---

You have a diamond inheritance hierarchy. You call a method on an instance, and `super()` chains the call through every class in the Method Resolution Order. You call a different method on the same instance, and the chain stops halfway. Same object, same MRO, different methods — yet completely different sets of classes execute.

This happens because cooperation is not a property of a class. It is a property of each *method*. A class can be fully cooperative for one method — calling `super()` and passing control down the MRO — while being completely non-cooperative for another, handling the call locally and returning without forwarding. The activation sequence, the set of classes that actually execute for a given method call, depends on which methods in the chain call `super()` and which do not.

Understanding activation sequences is what separates developers who use multiple inheritance deliberately from those who treat it as a black box. Without this understanding, you cannot debug why a method that "should" run in every class only runs in some, or why adding a new parent class changes behavior for methods you never touched. This article builds a concrete hierarchy where two methods produce different activation sequences, then shows how classes with no common ancestor can join the same `super()` chain.

---

### A Diamond with Two Behaviors

Consider a health check system for a distributed application. Every service exposes two methods: `check()` reports current status, and `recover()` attempts to fix problems. The base class anchors both chains:

```python
class Service:
    """Base service with health monitoring."""

    def check(self) -> list[str]:
        """Return health status messages."""
        return ["Service: baseline OK"]

    def recover(self) -> list[str]:
        """Attempt recovery and return status."""
        return ["Service: no recovery needed"]
```

Each method follows a pattern: call `super()` to collect status from downstream services, prepend your own message, and return the combined list. This builds a status report by walking the MRO in order, with each class contributing its own perspective.

Two specialized services extend this base. `DatabaseService` cooperates fully — both `check()` and `recover()` call `super()` to let downstream services participate:

```python
class DatabaseService(Service):
    """Monitors the database connection pool."""

    def check(self) -> list[str]:
        status = super().check()
        status.insert(0, "DatabaseService: connection pool active")
        return status

    def recover(self) -> list[str]:
        status = super().recover()
        status.insert(0, "DatabaseService: reconnected to primary")
        return status
```

`CacheService` cooperates for `check()` but *not* for `recover()`. When the cache fails, it flushes and restarts locally — there is no reason to propagate recovery further:

```python
class CacheService(Service):
    """Monitors the in-memory cache layer."""

    def check(self) -> list[str]:
        status = super().check()
        status.insert(0, "CacheService: 94% hit rate")
        return status

    def recover(self) -> list[str]:
        # Non-cooperative: handles recovery locally
        return ["CacheService: flushed and restarted"]
```

The application combines both:

```python
class AppService(DatabaseService, CacheService):
    """Application-level health monitoring."""
    pass
```

The MRO is `AppService → DatabaseService → CacheService → Service → object`. Both methods traverse this same MRO — but they activate different subsets of it.

---

### Two Methods, Two Activation Sequences

Call `check()` on the application service:

```python
app = AppService()
print(app.check())
# ['DatabaseService: connection pool active',
#  'CacheService: 94% hit rate',
#  'Service: baseline OK']
```

Three messages — one from each class in the hierarchy below `AppService`. The **activation sequence** for `check()` is the full chain: `DatabaseService.check` → `CacheService.check` → `Service.check`. Each method calls `super().check()`, receives the downstream results, prepends its own status, and returns the combined list upward. The chain reaches `Service` at the bottom because every class along the way cooperates by calling `super()`.

Now call `recover()`:

```python
print(app.recover())
# ['DatabaseService: reconnected to primary',
#  'CacheService: flushed and restarted']
```

Two messages. `Service.recover()` never runs. The activation sequence is shorter: `DatabaseService.recover` → `CacheService.recover` → stops. `DatabaseService.recover()` calls `super().recover()`, which routes to `CacheService.recover()` per the MRO. But `CacheService.recover()` returns its own list without calling `super()`. The chain terminates there. `Service.recover()` sits in the MRO but never receives the call.

This is the critical insight: **cooperation is per-method, not per-class.** `CacheService` is cooperative for `check()` and non-cooperative for `recover()`. The MRO does not change between calls — the same tuple governs both. What changes is which methods in that tuple actually forward the call. The activation sequence is the MRO filtered by cooperation.

Whether a method should cooperate is a design decision, not a rule violation. `CacheService.recover()` has a legitimate reason to stop the chain: cache recovery is self-contained, and propagating it to the base `Service` class would produce a meaningless "no recovery needed" message. The key is being *intentional* about it. A non-cooperative method is a deliberate termination point; a missing `super()` call due to oversight is a bug. The code looks identical — only the developer's intent differs.

This has a practical consequence for debugging. When a method call does not reach a class you expect it to reach, the problem is not necessarily in that class. It is in some class *earlier* in the MRO that chose not to forward the call. Trace the activation sequence from the beginning of the MRO, checking each class's implementation of the method, and you will find the one that broke the chain.

---

### When an Outsider Joins the Chain

`super()` does not care about class relationships. It follows the MRO, and the MRO includes every class in the hierarchy regardless of ancestry. A class with no connection to `Service` can participate in the `check()` chain simply by appearing in the MRO:

```python
class MetricsExporter:
    """Standalone metrics — no relationship to Service."""

    def check(self) -> list[str]:
        status = super().check()
        status.insert(0, "MetricsExporter: 42 data points exported")
        return status
```

`MetricsExporter` does not inherit from `Service`. It has no `recover()` method. Yet it defines `check()` and calls `super().check()`. Combine it with the existing hierarchy:

```python
class MonitoredApp(MetricsExporter, DatabaseService, CacheService):
    """Full monitoring with metrics export."""
    pass


print([cls.__name__ for cls in MonitoredApp.__mro__])
# ['MonitoredApp', 'MetricsExporter', 'DatabaseService',
#  'CacheService', 'Service', 'object']

print(MonitoredApp().check())
# ['MetricsExporter: 42 data points exported',
#  'DatabaseService: connection pool active',
#  'CacheService: 94% hit rate',
#  'Service: baseline OK']
```

Four messages. `MetricsExporter.check()` calls `super().check()`, and the MRO routes that call to `DatabaseService.check()` — a class that `MetricsExporter` knows nothing about and shares no ancestor with (other than `object`). The chain continues through `CacheService` and `Service` as before. The outsider slots into the pipeline seamlessly, as if it had always been part of the `Service` family.

This works because `super()` is resolved against the MRO of the *instance's* class, not the class where `super()` appears in source code. When `super()` runs inside `MetricsExporter.check()` and the instance is a `MonitoredApp`, Python looks up `MetricsExporter` in `MonitoredApp.__mro__`, finds the next class (`DatabaseService`), and dispatches there. The method's definition site is irrelevant — only the runtime MRO matters.

What about `recover()`? `MetricsExporter` does not define it, so `MonitoredApp().recover()` skips straight to `DatabaseService.recover()` in the MRO lookup. The activation sequence for `recover()` is unchanged — `MetricsExporter` is invisible for methods it does not implement. This is another dimension of per-method cooperation: a class can participate in the chain for `check()` while being entirely absent from the chain for `recover()`, not because it chose not to cooperate, but because it has nothing to contribute.

This pattern is common in practice. Logging, metrics collection, and monitoring are cross-cutting concerns that touch specific methods without needing to participate in every operation the hierarchy supports. An outsider class that defines only the methods it cares about naturally joins some chains and stays out of others.

---

### Conditional Cooperation: The Subtle Chain Breaker

The most deceptive form of non-cooperation is a method that calls `super()` only sometimes. It cooperates under certain conditions and silently breaks the chain under others:

```python
class CircuitBreakerService(Service):
    """Stops recovery propagation when failure count is too high."""

    def __init__(self, *, threshold: int = 3, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.failure_count = 0

    def recover(self) -> list[str]:
        self.failure_count += 1
        if self.failure_count > self.threshold:
            return ["CircuitBreakerService: circuit OPEN — recovery halted"]
        status = super().recover()
        status.insert(0, "CircuitBreakerService: attempting recovery")
        return status
```

The first three calls to `recover()` cooperate normally — `super().recover()` fires, and every downstream class participates. The fourth call silently severs the chain. Every class downstream — `DatabaseService`, `CacheService`, `Service` — stops receiving the call without any error, exception, or warning. The transition from cooperative to non-cooperative happens at runtime based on internal state, making it invisible during code review.

This is sometimes exactly the right design. Circuit breakers exist precisely to stop cascading recovery attempts when a system is overwhelmed. But the pattern demands clear documentation and ideally logging at the point where the chain breaks. Anyone reading the `super().recover()` call on the cooperative branch will assume the method always cooperates. The silent, stateful switch to non-cooperation is a maintenance hazard if the intent is not explicitly communicated through docstrings or log output.

As a general principle: if a method's cooperation depends on runtime conditions, log or signal when the chain is intentionally severed. Silent non-cooperation is the hardest bug to trace in a multiple inheritance hierarchy.

---

### Conclusion

Cooperation in Python's multiple inheritance is not binary — it is per-method. The same class can cooperate for `check()` and refuse to cooperate for `recover()`, producing different activation sequences for different method calls on the same instance. The MRO provides the full ordered list of classes. Which of those classes actually execute depends on which methods in the chain call `super()` and which return without forwarding.

Classes can join a `super()` chain without sharing a common ancestor. The MRO treats every class the same regardless of lineage, and `super()` dispatches based on the runtime MRO of the instance, not the compile-time hierarchy of the class. If the method exists and calls `super()`, the class participates. If it does not define the method, it is silently skipped.

Design your cooperative methods intentionally. When a method does not call `super()`, it is a termination point that reshapes the activation sequence for every instance downstream. Make that choice explicit — in the docstring, in a comment, or in the method name itself — so the next developer understands not just what the method does, but what it deliberately prevents.
