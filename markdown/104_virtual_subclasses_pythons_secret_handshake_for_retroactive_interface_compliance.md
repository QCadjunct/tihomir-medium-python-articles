# Virtual Subclasses: Python's Secret Handshake for Retroactive Interface Compliance

#### With ABC.register(), you can declare that a class satisfies an interface without touching its source code or its inheritance tree

**By Tihomir Manushev**

*Feb 19, 2026 · 7 min read*

---

You are building a data serialization framework. Every serializer in your system must conform to a common interface — `serialize()` and `deserialize()` — so your pipeline can swap formats without changing a line of calling code. You define an Abstract Base Class, write your JSON and CSV serializers, and everything works.

Then a colleague points you to a third-party TOML library. Its serializer class has exactly the methods your ABC requires — same names, same signatures, same behavior. But it does not inherit from your ABC. You cannot modify its source code. When your pipeline runs `isinstance(toml_serializer, Serializer)`, it returns `False`. Your framework rejects a perfectly valid class because of a missing inheritance declaration.

This is the problem that `ABC.register()` solves. It lets you declare — from the *outside* — that a class conforms to an ABC. No inheritance required. No source code changes. No monkey patching. Python will treat the registered class as a subclass of the ABC for all `isinstance` and `issubclass` checks. The catch: Python takes your word for it and never verifies that the class actually implements the interface.

---

### The Problem: Interface Compliance Without Inheritance

Start with a straightforward serializer ABC and one conforming subclass:

```python
import abc
from typing import Any


class Serializer(abc.ABC):
    """Contract for data serialization formats."""

    @abc.abstractmethod
    def serialize(self, data: dict[str, Any]) -> str:
        """Convert a dictionary to a formatted string."""

    @abc.abstractmethod
    def deserialize(self, raw: str) -> dict[str, Any]:
        """Parse a formatted string back into a dictionary."""

    def round_trip(self, data: dict[str, Any]) -> dict[str, Any]:
        """Serialize and deserialize to verify format integrity."""
        return self.deserialize(self.serialize(data))
```

The ABC has two abstract methods and one concrete mixin — `round_trip()` — that subclasses inherit for free. A JSON serializer that inherits from `Serializer` gets everything:

```python
import json


class JsonSerializer(Serializer):
    def serialize(self, data: dict[str, Any]) -> str:
        return json.dumps(data, indent=2)

    def deserialize(self, raw: str) -> dict[str, Any]:
        return json.loads(raw)
```

```python
js = JsonSerializer()
print(isinstance(js, Serializer))  # True
print(js.round_trip({"version": 3}))  # {'version': 3}
```

Now imagine a third-party class that implements the same interface but knows nothing about your ABC:

```python
import tomllib
import tomli_w


class TomlSerializer:
    """Third-party TOML serializer — not under your control."""

    def serialize(self, data: dict[str, Any]) -> str:
        return tomli_w.dumps(data)

    def deserialize(self, raw: str) -> dict[str, Any]:
        return tomllib.loads(raw)
```

The methods are there. The signatures match. But the inheritance link is missing:

```python
ts = TomlSerializer()
print(isinstance(ts, Serializer))  # False
```

Any framework code that checks `isinstance(serializer, Serializer)` will reject this class. Duck typing says it qualifies. The type hierarchy says it does not.

---

### ABC.register(): Declaring Compliance After the Fact

The `register()` method on an ABC declares that a class is a **virtual subclass** — a class that Python recognizes as belonging to the ABC's family without requiring inheritance. Call it as a plain function on the class you want to register:

```python
Serializer.register(TomlSerializer)
```

One line. No modifications to `TomlSerializer`. Now the type checks pass:

```python
ts = TomlSerializer()
print(isinstance(ts, Serializer))   # True
print(issubclass(TomlSerializer, Serializer))  # True
```

This is the primary use case for `register()` — bringing classes you *do not control* into your type hierarchy. The third-party library never needs to know your ABC exists. You make the declaration in your own code, at the integration boundary.

When you *do* control the class but want to avoid inheriting from the ABC, you can use `register` as a decorator:

```python
@Serializer.register
class YamlSerializer:
    """A serializer that opts into the Serializer interface without inheriting."""

    def serialize(self, data: dict[str, Any]) -> str:
        lines = [f"{k}: {v}" for k, v in data.items()]
        return "\n".join(lines)

    def deserialize(self, raw: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for line in raw.strip().splitlines():
            key, value = line.split(": ", maxsplit=1)
            result[key] = value
        return result
```

The decorator form reads clearly — "this class registers itself as a Serializer" — but the plain function call is more common in practice because the whole point of virtual subclasses is to work with code you cannot decorate.

---

### What Virtual Subclasses Don't Get

Registration is a declaration, not an inheritance. Virtual subclasses gain *recognition* but not *behavior*. The `Serializer` ABC has a concrete `round_trip()` method that regular subclasses inherit automatically. Virtual subclasses do not:

```python
js = JsonSerializer()
print(js.round_trip({"format": "json"}))
# {'format': 'json'}

ts = TomlSerializer()
print(ts.round_trip({"format": "toml"}))
# AttributeError: 'TomlSerializer' object has no attribute 'round_trip'
```

The reason is visible in the **Method Resolution Order**. Python searches for methods by walking the `__mro__` chain — the list of a class and its real superclasses. Virtual subclasses never appear in this chain:

```python
print(JsonSerializer.__mro__)
# (<class 'JsonSerializer'>, <class 'Serializer'>, <class 'abc.ABC'>, <class 'object'>)

print(TomlSerializer.__mro__)
# (<class 'TomlSerializer'>, <class 'object'>)
```

`JsonSerializer` has `Serializer` in its MRO, so it inherits `round_trip()`. `TomlSerializer` does not — its only ancestors are itself and `object`. The registration told Python "this class *is* a Serializer for type-checking purposes," but it did not weave `Serializer` into the inheritance graph.

This is the fundamental tradeoff. Regular inheritance gives you concrete mixin methods, instantiation-time enforcement, and a place in the MRO. Registration gives you type recognition and nothing else. If the ABC's concrete methods provide significant shared behavior — orchestration logic, validation workflows, retry mechanisms — virtual subclasses must reimplement that behavior themselves or forgo it entirely.

---

### The Gotcha: No Conformance Checking at Registration Time

Here is the trap that makes virtual subclasses dangerous in careless hands. When you call `register()`, Python performs **zero validation**. It does not check whether the class implements the abstract methods. It does not check method signatures. It does not check anything at all. You can register a completely empty class and Python will not complain:

```python
class EmptySerializer:
    pass


Serializer.register(EmptySerializer)

print(isinstance(EmptySerializer(), Serializer))  # True
print(issubclass(EmptySerializer, Serializer))     # True
```

Both checks return `True`. Python trusts your declaration unconditionally. The failure comes later, at runtime, when your framework tries to call `serialize()` on an object that does not have it:

```python
empty = EmptySerializer()
empty.serialize({"key": "value"})
# AttributeError: 'EmptySerializer' object has no attribute 'serialize'
```

Compare this with regular inheritance, where Python raises `TypeError` the moment you try to instantiate a class with missing abstract methods. With registration, the guard disappears entirely. The burden of correctness shifts from the interpreter to the developer.

This is not a design flaw — it is a deliberate choice. Registration exists precisely for cases where you cannot modify the class, which means Python cannot inject the ABC's metaclass machinery into it. The `@abstractmethod` enforcement requires `ABCMeta` as the metaclass, and third-party classes do not have it. Registration is a trust-based handshake: you vouch for the class, and Python believes you.

The practical defense: **write tests**. If your framework accepts registered virtual subclasses, write integration tests that exercise every abstract method on every registered class. Registration removes the safety net, so your test suite must replace it.

---

### When to Register vs When to Inherit

The choice between `register()` and inheritance maps to a simple question: *do you control the class?*

**Inherit** when you own the class and want the full package — abstract method enforcement at instantiation, concrete mixin methods inherited automatically, and a clear declaration of intent in the class definition. This is the default choice for classes within your own codebase.

**Register** when the class lives in a third-party library, predates your ABC, or belongs to a codebase you cannot modify. Registration is also useful when you want to avoid coupling a class to a specific ABC hierarchy — for example, if the class needs to work in multiple frameworks that each define their own base classes.

Python's standard library uses registration extensively. In `collections.abc`, the built-in types `tuple`, `str`, `range`, and `memoryview` are all registered as virtual subclasses of `Sequence`. These types were implemented in C long before `collections.abc` existed. Registration brought them into the ABC hierarchy retroactively, without modifying a single line of their C source code.

For ABCs that need even looser coupling, Python supports `__subclasshook__` — a class method that lets an ABC recognize conforming classes *without even requiring registration*. The `Sized` ABC uses this to recognize any class with a `__len__` method. But implementing `__subclasshook__` in your own ABCs is risky: the structural check is fragile and hard to debug. Stick with explicit registration or inheritance for custom ABCs.

---

### Conclusion

`ABC.register()` bridges the gap between duck typing and formal type hierarchies. It lets you bring existing, unmodified classes into your ABC's family — making `isinstance` and `issubclass` return `True` without inheritance, without metaclass machinery, and without touching the class's source code.

The tradeoff is real: virtual subclasses gain type recognition but not inherited behavior. They skip the MRO, miss concrete mixin methods, and face no conformance checks at registration time. Python takes your word that the class implements the interface and never verifies it.

Use inheritance when you want Python to enforce the contract. Use `register()` when you trust the class but cannot change it. And whichever path you choose, write the tests — because at runtime, the methods either exist or they do not, and no amount of type-checking ceremony will save you from an `AttributeError` in production.
