# The Sequence Protocol Illusion: How __getitem__ Alone Unlocks Iteration, Containment, and More

#### Python's interpreter bends over backwards to make your objects behave like sequences — and all it asks for is a single dunder method

**By Tihomir Manushev**

*Feb 7, 2026 · 7 min read*

---

You just built a custom container class. You want your users to loop over it with `for`, check membership with `in`, pull items by index, and maybe even slice it. Quick — how many special methods do you need to implement?

If you guessed three or four — `__iter__`, `__contains__`, `__getitem__`, maybe `__len__` — you are overengineering it. The real answer is one. A single `__getitem__` method is enough to unlock iteration, membership testing, indexing, and negative indexing, all without writing a single extra line of code.

This is not a quirk or an accident. It is a deliberate design choice baked into CPython's C source code — a set of fallback mechanisms that the interpreter activates when it encounters an object with `__getitem__` but no `__iter__`. Understanding how these fallbacks work reveals one of Python's most powerful and least understood features: the **dynamic sequence protocol**.

---

### The Sequence Protocol: Python's Invisible Contract

Python has two distinct ways to define what an object can do: **Abstract Base Classes** (ABCs) and **dynamic protocols**.

ABCs are explicit. You inherit from `collections.abc.Sequence`, you implement the required abstract methods, and the type system knows you are a sequence. Static type checkers like Mypy can verify compliance at analysis time. Everything is declared, formal, and visible.

Dynamic protocols are the opposite. They are implicit contracts defined by convention. No inheritance is required. No registration is needed. If your object implements the right methods with the right signatures, Python's interpreter will treat it as if it belongs to the club — no questions asked.

The **sequence protocol** is the most forgiving of these dynamic contracts. At its core, the protocol expects an object to support integer-based indexing via `__getitem__`. That is the minimum viable interface. Implement just that, and the interpreter fills in the blanks.

This is fundamentally different from how languages like Java or C# handle interfaces. In those languages, if your class doesn't explicitly declare that it implements `Iterable`, it doesn't matter whether it has the right methods — the compiler will reject it. Python takes the opposite stance: behavior trumps declarations. If you walk like a sequence and quack like a sequence, Python will iterate over you like a sequence.

The reason this works is that the core iteration and containment logic in CPython doesn't start by demanding `__iter__` or `__contains__`. Instead, it follows a fallback chain — checking for the ideal method first, and gracefully degrading to `__getitem__` when the ideal method is absent.

---

### One Method, Four Behaviors

Let's see this in action. We will build a `Palette` class that represents a collection of hex color codes. The class will implement only `__getitem__` — nothing else.

```python
class Palette:
    """A collection of hex color codes, accessed by index."""

    def __init__(self, *hex_codes: str) -> None:
        self._colors = hex_codes

    def __getitem__(self, index: int) -> str:
        return self._colors[index]
```

That is the entire class. No `__iter__`, no `__contains__`, no `__len__`. Now watch what Python lets us do with it:

```python
sunset = Palette("#FF6B35", "#F7C59F", "#EFEFD0", "#004E89", "#1A659E")

# 1. Direct indexing
print(sunset[0])       # '#FF6B35'
print(sunset[-1])      # '#1A659E'

# 2. Iteration with a for loop
for color in sunset:
    print(color)
# Prints all five colors, one per line

# 3. Membership testing with 'in'
print("#004E89" in sunset)   # True
print("#FFFFFF" in sunset)   # False

# 4. Unpacking
first, second, *rest = sunset
print(first)    # '#FF6B35'
print(rest)     # ['#EFEFD0', '#004E89', '#1A659E']
```

Four distinct behaviors. One dunder method. Negative indexing works because we delegate to a tuple, which already handles negative indices. But iteration, membership testing, and unpacking are entirely provided by the interpreter's fallback logic — our class has zero explicit support for any of them.

---

### Under the Hood: The Fallback Machinery

When you write `for color in sunset`, Python calls the built-in `iter()` function on the `sunset` object. Here is the fallback chain that `iter()` follows:

**Step 1:** Check if the object has an `__iter__` method. If yes, call it and return the resulting iterator.

**Step 2:** If `__iter__` is missing, check if the object has `__getitem__`. If yes, CPython constructs an internal iterator object that calls `__getitem__` with indices `0`, `1`, `2`, `3`, ... in sequence. When `__getitem__` raises an `IndexError`, the iterator treats it as the end of the sequence and stops.

**Step 3:** If neither method exists, raise a `TypeError`.

We can prove this fallback is happening by tracing the calls:

```python
class TrackedPalette:
    """A palette that logs every __getitem__ call."""

    def __init__(self, *hex_codes: str) -> None:
        self._colors = hex_codes

    def __getitem__(self, index: int) -> str:
        print(f"  __getitem__({index}) called")
        return self._colors[index]


traced = TrackedPalette("#E63946", "#457B9D", "#1D3557")

print("Iterating:")
for color in traced:
    pass
```

The output reveals exactly what the interpreter is doing:

```
Iterating:
  __getitem__(0) called
  __getitem__(1) called
  __getitem__(2) called
  __getitem__(3) called    # <-- raises IndexError internally, stops iteration
```

Notice that fourth call: `__getitem__(3)` triggers an `IndexError` because there are only three colors. The interpreter catches that error silently and terminates the loop. The `IndexError` is the stop signal — the `__getitem__`-based equivalent of `StopIteration`.

The `in` operator follows a similar pattern. When Python evaluates `"#457B9D" in traced`, it first checks for a `__contains__` method. Finding none, it falls back to iterating through the object via `__getitem__`, comparing each element. The time complexity is O(n) — a linear scan — which is exactly what you'd expect from a sequence without a hash-based lookup structure.

---

### When __getitem__ Isn't Enough

The sequence protocol fallback is generous, but it has clear limits. Several operations require additional dunder methods that the interpreter will not synthesize for you.

**`len()` requires `__len__`:**

```python
sunset = Palette("#FF6B35", "#F7C59F", "#EFEFD0")

try:
    print(len(sunset))
except TypeError as err:
    print(err)  # object of type 'Palette' has no len()
```

**`reversed()` requires `__reversed__` or `__len__` + `__getitem__`:**

```python
try:
    for color in reversed(sunset):
        print(color)
except TypeError as err:
    print(err)  # argument to reversed() must be a sequence
```

Interestingly, `reversed()` will work if you add *just* `__len__` — it uses `__len__` to determine the final index and then counts backwards through `__getitem__`. You don't need a dedicated `__reversed__` method.

**`random.shuffle()` requires `__setitem__`:**

```python
import random

try:
    random.shuffle(sunset)
except TypeError as err:
    print(err)  # 'Palette' object does not support item assignment
```

This makes sense: `shuffle` works by swapping elements in place, which requires writing back to the container. A read-only `__getitem__` is insufficient. This is the boundary between the **immutable** sequence protocol (read-only, `__getitem__` only) and the **mutable** sequence protocol (which adds `__setitem__`, `__delitem__`, and `insert`).

---

### The Gotcha: Not Every __getitem__ Is a Sequence

Here is a trap that catches even experienced developers. Dictionaries implement `__getitem__`, but Python does not treat them as sequences:

```python
config = {"host": "localhost", "port": 8080, "debug": True}

# This works — dict has __getitem__
print(config["host"])  # 'localhost'

# But this does NOT iterate via __getitem__ with integer indices
for key in config:
    print(key)  # iterates via __iter__, not __getitem__
```

Why the difference? Because `dict` provides its own `__iter__` method, which yields keys. The `__getitem__` fallback never activates — it is a last resort, triggered only when `__iter__` is absent.

But there is a deeper reason too. At the C level, CPython's `PySequence_Check` function — the internal test for "does this object behave like a sequence?" — explicitly excludes `dict` subclasses. Even if a `dict` subclass somehow lost its `__iter__`, CPython would still refuse to treat it as a sequence via `__getitem__`. The rationale: mapping-style `__getitem__` expects arbitrary keys, not sequential integers, and treating a mapping as a sequence would produce nonsensical results.

This distinction matters when you are writing functions that accept generic containers. If you need to determine at runtime whether an object supports sequential integer indexing, checking for `__getitem__` alone is not enough. The safer check is `isinstance(obj, collections.abc.Sequence)`.

---

### Conclusion

The sequence protocol is a window into Python's design philosophy: make the common case easy and the complex case possible. With a single `__getitem__` method, Python gives your objects iteration, membership testing, unpacking, and negative indexing — all powered by fallback machinery written in C.

But the protocol has boundaries. `len()`, `reversed()`, and mutation operations require their own dunder methods. And not every `__getitem__` is a sequence — mappings are explicitly excluded from the fallback chain.

Understanding these mechanics lets you make informed decisions: when a minimal `__getitem__` is sufficient, and when you need the full weight of `collections.abc.Sequence`. The interpreter is generous — but only if you know where its generosity ends.
