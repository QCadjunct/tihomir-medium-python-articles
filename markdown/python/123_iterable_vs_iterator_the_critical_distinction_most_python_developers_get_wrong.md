# Iterable vs Iterator: The Critical Distinction Most Python Developers Get Wrong

#### Why making a class its own iterator silently breaks every loop after the first one

**By Tihomir Manushev**

*Apr 11, 2026 · 7 min read*

---

You write a class that holds events. You give it `__iter__` and `__next__`. The first `for` loop over an instance works perfectly. The second `for` loop runs zero times and prints nothing — no error, no warning, just silence. A test passes, but the feature breaks in production.

This is one of the quietest bugs in hand-rolled Python iteration code, and it comes from conflating two concepts that look similar but play completely different roles. An **iterable** is a source of values. An **iterator** is a single-use cursor over that source. Fuse them into one class and you get exactly one pass through your data, forever.

Understanding the iterable-iterator split — and why Python insists on it — changes how you design every class that needs to be looped over.

---

### How Python's for Loop Actually Works

Before fixing anything, look at what `for` really does. The statement `for value in container:` expands roughly into this:

```python
iterator = iter(container)
while True:
    try:
        value = next(iterator)
    except StopIteration:
        break
    # loop body runs here
```

Three steps: call `iter()` to get an iterator, call `next()` repeatedly, stop when `StopIteration` fires. Every comprehension, unpacking assignment, and `for` loop in your codebase follows this pattern.

The critical detail is step one. `iter(container)` is expected to return a *fresh iterator* every single call. If `container` is walked three times — once by a `list()` call, once by a `sum()`, once by a user `for` loop — Python expects three independent cursors, each starting at the beginning.

The `iter()` built-in looks for `__iter__` on the object. If found, it calls that method and returns whatever comes back. The returned object must implement `__next__` to be useful. When `__next__` eventually raises `StopIteration`, the loop terminates cleanly.

An **iterable** is any object with a working `__iter__`. An **iterator** is any object with a working `__next__` *and* an `__iter__` that returns itself. That last detail — an iterator's `__iter__` returns `self` — is what lets you pass an iterator directly to `for`. It's also exactly the trap that breaks multi-pass code.

---

### The Antipattern: A Class as Its Own Iterator

Here is the buggy design — the one that catches thousands of developers every year:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    """A timestamped log event."""
    timestamp: str
    message: str


class EventLog:
    """Holds events and iterates over them. (Broken version.)"""
    def __init__(self, events: list[Event]) -> None:
        self._events = events
        self._cursor = 0

    def __iter__(self) -> "EventLog":
        return self

    def __next__(self) -> Event:
        if self._cursor >= len(self._events):
            raise StopIteration
        event = self._events[self._cursor]
        self._cursor += 1
        return event
```

The class looks perfectly reasonable: it stores events, tracks a cursor, yields each event via `__next__`, and signals exhaustion with `StopIteration`. Run a `for` loop and it behaves exactly as expected:

```python
log = EventLog([
    Event("09:00", "service started"),
    Event("09:01", "accepted connection"),
    Event("09:02", "request processed"),
])

for event in log:
    print(event.message)
# service started
# accepted connection
# request processed
```

Now run the same loop again immediately:

```python
for event in log:
    print(event.message)
# (nothing prints)
```

Silent failure. The loop terminated instantly because `self._cursor` is still sitting past the end of `self._events`. The iterable and the iterator are the same object, and that object has already been walked to completion. There is no way to rewind it — and worse, there is no exception to tell you something went wrong.

The problem compounds with multiple consumers. Two components that both want to scan the log — say, a dashboard and an alert system — cannot share one `EventLog` instance. The first to iterate wins; the second finds an empty river. A single `list(log)` call before a `for` loop does the same thing: `list()` exhausts the cursor, and the subsequent loop runs nothing.

---

### The Classic Fix: A Separate Iterator Class

The Gang of Four Iterator pattern has an answer: separate the container from the cursor. `EventLog.__iter__` stops returning `self` and instead constructs a new iterator object on every call:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    """A timestamped log event."""
    timestamp: str
    message: str


class EventLogIterator:
    """A single-pass cursor over an EventLog's events."""
    def __init__(self, events: list[Event]) -> None:
        self._events = events
        self._cursor = 0

    def __iter__(self) -> "EventLogIterator":
        return self

    def __next__(self) -> Event:
        if self._cursor >= len(self._events):
            raise StopIteration
        event = self._events[self._cursor]
        self._cursor += 1
        return event


class EventLog:
    """Holds events. Each iteration starts fresh."""
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def __iter__(self) -> EventLogIterator:
        return EventLogIterator(self._events)
```

The `EventLog` itself no longer carries a cursor — it stores only data. Every call to `iter(log)` returns a *new* `EventLogIterator` with its own `_cursor` starting at zero. Two consumers get two independent cursors:

```python
log = EventLog([
    Event("09:00", "service started"),
    Event("09:01", "accepted connection"),
])

dashboard_pass = [e.message for e in log]
alert_pass = [e.message for e in log]

print(dashboard_pass)  # ['service started', 'accepted connection']
print(alert_pass)      # ['service started', 'accepted connection']
```

Both passes succeed. Each `for` loop and each comprehension builds its own iterator, walks it to exhaustion, and discards it. This is the literal, textbook Iterator design pattern — and it works. It is also more code than any Pythonic solution needs.

---

### The Pythonic Fix: Generator Function as __iter__

A generator function returns a fresh generator object every time it is called. That property — baked into the language — is exactly what `__iter__` needs. Collapse the entire `EventLogIterator` class into a generator:

```python
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    """A timestamped log event."""
    timestamp: str
    message: str


class EventLog:
    """Holds events. Each iteration starts fresh."""
    def __init__(self, events: list[Event]) -> None:
        self._events = events

    def __iter__(self) -> Iterator[Event]:
        for event in self._events:
            yield event
```

The `__iter__` method is now a generator function — it contains `yield`. Calling it (which Python does on your behalf via `iter(log)`) returns a new generator object. Each generator tracks its own suspended frame state, so every consumer gets an independent cursor. No separate class, no manual `_cursor` bookkeeping, no `StopIteration` to raise explicitly — the generator handles all of it.

```python
log = EventLog([
    Event("09:00", "service started"),
    Event("09:01", "accepted connection"),
])

for event in log:
    print(event.message)
# service started
# accepted connection

for event in log:
    print(event.message)
# service started
# accepted connection
```

Both loops work. The code is shorter, has fewer moving parts, and reads as a straightforward description of intent. For containers that simply yield their stored items, `yield from self._events` is even shorter — but the explicit loop makes the iteration protocol visible to a reader encountering the pattern for the first time.

---

### Using ABCs to Catch the Bug at Runtime

`collections.abc` exposes the two concepts as separate ABCs, and each supports structural `isinstance` checks. You can ask any object which shape it actually has:

```python
from collections.abc import Iterable, Iterator

fixed_log = EventLog([Event("09:00", "service started")])

print(isinstance(fixed_log, Iterable))  # True
print(isinstance(fixed_log, Iterator))  # False
```

`EventLog` is an iterable (it produces iterators) but not an iterator (it has no `__next__`). That is the correct shape for a container.

Run the same checks against the broken original — the class that returned `self` from `__iter__` — and both return `True`. That dual identity is the bug crystallized into a type check. A class that is both iterable and iterator is almost always confusing the two roles. Lock these assertions into your test suite and you catch the antipattern before it ships.

---

### Conclusion

An iterable is a data source; an iterator is a single-use cursor over that source. Python's `for` loop calls `iter()` on the iterable to get a fresh cursor every time. If your class returns `self` from `__iter__` — making it its own iterator — only the first pass works, and every subsequent pass runs zero times without any error.

The fix is always the same: `__iter__` must return a *new* object. Write a separate iterator class if you need it, but in almost every case a generator function inside `__iter__` is shorter, cleaner, and correct by construction. When in doubt, let `isinstance` against `Iterable` and `Iterator` tell you whether you built what you intended.
