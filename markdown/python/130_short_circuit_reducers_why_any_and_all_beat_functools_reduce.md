# Short-Circuit Reducers: Why any() and all() Beat functools.reduce

#### The built-ins that quit the instant the answer is decided — and stay finite on streams that never end

**By Tihomir Manushev**

*Jul 17, 2026 · 7 min read*

---

You need to answer a yes/no question about a collection: does *any* transaction look fraudulent? are *all* the sensor readings within range? The mechanical instinct is to fold the whole thing — loop over every element, accumulate a boolean, return it at the end. `functools.reduce` will do exactly that, dutifully, for all ten million rows.

But the answer was often decided on row three. If the third transaction is fraudulent, checking the remaining 9,999,997 is wasted work — you already know "any" is `True`. This is **short-circuit evaluation**: stop the moment the outcome can't change. Python's `any()` and `all()` do it for free; `reduce` cannot do it at all. The gap between them is not a micro-optimization — on a large or infinite iterable it is the difference between microseconds and forever.

This article shows exactly when the outcome is decided, backed by real element counts and `timeit` numbers, the one feature that makes `any()` safe on streams that never end, and the cases where `reduce` remains the correct tool rather than a legacy relic.

---

### Short-Circuit: Stop the Moment You Know

`any()` returns `True` as soon as it sees one truthy element and stops pulling from the iterable. `all()` returns `False` at the first falsy one. Neither touches a single element beyond the one that settles the question. You can prove it by counting how many elements the predicate actually inspects:

```python
inspected = 0

def matches(n: int) -> bool:
    """A predicate that records every element it examines."""
    global inspected
    inspected += 1
    return n == 3

found = any(matches(n) for n in range(1, 1_000_000))
print("result:", found, "| inspected:", inspected)
# result: True | inspected: 3
```

Out of a million candidates, `any()` examined **three**. It found the match at `n == 3`, returned `True`, and never advanced the generator again. `all()` mirrors this from the other side — it keeps going while things are truthy and bails at the first failure:

```python
checked = 0

def under_five(n: int) -> bool:
    global checked
    checked += 1
    return n < 5

ok = all(under_five(n) for n in range(1, 1_000_000))
print("result:", ok, "| checked:", checked)
# result: False | checked: 5
```

Five elements checked, not a million: `1, 2, 3, 4` passed, `5` failed the `< 5` test, and `all()` stopped there. The mental model is precise — `any` hunts for one witness and quits when it finds one; `all` hunts for one counterexample and quits when it finds one.

---

### The Speed Difference When It Matters

`reduce` has no such escape. A boolean fold with `reduce` visits every element even when the accumulator is already `True` and nothing could change it. Timing the two against ten million elements, with a match sitting near the front, is stark:

```python
from functools import reduce
import timeit

def with_any() -> bool:
    return any(n == 3 for n in range(10_000_000))

def with_reduce() -> bool:
    return reduce(lambda acc, n: acc or n == 3, range(10_000_000), False)

print(f"any    : {min(timeit.repeat(with_any, number=1, repeat=5)) * 1e6:.1f} us")
print(f"reduce : {min(timeit.repeat(with_reduce, number=1, repeat=5)) * 1e3:.1f} ms")
# any    : 0.5 us
# reduce : 639.7 ms
```

That is 0.5 microseconds against 639.7 milliseconds — roughly a million-to-one, because `reduce` keeps evaluating `acc or n == 3` for all ten million elements after the answer is already `True`.

Now the honest caveat, because that headline number is a best case. Short-circuiting only helps when the deciding element comes early. If no element matches, `any()` has no excuse to stop and must scan the whole iterable — the same work `reduce` does:

```python
def any_absent() -> bool:
    return any(n < 0 for n in range(5_000_000))   # never true

print(f"{min(timeit.repeat(any_absent, number=1, repeat=5)) * 1e3:.1f} ms")
# 160.3 ms  (full scan, result False)
```

So the complexity is **O(k)**, where k is the position of the first decisive element — best case O(1), worst case O(n) when the answer lives at the end or nowhere. The point is not that `any()` is always fast; it is that `any()` *can* stop and `reduce` never can. When your data is ordered so hits tend to come early, or when you just need to know existence, that possibility is worth a lot.

---

### Safe on Infinite Streams

Here is the feature that turns a nice optimization into a categorical difference. Because `any()` and `all()` consume lazily and can stop, they terminate on iterables that have no end:

```python
from itertools import count

print(any(n > 100 for n in count()))
# True
```

`itertools.count()` yields `0, 1, 2, …` forever. `any()` pulls values until `n > 100` becomes true at 101, returns `True`, and stops. Feed that same infinite generator to `reduce`, or to `list()`, or to a sum, and the program hangs until it exhausts memory or your patience — they demand every element, and there is no last one. This is the composition that makes lazy pipelines powerful: a generator that produces values on demand, capped by a reducer that stops demanding the instant it has its answer. `any()` and `all()` are the natural terminators for an infinite or merely enormous stream.

---

### They Return a Bool, Not the Element

A trap that catches people: `any()` tells you *whether* something matched, not *what* matched. It always returns `True` or `False`, never the element:

```python
temps = [18, 21, 25, 19]

print(any(t > 24 for t in temps))
# True  -- not 25

print(next((t for t in temps if t > 24), None))
# 25    -- the element itself
```

If you actually want the first matching element, `any()` is the wrong tool — reach for `next()` over a generator expression, with a default so an empty result doesn't raise `StopIteration`. Use `any()`/`all()` for the yes/no question, `next()` for the give-me-the-item question. They short-circuit identically; they just return different things.

---

### Don't Wrap It in a List

Short-circuiting has a fragile prerequisite: the elements must arrive lazily. Feed `any()` or `all()` a **list comprehension** instead of a generator expression and you quietly destroy the whole benefit — the list is built in full *before* the reducer sees its first element:

```python
calls = 0

def hot(n: int) -> bool:
    global calls
    calls += 1
    return n == 3

any([hot(n) for n in range(1, 1000)])   # square brackets: builds the list first
print("predicate calls:", calls)
# predicate calls: 999
```

The square brackets forced all 999 predicate calls to run up front; `any()` then short-circuited over an already-complete list and saved nothing. Drop the brackets — `any(hot(n) for n in range(1, 1000))` — and the count falls to 3. The rule is the same one that separates a generator expression from a list comprehension: parentheses stream, brackets materialize. With a short-circuit reducer, materializing first is pure waste, and on an infinite source it's a hang.

---

### The Empty-Iterable Rule

What should `all()` return for an empty collection? The answer trips people until you see the logic: `all([])` is `True` and `any([])` is `False`.

```python
print("all([]) =", all([]))   # True
print("any([]) =", any([]))   # False
```

`all` asks "is there no counterexample?" — with zero elements there is none, so it's vacuously `True`. `any` asks "is there at least one witness?" — with zero elements there is none, so `False`. This is mathematically correct and occasionally a production bug: validate an *empty* batch of records with `all(is_valid(r) for r in batch)` and it passes, because there was nothing to fail. If an empty input should be rejected, test for it explicitly — the vacuous truth won't do it for you.

---

### When reduce Is Still the Right Tool

None of this makes `reduce` obsolete. `any()` and `all()` collapse an iterable to a boolean; `reduce` folds it into *any* accumulated value, and it is the right choice precisely when you genuinely need to touch every element. A running product is the classic case — there is no short-circuit for a factorial, because every factor matters:

```python
from functools import reduce
from operator import mul

print(reduce(mul, range(1, 11)))
# 3628800  (that is 10!)
```

`reduce(mul, range(1, 11))` multiplies `1 * 2 * … * 10`. You cannot stop early; skipping any element gives the wrong answer. That is the signature of a real fold, and where `reduce` (or a plain loop) belongs. One gotcha to respect: `reduce` on an empty iterable with no initial value raises, so always supply the initial value that doubles as your empty-case answer:

```python
try:
    reduce(mul, [])
except TypeError as error:
    print(error)
# reduce() of empty iterable with no initial value

print(reduce(mul, [], 1))
# 1
```

Passing the `initial` argument (`1` for a product, `0` for a sum) makes the fold total — it handles the empty case instead of crashing on it.

---

### Conclusion

`any()` and `all()` are reducers with a brake. They fold an iterable to a boolean and quit the instant the result is settled — three elements into a million, or 101 elements into an infinite stream — which makes them both faster in the common case and *safe* on iterables `reduce` would run off the end of. Reach for them whenever the question is existence ("does one match?") or universality ("do all pass?"), and pair them with generators so nothing downstream of the answer is ever computed.

Keep the three sharp edges in mind: they return a bool, not the matching element, so use `next()` when you want the item; an empty iterable makes `all()` vacuously true, which can wave bad input through; and `reduce` is not the enemy — it is the right tool the moment you truly need every element folded together. Match the reducer to the question, and you stop paying for work whose answer you already have.
