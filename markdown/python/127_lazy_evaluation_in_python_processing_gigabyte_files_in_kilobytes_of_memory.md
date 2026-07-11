# Lazy Evaluation in Python: Processing Gigabyte Files in Kilobytes of Memory

#### How swapping eager calls for lazy generator pipelines turns memory-hungry scripts into streaming ones

**By Tihomir Manushev**

*Jul 11, 2026 · 8 min read*

---

A script parses an access log, tallies the bytes served on successful requests, and prints a number. It sails through your 10 MB sample on a laptop. Then it meets the real thing — a 4 GB log rotated off a busy edge server — and dies with `MemoryError` before printing anything.

The logic never changed. The input did. The problem is that the script computes everything *eagerly*: it reads the whole file into a string, builds a list of every match, builds another list of every parsed value, and only then reduces. At peak, several full-size copies of the data coexist in RAM. A machine with 8 GB free chokes on a 4 GB file because the eager version needs far more than 4 GB to process it.

Lazy evaluation flips this. Instead of materializing each intermediate collection, you chain generators that produce one item at a time and forget it immediately. Below, we take a script that peaks at 548 MB and rewrite it to peak at 23 KB — same answer, four orders of magnitude less memory — with `tracemalloc` receipts.

---

### The Eager Trap

Here is the memory-hungry version. It extracts the HTTP status and byte count from each log line, keeps the successful (`2xx`) responses, and sums the bytes.

```python
import re

LOG_LINE = re.compile(r"\S+ \S+ (GET|POST|PUT|DELETE) \S+ (\d{3}) (\d+)")


def bytes_served_eager(path: str) -> int:
    """Sum bytes for 2xx responses by materializing every step."""
    with open(path) as handle:
        blob = handle.read()                       # whole file in memory
    hits = re.findall(LOG_LINE, blob)              # list of every match
    sizes = [int(size) for _method, status, size in hits
             if status.startswith("2")]            # list of every value
    return sum(sizes)
```

Three collections balloon here. `handle.read()` pulls the entire file into one string. `re.findall` walks that string and returns a **list of every match** — for a log with millions of lines, that is millions of tuples. The comprehension then builds a **third list** of integers. Only `sum` finally collapses it to a scalar, long after the damage is done.

The regex itself is fine. The waste is structural: every stage insists on finishing completely before the next begins, so every stage's full output lives in memory at once.

---

### finditer: The Same Search, One Match at a Time

The single most important swap is `re.findall` → `re.finditer`. They answer the same question and differ only in *when* the work happens. `findall` returns a fully built list. `finditer` returns a lazy iterator that scans the string and yields one `Match` object per `next()` call, holding nothing but its current position.

To see the gap in isolation, count how many four-plus-letter words appear in a large block of text — 3.5 million matches:

```python
import re
import tracemalloc

WORD = re.compile(r"[A-Za-z]{4,}")
text = "lorem ipsum dolor sit amet consectetur adipiscing elit " * 500_000


def count_findall() -> int:
    """Build a list of all matches, then measure its length."""
    return len(re.findall(WORD, text))


def count_finditer() -> int:
    """Consume matches one at a time; keep only a running counter."""
    total = 0
    for _ in re.finditer(WORD, text):
        total += 1
    return total


def peak_kb(func) -> float:
    tracemalloc.start()
    func()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024


print(f"findall  peak: {peak_kb(count_findall) / 1024:.1f} MB")   # 187.3 MB
print(f"finditer peak: {peak_kb(count_finditer):.1f} KB")         # 1.8 KB
```

Both count exactly 3,500,000 words. `findall` peaks at **187.3 MB** because it holds every matched substring at once. `finditer` peaks at **1.8 KB** because it never holds more than the match it is currently looking at. Same regex, same result, a 100,000× difference in footprint.

---

### Files Are Already Lazy

`finditer` still needed the whole `text` string in memory. For a real file we want to avoid `handle.read()` too — and Python hands us that for free. A file object is itself a **lazy iterator over lines**. Writing `for line in handle:` reads one line, hands it to the loop body, and only fetches the next when asked. The file is never fully resident.

That gives us a generator that emits parsed matches without ever holding the file or a match list:

```python
from collections.abc import Iterator


def parse_lines(path: str) -> Iterator[re.Match[str]]:
    """Yield one regex match per line, streaming the file lazily."""
    with open(path) as handle:
        for line in handle:                 # one line resident at a time
            match = LOG_LINE.match(line)
            if match:
                yield match
```

`parse_lines` is a generator function — calling it runs no code and reads nothing. It returns a generator object that springs to life only when something iterates it, and even then it advances one line per step. This is the foundation the whole pipeline stands on.

---

### Composing a Streaming Pipeline

Now stack lazy stages. Each generator expression pulls from the one before it, so a single item flows all the way through before the next item is ever read. Nothing accumulates.

```python
def bytes_served_lazy(path: str) -> int:
    """Sum bytes for 2xx responses without materializing any stage."""
    matches = parse_lines(path)
    successful = (m for m in matches if m.group(2).startswith("2"))
    sizes = (int(m.group(3)) for m in successful)
    return sum(sizes)
```

Read it top to bottom, but understand it as a pull chain from the bottom. `sum` asks `sizes` for a value; `sizes` asks `successful`; `successful` asks `matches`; `matches` reads exactly one line from disk. That value is summed and discarded, then `sum` asks for the next. At no instant does more than a single line — and a single integer — exist in the pipeline.

The rewrite is almost cosmetic: square brackets became parentheses, and `re.findall` on a blob became a per-line `match`. Semantically the two functions are identical. Operationally they live in different universes.

---

### Measuring It: 548 MB vs 23 KB

Talk is cheap; `tracemalloc` is not — but first we need a file to point it at. There is no bundled `access.log`, so generate one: two million lines of plausible traffic, weighted toward `2xx` responses, landing at about 112.6 MB on disk.

```python
METHODS = ["GET", "POST", "PUT", "DELETE"]
STATUSES = ["200", "200", "200", "301", "404", "500", "206"]


def write_sample_log(path: str, rows: int = 2_000_000) -> None:
    """Generate a synthetic access log so the benchmark is reproducible."""
    with open(path, "w") as handle:
        for row in range(rows):
            method = METHODS[row % len(METHODS)]
            status = STATUSES[row % len(STATUSES)]
            size = (row * 37) % 90_000 + 128
            handle.write(
                f"2026-07-11T08:{row % 60:02d}:{row % 60:02d}Z "
                f"10.0.{row % 256}.{row % 254} {method} /api/thing {status} {size}\n"
            )
```

Each field is deterministic, so the file is identical on every machine and the numbers below reproduce exactly. Now point both versions at it and record the peak:

```python
import tracemalloc


def measure(func, path: str) -> tuple[int, float]:
    """Return the function's result and its peak memory in bytes."""
    tracemalloc.start()
    result = func(path)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, peak


write_sample_log("access.log")            # ~112.6 MB, generated once
total_eager, peak_eager = measure(bytes_served_eager, "access.log")
total_lazy, peak_lazy = measure(bytes_served_lazy, "access.log")

print(f"eager: {total_eager}  peak={peak_eager / 1024 / 1024:.1f} MB")
print(f"lazy:  {total_lazy}  peak={peak_lazy / 1024:.1f} KB")
# eager: 51563402951  peak=547.8 MB
# lazy:  51563402951  peak=22.9 KB
```

Identical totals. The eager version peaks at **547.8 MB** — nearly five times the file size, because the raw string, the match list, and the integer list all coexist. The lazy version peaks at **22.9 KB**, flat regardless of input size. Feed the lazy pipeline a 4 GB file and the peak barely moves; feed the eager one 4 GB and it needs roughly 20 GB it does not have.

That flatness is the real prize. Lazy memory cost is **O(1)** in the size of the input, not **O(n)**. The file can outgrow RAM by any factor and the streaming version does not notice.

---

### The Gotcha: A Generator Is a One-Shot Deal

Laziness has one sharp edge that eager lists do not: a generator is **exhausted after a single pass**. A list you can iterate all day; a generator, once walked to the end, yields nothing forever after.

```python
matches = parse_lines("access.log")
successful = (m for m in matches if m.group(2).startswith("2"))
sizes = (int(m.group(3)) for m in successful)
print(sum(sizes))   # 51563402951 — drains the generator
print(sum(sizes))   # 0 — nothing left to yield
print(max(sizes))   # ValueError: max() iterable argument is empty
```

The second `sum` sees an empty stream, not because the file changed but because the generator was already consumed. If you need two aggregates — say a total *and* a maximum — you cannot iterate twice. Either compute both in a single pass with an explicit loop, or, if the data genuinely fits, materialize once with `list(...)` and accept the memory cost deliberately.

The subtler trap is a stray pair of square brackets. Write `sum([int(m.group(3)) for m in matches])` and you have silently re-armed the eager bomb: the list comprehension builds the whole list *before* `sum` runs, resurrecting the 548 MB peak inside a call that looks lazy. In a reducing context, drop the brackets — `sum(int(...) for m in matches)` — and let the values stream.

---

### When Eager Still Wins

Lazy is the right default for large or unbounded input, but it is not free, and it is not always the answer. A generator adds a small per-item cost — the interpreter suspends and resumes a frame on every `next()` — so for data that comfortably fits in memory, a plain list is often marginally faster and far easier to debug, since you can print it, slice it, and inspect it in a debugger.

Reach for an eager list deliberately when you need any of the things a one-pass stream cannot give you. Random access (`data[42]`), a length (`len(data)`), multiple passes over the same values, or slicing (`data[10:20]`) all require the collection to actually exist. A generator has no length and no index; asking for either is a category error. The rule of thumb: stream when the data is large or its size is unknown, materialize when it is small *and* you need to look at it more than once. The mistake is only materializing by accident — paying O(n) memory for a stream you were going to consume exactly once.

---

### Conclusion

Eager and lazy code can be line-for-line twins and still differ by four orders of magnitude in memory. The pattern is small and mechanical: reach for `re.finditer` over `re.findall`, iterate files line by line instead of `read()`, and chain generator expressions so each item flows through and vanishes rather than piling into intermediate lists.

The payoff is that your program's memory stops tracking its input. A pipeline that peaks at 23 KB on 112 MB peaks at roughly 23 KB on 112 GB — the file size simply drops out of the equation. Write the streaming version first and you never have to rewrite it when the sample file grows into the real one. Just watch for the one-pass rule, and never let a square bracket sneak an eager list back into a lazy chain.
