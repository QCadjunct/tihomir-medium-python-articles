# The Two-Argument iter(): Python's Sentinel-Driven Iteration Shortcut

#### The most underused form of a built-in, and when it beats every `while True` loop

**By Tihomir Manushev**

*Apr 11, 2026 · 7 min read*

---

Every Python developer has written this loop a hundred times:

```python
while True:
    chunk = source.read(4096)
    if not chunk:
        break
    process(chunk)
```

Read until empty. Poll until done. Pop until exhausted. The pattern is so universal that the fingers move on autopilot. But Python's `iter()` built-in has a second form — the two-argument form — that collapses the entire loop into a single iterator. It has been in the language since Python 1.4, and most developers have never used it.

The form is `iter(callable, sentinel)`. Pass any zero-argument callable and a stop value, and Python builds an iterator that calls the function repeatedly, yielding each result, until the function returns a value equal to the sentinel. At that point the iterator raises `StopIteration` and the loop ends — no `break`, no `if not chunk`, no boilerplate. Once you start spotting the pattern, half the read-and-check loops in your codebase look like missed opportunities.

---

### How Two-Argument iter() Works

The single-argument `iter(obj)` returns an iterator over an iterable. The two-argument `iter(callable, sentinel)` does something completely different: it turns a callable into an iterator. Each call to `next()` on the resulting iterator invokes the callable with no arguments and returns the result. The iterator stops the moment a result equals the sentinel — comparison is by `==`, not `is`.

That tiny mechanism solves a surprisingly broad class of problems. Anywhere a value is produced repeatedly until a stop condition is met, two-argument `iter()` collapses the loop into a one-liner. The result composes with all of Python's iterator machinery — `for` loops, comprehensions, `itertools` functions, generator pipelines — without any adapter code.

If it helps, the equivalent generator function is just three lines:

```python
def sentinel_iter(callable_, sentinel):
    while True:
        value = callable_()
        if value == sentinel:
            return
        yield value
```

Two restrictions matter in practice. First, the callable must take zero arguments. Functions that need parameters get adapted with `functools.partial` or wrapped in a `lambda`. Second, the sentinel comparison uses `==`, so any object whose equality is well-defined works — `None`, an empty string, an empty `bytes` object, or a unique marker created with `object()`.

---

### Pattern 1: Draining a Queue Until a Shutdown Signal

A worker thread consuming a `queue.SimpleQueue` typically polls until it receives a special value telling it to stop. The traditional version:

```python
import queue


SHUTDOWN = object()


def worker_traditional(jobs: queue.SimpleQueue) -> list[str]:
    """Consume jobs until the SHUTDOWN sentinel is received."""
    processed = []
    while True:
        job = jobs.get()
        if job is SHUTDOWN:
            break
        processed.append(job.upper())
    return processed
```

The same logic with two-argument `iter()`:

```python
import queue


SHUTDOWN = object()


def worker_iter(jobs: queue.SimpleQueue) -> list[str]:
    """Consume jobs until the SHUTDOWN sentinel is received."""
    return [job.upper() for job in iter(jobs.get, SHUTDOWN)]
```

The body of the loop disappears into a list comprehension. `iter(jobs.get, SHUTDOWN)` creates an iterator that calls `jobs.get()` over and over, yielding each job, until `jobs.get()` returns the `SHUTDOWN` object — at which point the iterator stops. The comprehension takes care of the rest.

```python
inbox: queue.SimpleQueue = queue.SimpleQueue()
for message in ["build", "test", "deploy"]:
    inbox.put(message)
inbox.put(SHUTDOWN)

print(worker_iter(inbox))  # ['BUILD', 'TEST', 'DEPLOY']
```

Note the choice of sentinel. `SHUTDOWN = object()` creates a unique instance whose only purpose is to be compared against. Two-argument `iter()` uses `==` for the comparison, but for a default `object()` instance, `==` falls back to `is` (identity), so the check is exact. A real "shutdown" string would risk a false stop if any job happened to carry that same value — the unique sentinel object guarantees no collision is possible.

---

### Pattern 2: Reading Fixed-Size File Blocks

The most-cited use of two-argument `iter()` in the standard library docs is reading binary files in fixed-size blocks. Here `functools.partial` does the heavy lifting, turning a multi-argument method into the zero-argument callable that `iter()` requires:

```python
from functools import partial
from pathlib import Path


def chunked_hash(path: Path, block_size: int = 4096) -> int:
    """Compute a folding hash over a file in fixed-size blocks."""
    digest = 0
    with path.open("rb") as stream:
        for block in iter(partial(stream.read, block_size), b""):
            for byte in block:
                digest = (digest * 31 + byte) & 0xFFFFFFFF
    return digest
```

`partial(stream.read, block_size)` produces a callable that, when invoked with no arguments, calls `stream.read(block_size)`. Two-argument `iter()` invokes it repeatedly, yielding each block. When `read()` returns an empty `bytes` object — the natural end-of-file signal — the iterator stops.

```python
sample_path = Path("sample.bin")
sample_path.write_bytes(b"alpha-beta-gamma-delta-epsilon-zeta")

print(chunked_hash(sample_path, block_size=8))  # 887712836
sample_path.unlink()
```

This pattern is the canonical alternative to a manual `while True: read; if not block: break` loop. It is shorter, harder to mess up, and reads as exactly what it does: iterate over blocks until empty. The same shape works for socket reads, pipe drains, and any other API that returns an empty result on exhaustion.

---

### Pattern 3: Polling Until a Terminal State

Two-argument `iter()` shines when the "next value" comes from an external system that needs to be polled. A deployment status that transitions through `pending` → `running` → `completed` (or `failed`) maps naturally onto the pattern:

```python
from typing import Iterator


def status_stream() -> Iterator[str]:
    """Simulate a deploy that transitions through statuses."""
    return iter(["pending", "running", "running", "completed"])


def watch_deploy() -> list[str]:
    """Collect every transient status, stop at the terminal state."""
    transitions = status_stream()
    history = []
    for status in iter(lambda: next(transitions), "completed"):
        history.append(status)
    return history


print(watch_deploy())  # ['pending', 'running', 'running']
```

The lambda wraps the polling source in a zero-argument callable. Each call returns the next status. Iteration stops when the status equals `"completed"` — the terminal state — without that final value being yielded. If you want the terminal status included in the history, append it after the loop or restructure the polling.

For real systems, replace the lambda with a function that hits an HTTP endpoint, queries a database, or checks a Kubernetes job. The shape of the calling code stays exactly the same, regardless of what is being polled.

---

### Composing With the Rest of the Iterator Ecosystem

The result of `iter(callable, sentinel)` is a `callable_iterator` — a built-in iterator type, distinct from generators but indistinguishable in behavior from outside. It plays well with everything iterator-shaped, which is where the real leverage compounds:

```python
import itertools
from functools import partial


counter = itertools.count(1)
first_five = list(itertools.islice(iter(partial(next, counter), 999), 5))
print(first_five)  # [1, 2, 3, 4, 5]
```

Take slices with `itertools.islice`. Filter with a generator expression. Zip it with another stream. The output is just an iterator — the rules for working with it are the same rules every Python developer already knows.

---

### Gotchas Worth Knowing

The callable runs once per `next()` call, with zero arguments. If the function has side effects — network requests, file reads, queue consumption — each iteration triggers another side effect. That is usually the point, but it can surprise developers who expect the value to be cached.

The sentinel comparison uses `==`, not `is`. For mutable values or objects with custom `__eq__`, the behavior depends on what you defined. For unique sentinels, prefer a freshly constructed `object()` — its `==` falls back to identity, eliminating any chance of a false stop on a value that happens to compare equal.

Finally, two-argument `iter()` cannot terminate on an exception. If the callable raises, the iterator propagates the exception unchanged. If your data source signals end-of-stream by raising — like `queue.Queue.get(timeout=...)` raising `Empty` — wrap the call in a function that catches the exception and returns the sentinel instead. Two-argument `iter()` only knows how to stop on a value, not on a failure.

---

### Conclusion

The two-argument `iter()` is one of the cleanest functional shortcuts hidden in Python's built-ins. Anywhere a `while True` loop is reading-and-checking against a stop condition, the pattern likely collapses into a single iterator. Pair it with `functools.partial` to adapt non-zero-argument callables, with `itertools` to compose downstream, and with `object()` sentinels when no natural stop value exists. Once the shape clicks, you start spotting it in code you already wrote — and shortening every one of those loops.
