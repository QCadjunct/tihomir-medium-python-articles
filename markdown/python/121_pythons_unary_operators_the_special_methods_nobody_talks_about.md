# Python's Unary Operators: The Special Methods Nobody Talks About

#### Everyone knows \_\_add\_\_ and \_\_eq\_\_, but \_\_neg\_\_, \_\_pos\_\_, \_\_abs\_\_, and \_\_invert\_\_ quietly power some of Python's most surprising behaviors.

**By Tihomir Manushev**

*Apr 05, 2026 · 6 min read*

---

Ask a Python developer to name a dunder method for operator overloading and you will hear `__add__`, `__eq__`, maybe `__mul__`. Ask them about `__neg__` or `__pos__` and you will likely get a blank stare. Unary operators live in the shadow of their binary cousins, rarely discussed and even more rarely implemented.

That is a missed opportunity. Unary operators — the minus `-x`, plus `+x`, bitwise not `~x`, and absolute value `abs(x)` — are simple to implement, easy to get right, and unlock expressive APIs for numeric and domain-specific types. They also hide one of Python's most surprising behaviors: cases where `x != +x` is `True` in the standard library.

Understanding these four special methods rounds out your knowledge of Python's operator model and gives you tools for building types that feel native to the language.

---

### The Four Unary Special Methods

Python defines four unary operator methods, each triggered by a specific syntax:

| Syntax | Method | Description |
|--------|--------|-------------|
| `-x` | `__neg__` | Arithmetic negation |
| `+x` | `__pos__` | Arithmetic plus (usually identity) |
| `~x` | `__invert__` | Bitwise NOT |
| `abs(x)` | `__abs__` | Absolute value |

Each method takes only `self` and returns a new object. The cardinal rule of operator overloading applies here: **never modify the receiver**. Unary operators produce new values — they do not mutate the original.

Here is a minimal `Temperature` class that supports all four where they make sense:

```python
class Temperature:
    """A temperature value in Celsius."""

    def __init__(self, degrees: float) -> None:
        self.degrees = degrees

    def __repr__(self) -> str:
        return f"Temperature({self.degrees})"

    def __neg__(self) -> "Temperature":
        """Negate the temperature: -Temperature(30) == Temperature(-30)."""
        return Temperature(-self.degrees)

    def __pos__(self) -> "Temperature":
        """Return the temperature unchanged."""
        return Temperature(self.degrees)

    def __abs__(self) -> "Temperature":
        """Return the absolute temperature value."""
        return Temperature(abs(self.degrees))


cold = Temperature(-15.0)

print(-cold)       # Temperature(15.0)
print(+cold)       # Temperature(-15.0)
print(abs(cold))   # Temperature(15.0)
```

`__neg__` flips the sign. `__abs__` strips it. `__pos__` returns a copy with the same value. We deliberately skip `__invert__` because bitwise NOT has no meaningful interpretation for a temperature — and implementing operators that do not make sense for your domain is worse than not implementing them at all. Python will raise a clear `TypeError` if someone tries `~cold`.

---

### __neg__: Arithmetic Negation

`__neg__` is the most intuitive unary operator. It maps directly to the mathematical concept of negation: `-x` produces the additive inverse of `x`. For numeric types, this means flipping the sign. For domain types, it means whatever "opposite" means in context.

A practical use case is a `Money` class where negation converts a credit to a debit:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    def __repr__(self) -> str:
        sign = "" if self.amount >= 0 else "-"
        return f"{sign}{self.currency}{abs(self.amount):.2f}"


payment = Money(49.99, "USD")
refund = -payment

print(payment)  # USD49.99
print(refund)   # -USD49.99
```

The key detail: `__neg__` returns a **new** `Money` instance. The original `payment` is untouched. This immutability guarantee is what makes unary operators safe to use in expressions like `total = payment + (-discount)`.

---

### __pos__: The Operator That Should Do Nothing (But Sometimes Doesn't)

Most developers assume `+x` is always equal to `x`. For integers, floats, and strings, that is true. But Python's data model makes no such guarantee — `__pos__` is a real method call, and the return value is whatever the class decides.

The standard library contains two cases where `x != +x`.

**Case 1: `decimal.Decimal` and precision contexts.** A `Decimal` created in one precision context retains its precision. Applying `+` re-evaluates it in the *current* context:

```python
import decimal

ctx = decimal.getcontext()
ctx.prec = 40

one_third = decimal.Decimal("1") / decimal.Decimal("3")
print(one_third)
# 0.3333333333333333333333333333333333333333

print(one_third == +one_third)  # True — same context

ctx.prec = 10
print(one_third == +one_third)  # False — different precision!

print(one_third)
# 0.3333333333333333333333333333333333333333  (40 digits)

print(+one_third)
# 0.3333333333  (10 digits — re-evaluated in current context)
```

The `+` operator does not return `self` — it creates a new `Decimal` with the same numeric value but evaluated in the current arithmetic context. When the precision differs, the two values are no longer equal.

**Case 2: `collections.Counter` and sign filtering.** Applying `+` to a `Counter` strips entries with zero or negative counts:

```python
from collections import Counter

inventory = Counter(apples=5, bananas=0, cherries=-3)
print(inventory)
# Counter({'apples': 5, 'bananas': 0, 'cherries': -3})

print(+inventory)
# Counter({'apples': 5})
```

This behavior is by design. `Counter` uses `+` as a cleanup operation — removing items that have been fully consumed or overdrawn. It is documented but rarely expected by developers who assume `+x == x`.

The lesson: `__pos__` is not an identity function. It is a method call that can return anything the class considers meaningful for the "positive" interpretation of itself.

---

### __abs__: Absolute Value

`abs(x)` delegates to `x.__abs__()`. For numbers, this means stripping the sign. For domain types, it can mean whatever "magnitude" means in context.

A two-dimensional point can use `__abs__` to return its distance from the origin:

```python
import math


class Point2D:
    """A point in 2D Euclidean space."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __abs__(self) -> float:
        """Return the Euclidean distance from the origin."""
        return math.hypot(self.x, self.y)

    def __repr__(self) -> str:
        return f"Point2D({self.x}, {self.y})"


p = Point2D(3.0, 4.0)
print(abs(p))  # 5.0
```

Note that `__abs__` returns a `float`, not a `Point2D`. This is intentional — the absolute value of a point is a scalar distance, not another point. The return type should match what "absolute value" means for your domain.

---

### __invert__: Bitwise NOT

The `~` operator triggers `__invert__`. For integers, `~x` equals `-(x + 1)`:

```python
print(~0)    # -1
print(~5)    # -6
print(~-1)   # 0
```

Outside of integer arithmetic, `__invert__` is fair game for domain-specific semantics. Pandas uses `~` to invert boolean Series. SQLAlchemy uses it to negate query conditions. Django uses it to invert Q objects.

Here is a simple `Permission` class where `~` revokes a permission:

```python
class Permission:
    """Represents a named permission that can be granted or revoked."""

    def __init__(self, name: str, granted: bool = True) -> None:
        self.name = name
        self.granted = granted

    def __invert__(self) -> "Permission":
        """Invert the permission: granted becomes revoked and vice versa."""
        return Permission(self.name, not self.granted)

    def __repr__(self) -> str:
        status = "granted" if self.granted else "revoked"
        return f"Permission({self.name!r}, {status})"


write_access = Permission("write")
print(write_access)     # Permission('write', granted)
print(~write_access)    # Permission('write', revoked)
```

The warning applies here too: only implement `__invert__` when `~` has a clear, intuitive meaning for your type. If users have to check the documentation to understand what `~` does, a named method like `.revoke()` is the better API.

---

### The Gotcha: Returning the Wrong Type

A common mistake is returning `self` from a unary operator instead of a new instance:

```python
class BrokenCounter:
    def __init__(self, value: int) -> None:
        self.value = value

    def __neg__(self) -> "BrokenCounter":
        self.value = -self.value  # Mutates self!
        return self


c = BrokenCounter(10)
negative = -c

print(negative.value)  # -10
print(c.value)         # -10 — original was mutated!
print(c is negative)   # True — same object
```

The caller expects `-c` to produce a new value, leaving `c` unchanged. Mutating `self` violates this expectation and creates aliasing bugs — `c` and `negative` point to the same object, and both are now negative. Always construct and return a new instance.

---

### Conclusion

Python's unary operators are the simplest corner of operator overloading — four methods, each taking only `self`, each returning a new value. `__neg__` flips the sign, `__abs__` extracts the magnitude, `__invert__` provides bitwise or logical negation, and `__pos__` does whatever "positive" means for your type.

The surprise is `__pos__`. It is not an identity function — it is a genuine method call, and the standard library proves it with `Decimal` precision re-evaluation and `Counter` sign filtering. When you implement these methods in your own types, follow the same contract: never mutate `self`, always return a new object, and only implement operators that have clear meaning for your domain.
