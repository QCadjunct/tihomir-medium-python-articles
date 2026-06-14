# What yield Actually Does: Frame Suspension, send(), and When Classes Still Win

#### Generators aren't shorter iterators — they're a different machine, and yield is the lever

**By Tihomir Manushev**

*Apr 11, 2026 · 7 min read*

---

Most Python tutorials introduce generators by saying they replace iterator classes with less boilerplate. That framing is true on the surface and misses what is actually going on. A `yield` statement is not syntactic sugar over `__next__`. It hooks into the same machinery that drives every Python function call — the frame object — and uses it for something function calls usually don't do: pause, hand control back, and resume later with all state intact.

Once you see the frame underneath, generators stop looking like "shorter iterators" and start looking like a different abstraction entirely. They give you a two-way communication channel for free. They return values that flow through `StopIteration`. They cooperate with the runtime in ways iterator classes can't match — and they hit limits in places iterator classes still handle cleanly.

This article digs into what `yield` actually does, why that makes generators more than a typing shortcut, and where iterator classes still win.

---

### The Visible Difference

Start with the surface comparison. Here is a hand-written iterator class that walks through paginated API results, yielding each item:

```python
class PaginatedReader:
    """Walk through pages of items, yielding one item at a time."""
    def __init__(self, pages: list[list[str]]) -> None:
        self._pages = pages
        self._page_idx = 0
        self._item_idx = 0

    def __iter__(self) -> "PaginatedReader":
        return self

    def __next__(self) -> str:
        while self._page_idx < len(self._pages):
            page = self._pages[self._page_idx]
            if self._item_idx < len(page):
                item = page[self._item_idx]
                self._item_idx += 1
                return item
            self._page_idx += 1
            self._item_idx = 0
        raise StopIteration
```

Now the generator function version of the same logic:

```python
from typing import Iterator


def paginated_reader(pages: list[list[str]]) -> Iterator[str]:
    """Walk through pages of items, yielding one item at a time."""
    for page in pages:
        for item in page:
            yield item
```

Both produce identical output:

```python
pages = [["alpha", "beta"], ["gamma"], ["delta", "epsilon"]]
print(list(PaginatedReader(pages)))   # ['alpha', 'beta', 'gamma', 'delta', 'epsilon']
print(list(paginated_reader(pages)))  # ['alpha', 'beta', 'gamma', 'delta', 'epsilon']
```

The class spells out the state machine: two cursors, conditional advancement, manual `StopIteration`. The generator reads as nested loops — correct by construction. The brevity is real. But brevity isn't the reason to choose the generator. To see the real reason, look at what Python does the moment you call `paginated_reader(pages)`.

---

### What yield Actually Does

Every Python function call goes through the same lifecycle: Python creates a **frame object** holding the function's local variables, an instruction pointer, and a reference to the caller's frame. The body runs to completion. The frame is discarded on return.

A generator function — any function whose body contains `yield` — bends this lifecycle in two ways:

1. Calling the function does *not* run the body. Python creates the frame, wraps it in a generator object, and returns the generator object immediately. The body has not executed.
2. Each call to `next(gen)` runs the body until the next `yield`, then suspends. The frame is *not* discarded. Locals, the instruction pointer, the loop counters — everything — stay alive inside the generator object, ready to resume.

Iterator classes track state in instance attributes you have to declare, increment, and reset by hand. Generator functions delegate state to the frame, which Python maintains for you. Whatever local variables exist when `yield` runs — loop indices, accumulators, partial parses, even nested loop positions — all of them are preserved automatically and restored on the next `next()`.

Prove it with a generator that prints at multiple points:

```python
from typing import Iterator


def chatty() -> Iterator[int]:
    print("body started")
    yield 1
    print("between yields")
    yield 2
    print("body ended")


stream = chatty()
print("constructed")
print(next(stream))
print(next(stream))
try:
    next(stream)
except StopIteration:
    print("stopped")
# constructed
# body started
# 1
# between yields
# 2
# body ended
# stopped
```

The line `stream = chatty()` ran the function call, but nothing inside `chatty` executed. `"body started"` only appears after `next(stream)` resumes the frame. That lazy-startup behavior is the frame-suspension model made visible.

---

### The Two-Way Channel: send() and throw()

Here is where generators leave iterator classes behind entirely. `yield` is not a statement — it is an **expression**. The value of that expression is whatever the caller passes via `send()`. An iterator class has no equivalent; `__next__` only produces.

Build a streaming average. The generator yields the current rolling mean, and the caller pushes the next sample in through `send()`:

```python
from typing import Generator


def averager() -> Generator[float | None, float, None]:
    """Yield the rolling mean; consume new samples via send()."""
    total = 0.0
    count = 0
    average: float | None = None
    while True:
        value = yield average
        total += value
        count += 1
        average = total / count


avg = averager()
next(avg)                 # prime: run to first yield
print(avg.send(10))       # 10.0
print(avg.send(20))       # 15.0
print(avg.send(30))       # 20.0
```

`next(avg)` "primes" the generator — it runs the body until the first `yield average`, where it suspends. The first yielded value is `None` (no samples yet). Each `avg.send(value)` then resumes the frame: the suspended `yield` expression evaluates to `value`, the body updates `total`, `count`, and `average`, then yields the new average and suspends again. The generator behaves like a small object with a single-method interface (`send`) and persistent state — but no class definition.

`throw()` is the matching mechanism for exceptions. It injects an exception into the paused frame as if the suspended `yield` had raised it:

```python
from typing import Generator


def lenient_consumer() -> Generator[None, str, None]:
    """Accept items via send(); recover from injected exceptions."""
    while True:
        try:
            item = yield
            print(f"got {item}")
        except ValueError as err:
            print(f"recovered from {err}")


sink = lenient_consumer()
next(sink)                            # prime
sink.send("a")                        # got a
sink.throw(ValueError("bad input"))   # recovered from bad input
sink.send("b")                        # got b
```

`sink.throw(ValueError(...))` resumes the generator at the suspended `yield`, but instead of returning a value the `yield` raises the supplied exception. The `try`/`except` catches it, the loop continues, and the next `yield` waits for more input. To reproduce this with an iterator class, you would need to expose a method, build a state machine, and manually route exceptions — code that the generator gets for free from the frame.

---

### Return Values Flow Through StopIteration

A `return value` statement inside a generator does something specific: it stores `value` in the `StopIteration` exception that terminates iteration. The value rides out on the exception:

```python
from typing import Iterator


def yield_until_zero(numbers: list[int]) -> Iterator[int]:
    """Yield each non-zero number; return the running total on zero."""
    total = 0
    for n in numbers:
        if n == 0:
            return total
        yield n
        total += n


gen = yield_until_zero([3, 1, 4, 0, 2])
yielded: list[int] = []
try:
    while True:
        yielded.append(next(gen))
except StopIteration as stop:
    print(yielded)      # [3, 1, 4]
    print(stop.value)   # 8
```

The consumer collected `[3, 1, 4]` as the yielded values, then captured `8` as `stop.value` when the generator's `return total` fired. This is the mechanism that powers `yield from`: when delegation ends, the inner generator's return value is propagated to the outer one via the captured `StopIteration.value`. Iterator classes have no equivalent — `__next__` is constrained to yielding values or raising `StopIteration` with no payload.

---

### When Iterator Classes Still Win

Generators are not always the right tool. Reach for an iterator class when one of these holds:

**You need other special methods.** Generators expose `__next__`, `__iter__`, `send`, `throw`, and `close`. They do *not* expose `__len__`, `__getitem__`, `__reversed__`, or `__contains__`. A consumer that wants to call `len(my_iter)`, index into it, reverse it, or check membership with `in` needs a class.

**You need to reset.** Generators are strictly single-pass. There is no rewind. An iterator class can offer `reset()` or replayable internal state — useful for test fixtures, retry loops, or replayable streams.

**You need to inspect state mid-iteration.** A class can expose `current_page`, `progress()`, or `remaining()` for monitoring. A generator's frame is opaque to outside code; the `frame.f_locals` attribute exists but is intended for debuggers, not application logic.

**The state machine is genuinely complex.** State machines with many branches, peek-ahead semantics, or multiple entry points often read more clearly as a class with named methods than as deeply nested `yield`s wrapped in tangled control flow.

Outside these cases, the generator is the right choice. Most production iterators don't need any of the above, which is why the generator function has displaced the iterator class as the idiomatic Python pattern.

---

### Conclusion

`yield` is not a typing convenience. It hooks into CPython's frame object — the same machinery that backs every function call — and uses it to suspend execution between values. That gives you automatic state preservation, a two-way `send()`/`throw()` communication channel, and return values that flow through `StopIteration` to enable `yield from`. The iterator class still has its niche when you need other special methods, resettable state, or external introspection. Everywhere else, the generator is shorter, faster to write, and built on machinery you cannot replicate by hand.
