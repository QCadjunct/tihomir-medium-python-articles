# Rich Comparison Operators: Why Python's == and < Follow Different Rules

#### The asymmetric fallback rules that make equality forgiving and ordering strict

**By Tihomir Manushev**

*Apr 08, 2026 · 7 min read*

---

Implement `__eq__` on a custom class, and `!=` works immediately — without writing a single extra line. Try `<` on the same class, and Python throws a `TypeError`. Both are comparison operators. Both rely on special methods. Yet they follow completely different fallback rules when those methods can't produce an answer.

This asymmetry trips up even experienced developers. Equality operators (`==`, `!=`) silently fall back to comparing object identities. Ordering operators (`<`, `>`, `<=`, `>=`) refuse to guess and raise `TypeError` instead. The distinction is deliberate, rooted in a simple truth: every pair of objects either *is* or *isn't* the same object, but not every pair of objects has a meaningful order.

Understanding how Python dispatches these six operators — and where the dispatch rules diverge — prevents subtle bugs in every class that needs custom comparisons.

---

### The Dispatch Protocol

When Python evaluates `a == b`, it doesn't simply call `a.__eq__(b)` and trust the result. It follows a multi-step protocol:

1. Call `a.__eq__(b)`. If the result is anything other than `NotImplemented`, return it.
2. If `a.__eq__` returns `NotImplemented` (or doesn't exist), call `b.__eq__(a)` — the *reverse* call with swapped arguments.
3. If that also returns `NotImplemented`, fall back to comparing object identities: return `id(a) == id(b)`.

The ordering operators follow the same first two steps, but step 3 changes everything. For `a < b`:

1. Call `a.__lt__(b)`. If the result is not `NotImplemented`, return it.
2. If `a.__lt__` returns `NotImplemented`, call `b.__gt__(a)` — note the *complementary* method, not `__lt__` again.
3. If that also returns `NotImplemented`, raise `TypeError`.

Two differences stand out. First, equality uses the *same* method on both sides (`__eq__` on `a`, then `__eq__` on `b`), while ordering swaps to the complement (`__lt__` on `a`, then `__gt__` on `b`). Second, equality has a safe landing; ordering does not.

Here is the full mapping of forward-to-reverse calls:

| Expression | Forward call | Reverse call | Final fallback |
|-----------|-------------|-------------|---------------|
| `a == b` | `a.__eq__(b)` | `b.__eq__(a)` | `id(a) == id(b)` |
| `a != b` | `a.__ne__(b)` | `b.__ne__(a)` | `id(a) != id(b)` |
| `a < b` | `a.__lt__(b)` | `b.__gt__(a)` | `TypeError` |
| `a > b` | `a.__gt__(b)` | `b.__lt__(a)` | `TypeError` |
| `a <= b` | `a.__le__(b)` | `b.__ge__(a)` | `TypeError` |
| `a >= b` | `a.__ge__(b)` | `b.__le__(a)` | `TypeError` |

Let's build a `Money` class to watch this protocol in action.

---

### Equality: The Identity Safety Net

```python
from dataclasses import dataclass


@dataclass
class Money:
    """A monetary amount tied to a specific currency."""
    amount: float
    currency: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency
```

```python
rent = Money(1500.0, "USD")
rent_copy = Money(1500.0, "USD")
deposit = Money(1500.0, "EUR")

print(rent == rent_copy)         # True
print(rent == deposit)           # False
print(rent == "fifteen hundred") # False
print(rent != deposit)           # True
```

Four behaviors emerged from a single `__eq__` method. The comparison against the string `"fifteen hundred"` is the revealing one. Python called `Money.__eq__(rent, "fifteen hundred")`, got `NotImplemented`, then tried `str.__eq__("fifteen hundred", rent)`, got `NotImplemented` again. Both sides declined, so Python fell back to identity comparison: different objects, result `False`.

This fallback is safe because identity is universal. Every Python object lives at a unique memory address. Two objects of completely unrelated types are never the same object, so `==` returns `False` and `!=` returns `True`. No ambiguity, no crash.

---

### Ordering: No Safety Net

Now add ordering to the same class:

```python
from dataclasses import dataclass


@dataclass
class Money:
    """A monetary amount tied to a specific currency."""
    amount: float
    currency: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            return NotImplemented
        return self.amount < other.amount
```

```python
rent = Money(1500.0, "USD")
groceries = Money(320.0, "USD")

print(rent < groceries)  # False
print(groceries < rent)  # True

try:
    print(rent < Money(1500.0, "EUR"))
except TypeError as err:
    print(err)
# TypeError: '<' not supported between instances of 'Money' and 'Money'
```

The cross-currency comparison raised `TypeError` — and rightfully so. Is 1500 USD less than 1500 EUR? Without an exchange rate, the question has no answer. Python's refusal to guess is a feature. If ordering fell back to comparing `id()` values, you'd get a "result" that changes between program runs and means nothing. A loud error beats a silent wrong answer.

---

### NotImplemented vs. NotImplementedError

The most common mistake in comparison methods is confusing these two:

```python
# CORRECT — return the singleton to signal "I can't handle this operand"
def __lt__(self, other: object) -> bool:
    if not isinstance(other, Money):
        return NotImplemented
    ...

# WRONG — raising an exception kills the dispatch immediately
def __lt__(self, other: object) -> bool:
    if not isinstance(other, Money):
        raise NotImplementedError("Cannot compare Money with non-Money")
    ...
```

**`NotImplemented`** is a built-in singleton that you *return*. It tells the interpreter: "I don't know how to handle this operand — ask the other side." The dispatch protocol continues.

**`NotImplementedError`** is an exception that you *raise*. It aborts the dispatch entirely. The other operand never gets its turn. If you raise `NotImplementedError` inside `__eq__`, then `rent == "hello"` crashes instead of returning `False`. You've broken the protocol that every Python object relies on.

---

### Getting __ne__ for Free

When you define `__eq__`, you get `__ne__` automatically through inheritance from `object`. The inherited `__ne__` works like this (shown in Python, though the real implementation is in C):

```python
def __ne__(self, other: object) -> bool:
    eq_result = self.__eq__(other)
    if eq_result is NotImplemented:
        return NotImplemented
    return not eq_result
```

If `__eq__` returns `NotImplemented`, `__ne__` passes that signal through to the dispatch protocol. If `__eq__` returns a boolean, `__ne__` negates it. This is why `rent != deposit` returned `True` earlier without us writing any `__ne__` logic.

Override `__ne__` only if you need `!=` to behave differently from `not (a == b)`. This is almost never the case — and if you find yourself wanting it, reconsider whether your equality semantics make sense.

---

### functools.total_ordering: Write Two, Get Six

Supporting all six comparison operators means implementing five methods (`__eq__`, `__lt__`, `__le__`, `__gt__`, `__ge__`). The `functools.total_ordering` decorator eliminates the boilerplate — define `__eq__` plus any *one* ordering method, and it generates the remaining three:

```python
from dataclasses import dataclass
from functools import total_ordering


@total_ordering
@dataclass
class Money:
    """A monetary amount tied to a specific currency."""
    amount: float
    currency: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            return NotImplemented
        return self.amount < other.amount
```

```python
rent = Money(1500.0, "USD")
groceries = Money(320.0, "USD")

print(rent > groceries)     # True
print(groceries <= rent)    # True
print(groceries >= rent)    # False
```

All four ordering comparisons work from a single `__lt__`. The tradeoff is performance: the generated methods make an extra method call internally. For most code, this overhead is negligible. If you're sorting millions of objects in a tight loop, implementing all five methods directly avoids the indirection — but profile before optimizing.

---

### The Subclass Priority Rule

Python adds one more wrinkle. If `b` is an instance of a subclass of `a`'s class, Python tries `b`'s method *first*, even though `a` sits on the left side of the operator:

```python
@total_ordering
@dataclass
class DiscountedMoney(Money):
    """Money with a discount percentage applied at comparison time."""
    discount_pct: float = 0.0

    @property
    def effective(self) -> float:
        """Amount after applying the discount."""
        return self.amount * (1 - self.discount_pct / 100)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DiscountedMoney):
            return (self.effective == other.effective
                    and self.currency == other.currency)
        if isinstance(other, Money):
            return self.effective == other.amount and self.currency == other.currency
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, DiscountedMoney):
            if self.currency != other.currency:
                return NotImplemented
            return self.effective < other.effective
        if isinstance(other, Money):
            if self.currency != other.currency:
                return NotImplemented
            return self.effective < other.amount
        return NotImplemented
```

```python
full_price = Money(100.0, "USD")
on_sale = DiscountedMoney(100.0, "USD", discount_pct=25.0)

print(full_price == on_sale)  # False
print(on_sale < full_price)   # True
print(on_sale.effective)      # 75.0
```

When Python evaluates `full_price == on_sale`, it sees that `on_sale` is an instance of a `Money` subclass and calls `DiscountedMoney.__eq__(on_sale, full_price)` first. This ensures the more specific type controls the comparison. Without this rule, `Money.__eq__` would compare raw `amount` values and incorrectly report `True` — completely ignoring the discount.

This priority rule exists because subclasses typically have richer knowledge about how to compare themselves with their parent type. The parent's method might not even know the subclass exists.

---

### Conclusion

Python's six rich comparison operators split into two families with fundamentally different safety nets. Equality (`==`, `!=`) falls back to identity comparison because every object has an `id()` — the question "are these the same object?" always has an answer. Ordering (`<`, `>`, `<=`, `>=`) raises `TypeError` because no universal ordering exists — fabricating one would produce meaningless results.

Four rules keep custom comparisons correct. Return `NotImplemented` (never raise `NotImplementedError`) when you can't handle an operand. Let `__ne__` inherit from `__eq__` instead of reimplementing it. Use `functools.total_ordering` to generate four ordering methods from one. And when subclasses enter the picture, remember that Python gives the more specific type first shot at the comparison — regardless of which side of the operator it appears on.
