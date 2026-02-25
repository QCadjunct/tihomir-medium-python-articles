# The Lies Python's isinstance Tells: When Hashable and Iterable Checks Betray You

#### Why isinstance(obj, Hashable) returning True does not mean you can hash the object — and why False from Iterable does not mean you cannot iterate

**By Tihomir Manushev**

*Feb 24, 2026 · 7 min read*

---

You have a function that inserts objects into a set. Before inserting, you guard with `isinstance(obj, Hashable)` to avoid a `TypeError`. The check returns `True`, so you insert. The program crashes anyway — `TypeError: unhashable type: 'list'`. The object was a tuple containing a list. The *class* defines `__hash__`, but this specific *instance* cannot be hashed.

In another part of your codebase, a function guards against non-iterable arguments with `isinstance(obj, Iterable)`. The check returns `False` for a custom object, so you raise a helpful error. But the object *is* iterable — it implements `__getitem__` with integer indices, and a `for` loop would work perfectly. Your guard rejected a valid input.

These are not edge cases. They are fundamental limitations of how `isinstance` interacts with Python's abstract base classes. The checks examine the *class*, not the *instance*. They look for method *existence*, not method *behavior*. Understanding where `isinstance` lies — and what to use instead — prevents false confidence in your validation logic.

---

### The Hashable False Positive

The `Hashable` ABC from `collections.abc` checks whether a class defines `__hash__`. If the method exists on the class or any of its parents, `isinstance` returns `True`. But having the method does not guarantee that calling it will succeed.

The classic trap is a tuple containing mutable elements:

```python
from collections.abc import Hashable

clean_tuple = (1, 2, 3)
dirty_tuple = (1, 2, [3, 4])

print(isinstance(clean_tuple, Hashable))  # True
print(isinstance(dirty_tuple, Hashable))  # True
```

Both return `True` because the `tuple` class defines `__hash__`. Python's `isinstance` check examines the class, not the contents of this particular instance. But try to actually hash the second tuple:

```python
hash(clean_tuple)  # 529344067295497451 (some integer)
hash(dirty_tuple)  # TypeError: unhashable type: 'list'
```

The `tuple.__hash__` implementation recursively hashes each element. When it reaches the list at index 2, it calls `list.__hash__` — which is set to `None`, signaling that lists are unhashable. The `TypeError` fires deep inside the hash computation, long after `isinstance` gave its blessing.

This is not limited to tuples. Any class that inherits `__hash__` from a parent but contains unhashable internal state will produce the same false positive. A frozen dataclass holding a list field, a named tuple wrapping a dictionary — the pattern recurs wherever immutable containers hold mutable contents.

The **ground truth** for hashability is calling `hash()` directly:

```python
def is_truly_hashable(obj: object) -> bool:
    """Test whether an object can actually be hashed."""
    try:
        hash(obj)
        return True
    except TypeError:
        return False


print(is_truly_hashable((1, 2, 3)))       # True
print(is_truly_hashable((1, 2, [3, 4])))  # False
```

This function tests the *instance*, not the *class*. It catches the exact cases that `isinstance` misses. If you are guarding a set insertion or a dictionary key assignment, `hash()` with a try/except is the only reliable check.

---

### The Iterable False Negative

The `Iterable` ABC checks for `__iter__`. If the class defines it, the check returns `True`. If not, it returns `False`. Simple — and wrong.

Python's iteration machinery has a **fallback path**. When `__iter__` is not defined, the interpreter looks for `__getitem__` and tries to call it with integer indices starting from 0. If that works, the object is iterable. This fallback is how Python supported iteration before the iterator protocol existed, and it still works today:

```python
from collections.abc import Iterable


class OldStylePalette:
    """A class that supports iteration through __getitem__ only."""

    def __init__(self) -> None:
        self._colors = ["crimson", "teal", "amber", "slate"]

    def __getitem__(self, index: int) -> str:
        return self._colors[index]
```

```python
palette = OldStylePalette()

print(isinstance(palette, Iterable))  # False — no __iter__

for color in palette:
    print(color)
# crimson
# teal
# amber
# slate
```

The `isinstance` check says `False`. The `for` loop says otherwise. Python's `for` statement does not use `isinstance` to decide whether to iterate — it calls `iter()` on the object, which tries `__iter__` first and falls back to `__getitem__`. The ABC check only knows about the first path.

The **ground truth** for iterability is calling `iter()`:

```python
def is_truly_iterable(obj: object) -> bool:
    """Test whether Python can actually iterate over an object."""
    try:
        iter(obj)
        return True
    except TypeError:
        return False


print(is_truly_iterable(OldStylePalette()))  # True
print(is_truly_iterable(42))                 # False
```

The `iter()` function exercises the same machinery that `for` loops use, including the `__getitem__` fallback. If `iter()` succeeds, iteration will work. If it raises `TypeError`, nothing will make the object iterable.

---

### The Asymmetry: When You Can Trust isinstance

The lies `isinstance` tells are not symmetric. There is a reliable direction for each ABC:

**Hashable:** a `False` result is trustworthy. If `isinstance(obj, Hashable)` returns `False`, the class has explicitly set `__hash__ = None` or does not define it. You *cannot* hash the object. But a `True` result is unreliable — the instance might still be unhashable due to its contents.

**Iterable:** a `True` result is trustworthy. If `isinstance(obj, Iterable)` returns `True`, the class defines `__iter__`, and iteration will work (assuming the method is implemented correctly). But a `False` result is unreliable — the object might still be iterable via `__getitem__`.

In table form:

| ABC | `True` result | `False` result |
|---|---|---|
| `Hashable` | Unreliable (false positive possible) | Reliable |
| `Iterable` | Reliable | Unreliable (false negative possible) |

This asymmetry means you can use `isinstance` as a quick filter in one direction but must fall back to the ground-truth function in the other. If you need to *reject* unhashable objects, use `hash()`. If you need to *accept* all iterables, use `iter()`.

---

### Beyond Hashable and Iterable: The Pattern Repeats

The same class-vs-instance gap appears with other ABCs, though less dramatically.

**`Callable`** checks for `__call__`. The built-in `callable()` function is more reliable because it accounts for internal CPython dispatch mechanisms that `isinstance(obj, Callable)` does not. Always prefer `callable(obj)` over the ABC check:

```python
from collections.abc import Callable

print(isinstance(len, Callable))  # True
print(callable(len))              # True — same result, but more reliable for edge cases
```

**`Sized`** checks for `__len__` via `__subclasshook__`. Any class with a `__len__` method is recognized as a virtual subclass of `Sized` — even without inheriting from it and even if `__len__` returns something nonsensical:

```python
from collections.abc import Sized


class Misleading:
    def __len__(self) -> int:
        raise RuntimeError("Length is not supported")


print(isinstance(Misleading(), Sized))  # True
len(Misleading())                        # RuntimeError: Length is not supported
```

The `isinstance` check sees that `__len__` exists. It does not call it. It does not verify the return type. It does not check whether the method actually works. This is, again, by design — runtime verification of method behavior would carry unacceptable performance costs for every `isinstance` call in every hot path.

---

### The Practical Defense: Ground-Truth Functions

The pattern is consistent across all ABCs: `isinstance` checks method *presence* on the *class*. It does not check method *behavior* on the *instance*. When the gap matters, use the corresponding built-in function as the ground truth:

| Need to verify | Don't rely on | Use instead |
|---|---|---|
| Hashability | `isinstance(obj, Hashable)` | `hash(obj)` in try/except |
| Iterability | `isinstance(obj, Iterable)` | `iter(obj)` in try/except |
| Callability | `isinstance(obj, Callable)` | `callable(obj)` |
| Length support | `isinstance(obj, Sized)` | `len(obj)` in try/except |

This does not mean `isinstance` with ABCs is useless. It is fast, it reads clearly in type guards, and it is correct in the *majority* of cases. The built-in types — `list`, `dict`, `str`, `tuple`, `set` — all behave consistently with their ABC memberships. The lies emerge at the edges: composite objects with mixed mutability, legacy classes with `__getitem__` but no `__iter__`, and custom classes with broken dunder methods.

Use `isinstance` for the common case. Use the ground-truth functions when correctness matters more than speed — especially at system boundaries where you cannot control what inputs arrive.

---

### Conclusion

`isinstance` with ABCs answers a narrower question than most developers assume. It asks "does this class *declare* support for this protocol?" — not "can this instance *actually perform* the operation?" The distinction is invisible for well-behaved built-in types but becomes a trap for composite objects, legacy classes, and adversarial inputs.

The fix is simple: when the check must be airtight, skip `isinstance` and call the operation directly — `hash()`, `iter()`, `callable()`, `len()` — inside a try/except. These functions exercise the same machinery that Python uses internally, including fallback paths and instance-level behavior that no class-level check can capture.

Trust `isinstance` for what it is: a fast, structural check on the class. Reach for the ground-truth function when you need a behavioral check on the instance.
