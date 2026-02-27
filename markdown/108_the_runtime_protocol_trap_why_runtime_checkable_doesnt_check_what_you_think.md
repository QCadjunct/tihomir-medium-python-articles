# The Runtime Protocol Trap: Why Python's @runtime_checkable Doesn't Check What You Think

#### It verifies that a method exists on the class — not that the method works, not that its signature matches, and not that it returns the right type

**By Tihomir Manushev**

*Feb 27, 2026 · 7 min read*

---

You define a protocol with `@runtime_checkable`, add an `isinstance` guard at the top of your function, and feel confident that any object passing the check will behave correctly. Then a caller passes an object whose method has the right *name* but the wrong *signature* — three required parameters instead of one. The `isinstance` check returns `True`. Your function calls the method. It crashes with a `TypeError` about missing arguments.

The `@runtime_checkable` decorator promises runtime type checking for protocols. What it actually delivers is far narrower: it checks whether an attribute with the right *name* exists on the object's class. It does not examine the method's parameters, return type, or type annotations. It does not call the method to see if it works. It does not even verify that the attribute is callable.

This gap between expectation and reality makes `@runtime_checkable` one of Python's most misunderstood features. Understanding what it checks — and what it cannot — prevents false confidence in your runtime validation.

---

### What @runtime_checkable Actually Checks

A `typing.Protocol` subclass defines a structural contract: a set of methods that conforming classes must implement. By default, this contract is enforced only by static type checkers like mypy or pyright. The `@runtime_checkable` decorator adds `isinstance` and `issubclass` support:

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Printable(Protocol):
    def to_display_string(self) -> str: ...
```

Now `isinstance` works against the protocol:

```python
class StatusReport:
    def to_display_string(self) -> str:
        return "All systems operational"


class TemperatureSensor:
    def read(self) -> float:
        return 22.5


print(isinstance(StatusReport(), Printable))       # True
print(isinstance(TemperatureSensor(), Printable))   # False
```

So far, so good. `StatusReport` has `to_display_string`, so it passes. `TemperatureSensor` does not, so it fails. The check works as expected — for this simple case.

The trouble starts when the method exists but does not match the protocol's declared signature.

---

### The Signature Blind Spot

`@runtime_checkable` verifies method *existence*, not method *shape*. A class whose method has a completely different signature will still pass the check:

```python
class BrokenReport:
    def to_display_string(self, width: int, indent: int, header: bool) -> bytes:
        return b"raw bytes"


print(isinstance(BrokenReport(), Printable))  # True
```

The protocol declares `to_display_string(self) -> str`. The class implements `to_display_string(self, width, indent, header) -> bytes`. Wrong parameters, wrong return type — yet `isinstance` returns `True`. The check saw the name `to_display_string` in the class dictionary and stopped looking.

Call the method through a function that expects the protocol's signature, and the mismatch surfaces:

```python
def render_summary(item: Printable) -> str:
    return f"[SUMMARY] {item.to_display_string()}"


render_summary(BrokenReport())
# TypeError: BrokenReport.to_display_string() missing 3 required
#            positional arguments: 'width', 'indent', and 'header'
```

This is the core limitation. Python's runtime does not inspect method signatures during `isinstance` checks because doing so would require introspecting every method on every call — an unacceptable performance cost for a dynamic language where `isinstance` is used in hot paths throughout the standard library.

Static type checkers *do* verify signatures. Run mypy on the code above and it flags `BrokenReport` as incompatible with `Printable`. But at runtime, you are on your own.

---

### Methods That Exist but Don't Work

Signature mismatches are the obvious trap. The subtler one is methods that have the right name and the right signature but raise exceptions when called.

Consider Python's `SupportsFloat` protocol from the `typing` module. It requires a `__float__` method. In Python 3.9 and earlier, the built-in `complex` type had a `__float__` method — but that method existed *solely* to raise `TypeError` with a helpful message:

```python
from typing import SupportsFloat

value = 3 + 4j
print(isinstance(value, SupportsFloat))  # True (Python 3.9)
float(value)
# TypeError: can't convert complex to float
```

The `isinstance` check returned `True` because `complex.__float__` existed as a method. But calling it raised an exception — the method was a trap, not an implementation. Python 3.10 fixed this specific case by removing `complex.__float__`, but the general pattern remains: `@runtime_checkable` cannot distinguish a working implementation from a method stub that raises `NotImplementedError` or `TypeError`.

If you define a protocol for objects that support serialization:

```python
@runtime_checkable
class Storable(Protocol):
    def save(self, path: str) -> None: ...
```

Any class with a `save` method passes the check — including one that raises `NotImplementedError`:

```python
class ReadOnlyCache:
    def save(self, path: str) -> None:
        raise NotImplementedError("Read-only cache cannot be saved")


print(isinstance(ReadOnlyCache(), Storable))  # True
```

The check says "yes, this is Storable." The method says "no, it is not." The `isinstance` result is technically correct — the method exists — but semantically misleading.

---

### The Inheritance Trap: @runtime_checkable Is Not Inherited

When you compose protocols by inheriting from a `@runtime_checkable` parent, the derived protocol does **not** inherit the decorator's behavior:

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Loadable(Protocol):
    def load(self, source: str) -> None: ...


class LoadableAndSaveable(Loadable, Protocol):
    def save(self, path: str) -> None: ...


class DataStore:
    def load(self, source: str) -> None:
        print(f"Loading from {source}")

    def save(self, path: str) -> None:
        print(f"Saving to {path}")


print(isinstance(DataStore(), Loadable))           # True — parent is runtime_checkable
print(isinstance(DataStore(), LoadableAndSaveable))
# TypeError: Protocols with non-method members don't support issubclass()
# or: Instance and class checks can only be used with @runtime_checkable protocols
```

The parent protocol `Loadable` is runtime-checkable. The derived protocol `LoadableAndSaveable` is not — despite inheriting from a runtime-checkable parent. You must apply the decorator again explicitly:

```python
@runtime_checkable
class LoadableAndSaveable(Loadable, Protocol):
    def save(self, path: str) -> None: ...


print(isinstance(DataStore(), LoadableAndSaveable))  # True
```

This catches developers who compose protocols incrementally and assume the runtime-checkable behavior carries through. It does not. Every protocol that needs `isinstance` support must be decorated individually.

---

### Data Attributes: Present but Not Typed

Python 3.12 improved `@runtime_checkable` to inspect instance attributes — not just the class. A protocol declaring a `name: str` attribute will now correctly detect instance attributes set in `__init__`. But the check is still shallow: it verifies that the attribute *exists*, not that its *type* matches:

```python
@runtime_checkable
class Named(Protocol):
    name: str


class Device:
    def __init__(self, name: str) -> None:
        self.name = name


class Gadget:
    def __init__(self) -> None:
        self.name = 42  # Wrong type — int, not str


print(isinstance(Device("sensor-01"), Named))  # True — name exists and is a str
print(isinstance(Gadget(), Named))              # True — name exists but is an int
```

Both pass. The protocol declares `name: str`, but `isinstance` does not compare the attribute's actual type against the annotation. `Gadget` stores an integer in `name` and the check says nothing is wrong. A static type checker would flag `Gadget` immediately — but at runtime, the annotation is invisible.

---

### When to Use @runtime_checkable

Given these limitations, `@runtime_checkable` is still useful — but for a narrower set of scenarios than most developers assume.

**Use it** for lightweight guards at system boundaries where you want to fail fast on obviously wrong types. If a function expects an object with a `render()` method and receives an integer, `isinstance(obj, Renderable)` will catch it immediately. The check is fast, the error message is clear, and the common case — correct types with correct signatures — is handled.

**Do not use it** as a substitute for static type checking. If signature conformance matters, run mypy or pyright. If behavioral correctness matters, write tests that exercise the methods. `@runtime_checkable` sits in the gap between these two — better than nothing, but weaker than either.

**Do not use it** in tight loops or performance-critical paths where you expect frequent protocol mismatches. The check is inexpensive on the happy path but carries overhead proportional to the number of methods in the protocol.

The mental model: `@runtime_checkable` is a **name check**, not a **contract check**. It answers "does this object have a method called X?" — not "does this object's X method do what I need?"

---

### Conclusion

`@runtime_checkable` fills a real need: quick, lightweight protocol checks at runtime without requiring inheritance or registration. But it checks less than its name implies. It verifies that methods *exist* on the class — not that their signatures match, not that they return the declared type, not that they work at all, and not that data attributes are present.

The decorator is not inherited by derived protocols, it cannot inspect instance attributes, and it operates at the class level rather than the instance level. These limitations are not bugs — they are performance tradeoffs that keep `isinstance` fast enough for widespread use.

Use `@runtime_checkable` as a coarse filter. Use static type checkers for signature verification. Use tests for behavioral correctness. And never assume that `isinstance(obj, MyProtocol)` returning `True` means the object fully satisfies the contract — it means the object has the right method names, and nothing more.
