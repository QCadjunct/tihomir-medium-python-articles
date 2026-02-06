# The Crumbling Tower: Why Python’s numbers Hierarchy Fails Modern Type Safety
#### How PEP 484 and Static Analysis rendered Python’s numbers module obsolete, and what to use instead for robust type safety

**By Tihomir Manushev**  
*Feb 6, 2026 · 7 min read*

---

In the early days of Python 3, the architectural vision for numeric types was elegant, mathematically pure, and structurally sound. It was based on the concept of the “Numeric Tower” — a hierarchy of Abstract Base Classes (ABCs) defined in PEP 3141 and residing in the `numbers` module.

The logic was flawless in theory: Integral implies Rational, which implies Real, which implies Complex, which finally implies Number. It mirrored the set theory taught in high school mathematics. For years, Python developers were told: “If you want to accept any number, type check against `numbers.Number`. If you need a floating-point value, check against `numbers.Real`.”

But as Python evolved from a purely dynamic language into one that heavily embraces static analysis and Gradual Typing (PEP 484), the Numeric Tower began to show structural cracks. Today, for the modern Python engineer relying on Mypy, Pyright, or PyCharm for type safety, the `numbers` module is effectively a trap.

Here is why the tower fell, and how we should architect numeric interfaces in the era of modern Python.

---

### The Ideal vs. The Implementation

To understand the failure, we must first appreciate the ambition. The `numbers` module was the epitome of Goose Typing — Python’s approach to runtime interface checking using ABCs.

Consider a physics simulation function designed to calculate kinetic energy. In the old world, we might write it like this to ensure we didn’t accidentally pass a string or a list:

```python
import numbers

def calculate_kinetic_energy(mass: numbers.Real, velocity: numbers.Real) -> numbers.Real:
    if not isinstance(mass, numbers.Real):
        raise TypeError("Mass must be a real number")
    return 0.5 * mass * (velocity ** 2)
```

At runtime, this works beautifully. Pass a float? It works. Pass an int? It works (because int is a virtual subclass of Real). Pass a `fraction.Fraction`? It works.

However, the moment we introduce a static type checker, the abstraction leaks.

---

### The Root Problem: Number is Empty

The top of the tower is `numbers.Number`. One might assume that annotating a variable as `x: Number` tells the type checker, “This is something I can do math with.”

It does not.

If you inspect the source code or the stub files for `numbers.Number`, you will find that it defines no methods. It does not guarantee addition, subtraction, or even comparison. It is a semantic marker, not a behavioral contract.

Consequently, modern static analysis tools will flag valid code as erroneous:

```python
# modern_physics.py
from numbers import Number

def add_scalars(a: Number, b: Number) -> Number:
    # Mypy Error: "Number" has no attribute "__add__"
    return a + b
```

The type checker is technically correct: not everything that inherits from Number supports addition. However, this renders the root of the tower useless for the very purpose type hints were invented: to prove code correctness before execution.

---

### The Decimal Schism

The second structural failure of the Numeric Tower is the treatment of `decimal.Decimal`.

In the mathematical universe, a decimal number is a Real number. However, in the “pragmatic” universe of software engineering, mixing floating-point numbers (which obey IEEE 754) and Decimals (which require arbitrary precision) is a recipe for silent, catastrophic precision errors.

Because of this, the Python core developers made a conscious decision: `decimal.Decimal` does not register itself as a virtual subclass of `numbers.Real`.

This creates a paradox where `numbers.Real` does not actually mean “any real number.” It means “floating-point numbers and rationals, but not the one type you actually use for money.”

```python
import numbers
from decimal import Decimal

val = Decimal('3.14')

# Returns False, confusing developers who know Decimal is "Real" math
print(isinstance(val, numbers.Real))
```

This inconsistency forces developers to abandon the ABCs and write ugly Union types or explicit runtime checks anyway, defeating the purpose of the abstraction.

---

### The Static Solution: Protocols over Hierarchies

If nominal subtyping (inheriting from ABCs) fails us, we must turn to Static Duck Typing — also known as structural subtyping. This is powered by PEP 544 and the `typing.Protocol` mechanism.

Instead of asking “What is your name?” (Inheritance), we ask “What can you do?” (Protocols).

Python 3.8+ introduced specific numeric protocols in the `typing` module, but they come with significant caveats. The most common ones are `typing.SupportsFloat`, `typing.SupportsInt`, and `typing.SupportsComplex`.

These protocols define objects that have `__float__`, `__int__`, or `__complex__` methods, respectively. This seems like a solution, but it separates the ability to convert to a number from the ability to act like a number.

---

### The complex Trap

A subtle but dangerous issue arises when using runtime_checkable protocols with complex numbers. In Python 3.9, the built-in complex type implements `__float__`, but only to raise a `TypeError` saying “can’t convert complex to float.”

This leads to a situation where a runtime check lies to you:

```python
from typing import SupportsFloat

c = 3 + 4j

# Returns True in Python 3.9!
is_floatable = isinstance(c, SupportsFloat)

if is_floatable:
    # Raises TypeError: can't convert complex to float
    val = float(c)
```

While Python 3.10 cleaned up some of these dunder methods, reliance on Supports* protocols for runtime checks remains fraught with version-specific inconsistencies.

---

### Production-Grade Solutions

So, if `numbers.Number` is useless for static typing, and `numbers.Real` excludes Decimal, and `SupportsFloat` can be misleading at runtime, what should a Senior Python Engineer use in production code?

We have three distinct strategies, depending on the level of precision and abstraction required.

#### Strategy 1: The Pragmatic Union (Recommended)

For 95% of use cases, you are not writing a generic library that needs to handle custom numeric types from third-party packages. You are handling standard primitives.

Explicit is better than implicit. Use Unions.

```python
from typing import TypeAlias
from decimal import Decimal

# Clear, explicit, and Mypy-compliant
Numeric: TypeAlias = float | int | Decimal

def calculate_tax(amount: Numeric, rate: float) -> Decimal:
    # Explicit conversion logic handles the types safely
    return Decimal(str(amount)) * Decimal(str(rate))

print(calculate_tax(100, 0.1))
```

This satisfies the Fail Fast principle. If a user passes a complex number or a string, the type checker catches it immediately. It avoids the ambiguity of the ABCs.

#### Strategy 2: Mypy’s Implicit Promotion

It is worth noting that Mypy (and PEP 484 standards) strictly enforce a rule that `int` is consistent-with `float`.

Even though `issubclass(int, float)` is False at runtime, static type checkers allow you to pass an int wherever a float is expected.

```python
def fast_inverse_sqrt(number: float) -> float:
    return number ** -0.5

# Mypy is happy with this, despite 100 being an int
result = fast_inverse_sqrt(100)
```

Therefore, if your function performs floating-point math, just annotate with `float`. The type checker will allow integers to pass through, and the Python interpreter will handle the promotion automatically. You do not need `numbers.Real`.

#### Strategy 3: Custom Protocols for Generic Math

If you are writing a library (like NumPy or TensorFlow) and you need to support any object that supports arithmetic operations (regardless of whether it inherits from a specific class), you should define a custom Protocol.

Do not use `numbers.Number`. Define exactly the behavior you need.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Addable(Protocol):
    def __add__(self, other: object) -> "Addable": ...

def accum_generics(a: Addable, b: Addable) -> Addable:
    return a + b
```

This adheres to the Interface Segregation Principle: client code should not depend on methods it does not use. By defining a narrow `Addable` protocol, you support int, float, complex, str, list, and any future custom class that supports the `+` operator.

---

### Conclusion

The Numeric Tower was a noble attempt to impose mathematical order on a dynamic world. However, in the modern era of Python — defined by practical static analysis and production safety — it has become an antipattern.

The numbers ABCs are too rigid for Decimal, too empty for Mypy, and too broad for robust error handling.

As Python engineers, we must shift our mindset from “What is this object’s place in the hierarchy?” to “What acts is this object capable of performing?” For static analysis, rely on implicit promotion (int -> float) or explicit Unions. For generic interfaces, rely on Protocols.

Leave the tower to the historians.
