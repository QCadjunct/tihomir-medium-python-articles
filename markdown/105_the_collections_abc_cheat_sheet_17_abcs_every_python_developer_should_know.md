# The collections.abc Cheat Sheet: 17 ABCs Every Python Developer Should Know

#### A guided tour of Python's abstract container hierarchy — and how choosing the right ABC shapes better function signatures, type hints, and isinstance checks

**By Tihomir Manushev**

*Feb 21, 2026 · 7 min read*

---

You write a function that accepts a list of user IDs. A colleague calls it with a tuple. It crashes. Another colleague passes a generator. It crashes differently. You change the type hint to `Sequence`, and suddenly both work — but now someone passes a dictionary, and your function iterates over its keys instead of raising an error.

The problem is not your code. The problem is that "a collection of items" means different things depending on which operations you need. Do you need indexing? Iteration? Mutation? Membership testing? Python's `collections.abc` module defines **17 abstract base classes** that formalize exactly these distinctions. Knowing which ABC to reach for — `Iterable` vs `Sequence` vs `MutableSequence`, `Mapping` vs `MutableMapping` — transforms vague type hints into precise contracts and turns brittle `isinstance(x, list)` checks into flexible ones.

This is not a dry reference table. This is a tour of the hierarchy, organized around the questions you actually face when designing function signatures.

---

### The Three Foundations: Iterable, Container, Sized

Every collection in Python is built on three primitives. Each one corresponds to a single dunder method:

```python
from collections.abc import Iterable, Container, Sized


class SensorLog:
    """A minimal collection that supports iteration, membership, and length."""

    def __init__(self, readings: list[float]) -> None:
        self._readings = readings

    def __iter__(self):
        return iter(self._readings)

    def __contains__(self, value: object) -> bool:
        return value in self._readings

    def __len__(self) -> int:
        return len(self._readings)
```

```python
log = SensorLog([23.1, 19.8, 22.4])
print(isinstance(log, Iterable))   # True — has __iter__
print(isinstance(log, Container))  # True — has __contains__
print(isinstance(log, Sized))      # True — has __len__
```

**`Iterable`** requires `__iter__()`. If your function only needs to loop over items, this is the most permissive type hint — it accepts lists, tuples, sets, generators, dictionaries, strings, and any custom class with `__iter__`.

**`Container`** requires `__contains__()`. It formalizes the `in` operator. Use it when your function tests membership but does not iterate.

**`Sized`** requires `__len__()`. It formalizes `len()`. Use it when your function needs to know how many items exist without consuming them.

These three ABCs are the atoms. Python 3.6 introduced **`Collection`**, which combines all three into a single base class. If your function needs iteration *and* membership testing *and* length, annotate with `Collection` instead of listing all three.

---

### Sequence vs Mapping vs Set: The Three Pillars

Once you move beyond the foundations, the hierarchy splits into three branches based on *how* you access items.

**`Sequence`** is for ordered collections accessed by integer index. It requires `__getitem__()` and `__len__()`, and it provides concrete mixin methods for free: `__contains__()`, `__iter__()`, `__reversed__()`, `index()`, and `count()`. Lists, tuples, strings, and ranges are all sequences.

**`Mapping`** is for key-value collections accessed by arbitrary keys. It requires `__getitem__()`, `__iter__()`, and `__len__()`, and provides `keys()`, `values()`, `items()`, `get()`, `__contains__()`, and `__eq__()`. Dictionaries are the canonical mapping.

**`Set`** is for unordered collections of unique elements. It provides the full suite of set operations — union, intersection, difference, symmetric difference — as concrete methods.

Here is how the choice affects your function signatures:

```python
from collections.abc import Sequence, Mapping


def compute_average(readings: Sequence[float]) -> float:
    """Accepts lists, tuples, or any indexed collection — but not dicts or sets."""
    total = sum(readings)
    return total / len(readings)


def lookup_thresholds(config: Mapping[str, float]) -> list[str]:
    """Accepts dicts, OrderedDicts, or any key-value container — but not lists."""
    return [key for key, value in config.items() if value > 100.0]
```

```python
print(compute_average([23.1, 19.8, 22.4]))          # 21.77 — list works
print(compute_average((23.1, 19.8, 22.4)))           # 21.77 — tuple works
print(lookup_thresholds({"cpu": 85.0, "mem": 120.0}))  # ['mem']
```

Using `Sequence` instead of `list` means your function accepts tuples, ranges, and any custom sequence. Using `Mapping` instead of `dict` means it accepts any key-value container. The ABC tells callers exactly which operations you need — no more, no less.

---

### Mutable vs Immutable: The Mutation Boundary

Each pillar has a mutable counterpart that adds write operations:

| Immutable ABC | Mutable ABC | Extra Abstract Methods |
|---|---|---|
| `Sequence` | `MutableSequence` | `__setitem__`, `__delitem__`, `insert` |
| `Mapping` | `MutableMapping` | `__setitem__`, `__delitem__` |
| `Set` | `MutableSet` | `add`, `discard` |

The mutable variants inherit all concrete methods from their immutable parent and add more. `MutableSequence` provides `append()`, `extend()`, `pop()`, `remove()`, `reverse()`, and `__iadd__()` — the `+=` operator. `MutableMapping` provides `pop()`, `popitem()`, `clear()`, `update()`, and `setdefault()`.

This distinction matters for function signatures. If your function only *reads* from a collection, annotate with the immutable ABC. If it *modifies* the collection, use the mutable variant:

```python
from collections.abc import MutableSequence


def remove_outliers(
    readings: MutableSequence[float],
    threshold: float,
) -> None:
    """Remove readings above threshold IN PLACE."""
    indices = [i for i, r in enumerate(readings) if r > threshold]
    for offset, idx in enumerate(indices):
        del readings[idx - offset]
```

```python
data: list[float] = [23.1, 19.8, 999.9, 22.4, 888.8]
remove_outliers(data, threshold=100.0)
print(data)  # [23.1, 19.8, 22.4]
```

Annotating with `MutableSequence` instead of `list` communicates two things: the function *will* modify the collection, and any mutable sequence — not just a `list` — is acceptable.

---

### The Overlooked ABCs: Iterator, Reversible, and the Views

Beyond the three pillars, several ABCs cover specialized patterns.

**`Iterator`** extends `Iterable` by adding `__next__()`. An iterator is a one-shot, stateful object that can only move forward. Generators are iterators. If your function consumes a stream of items exactly once, `Iterator` is the right hint.

**`Reversible`** requires `__reversed__()`. Sequences are reversible by default, but you can also make custom iterables reversible without supporting full indexing.

**`MappingView`**, **`KeysView`**, **`ItemsView`**, and **`ValuesView`** formalize the objects returned by `dict.keys()`, `dict.items()`, and `dict.values()`. These are rarely used in type hints, but understanding them explains why dictionary views support set operations:

```python
from collections.abc import KeysView

menu_a = {"pasta": 12.0, "salad": 8.0, "soup": 6.0}
menu_b = {"salad": 9.0, "steak": 22.0, "soup": 7.0}

common = menu_a.keys() & menu_b.keys()
print(common)  # {'salad', 'soup'}
print(isinstance(menu_a.keys(), KeysView))  # True
```

`KeysView` and `ItemsView` inherit from `Set`, which is why `&` (intersection) and `|` (union) work on dictionary keys and items.

---

### Two ABCs That Lie: Hashable and Callable

**`Hashable`** and **`Callable`** stand apart from the collection hierarchy. They check for the existence of `__hash__` and `__call__`, respectively. But both can produce misleading `isinstance` results.

An `isinstance(obj, Hashable)` check returning `True` does not guarantee you can actually hash the object. A tuple is hashable — unless it contains a mutable element:

```python
from collections.abc import Hashable

t = (1, 2, [3, 4])
print(isinstance(t, Hashable))  # True — the tuple class has __hash__
hash(t)                          # TypeError: unhashable type: 'list'
```

The `isinstance` check examines the *class*, not the *instance*. The `tuple` class defines `__hash__`, so the check passes. But this specific tuple contains a list, which makes it unhashable at runtime. The only reliable test is calling `hash()` directly and catching `TypeError`.

Similarly, for `Callable`, the built-in `callable()` function is more reliable than `isinstance(obj, Callable)` because it accounts for edge cases in CPython's internal callable detection.

**Rule of thumb:** for `Hashable`, call `hash()`. For `Callable`, call `callable()`. Use the ABCs in type hints, but use the built-in functions for runtime checks.

---

### Choosing the Right ABC: A Decision Guide

When designing a function signature, start with the narrowest question: *what operations does this function actually perform on the argument?*

If you only **loop** over items: `Iterable`. This is the most permissive — it accepts generators, which cannot be indexed or measured.

If you **loop and need length**: `Sized` won't give you iteration, and `Iterable` won't give you length. Use `Collection`, which combines both with membership testing.

If you **index by position**: `Sequence`. This guarantees `[0]`, slicing, and `in` operator support.

If you **modify in place**: `MutableSequence`, `MutableMapping`, or `MutableSet` — depending on the access pattern.

If you **look up by key**: `Mapping` for read-only access, `MutableMapping` for read-write.

The pattern is consistent: use the **immutable** ABC unless your function mutates, and use the **most general** ABC that covers the operations you need. A function that only iterates should not demand a `Sequence` — that rejects generators for no reason. A function that indexes by position should not accept a bare `Iterable` — that accepts generators that cannot be indexed.

---

### Conclusion

The 17 ABCs in `collections.abc` are not academic abstractions. They are the vocabulary for describing what your functions need from their arguments. Using `Mapping` instead of `dict` in a type hint says "I need key-value access but I don't care about the concrete type." Using `MutableSequence` instead of `list` says "I will modify this collection in place, and any ordered mutable container will do."

The hierarchy is built on a simple principle: each ABC adds one or two operations to its parent, and each mutable variant adds write methods to its immutable counterpart. Learn the three foundations (`Iterable`, `Container`, `Sized`), the three pillars (`Sequence`, `Mapping`, `Set`), and their mutable counterparts — and you have the mental model for the entire tree. Everything else is a specialization or a view.

Choose the most general ABC that covers your needs, and your functions will accept the widest range of inputs without sacrificing type safety.
