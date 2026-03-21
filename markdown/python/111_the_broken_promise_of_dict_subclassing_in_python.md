# The Broken Promise of dict Subclassing in Python

#### Why CPython's C internals silently ignore your method overrides — and what to use instead

**By Tihomir Manushev**

*Mar 03, 2026 · 7 min read*

---

You subclass `dict`, override `__setitem__` to enforce a constraint — say, every key must be a string — and test it with bracket assignment. The validation fires. Confident it works, you ship it. A week later, a colleague constructs the same subclass with keyword arguments: `ValidatedMap(count=5)`. The integer key sails through without triggering your override. No error, no warning, no validation.

This is not a bug in your code. It is a documented behavior of CPython: built-in types implemented in C do not reliably call overridden Python methods from their internal operations. The `dict` constructor, the `update` method, and several other operations call C-level functions directly, bypassing your `__setitem__` entirely. Understanding where this happens — and why — saves hours of debugging and steers you toward the right base class for custom mappings.

---

### The Override That Gets Ignored

Consider a mapping that enforces a simple invariant: every key must be a string. The implementation looks like textbook subclassing — override `__setitem__`, add a type check, and delegate to the parent for valid entries:

```python
class ValidatedMap(dict):
    """A dict that only accepts string keys."""

    def __setitem__(self, key: object, value: object) -> None:
        if not isinstance(key, str):
            raise TypeError(f"keys must be strings, got {type(key).__name__}")
        super().__setitem__(key, value)
```

Bracket assignment works exactly as expected:

```python
config = ValidatedMap()
config["host"] = "localhost"  # string key — passes validation
print(config)
# {'host': 'localhost'}

config[42] = "bad"  # integer key — rejected
# TypeError: keys must be strings, got int
```

So far, the override behaves correctly. Now pass data through the constructor and the `update` method:

```python
config = ValidatedMap(port=5432)
print(config)
# {'port': 5432}  — no TypeError raised

config["host"] = "localhost"
config.update({"timeout": 30, 99: "oops"})
print(config)
# {'port': 5432, 'host': 'localhost', 'timeout': 30, 99: 'oops'}
```

The integer key `99` entered the dictionary without triggering the type check. Neither the constructor nor `update()` ever called our `__setitem__`. Both operations routed directly to C-level insertion functions that skip Python's method dispatch entirely. The override exists, Python knows about it, and the built-in machinery chooses not to use it.

This behavior is not a special case or a known bug being fixed in a future release. It is how CPython's built-in types have always worked when subclassed, and it applies across the board.

---

### It's Not Just __setitem__

The bypass extends to read operations too. Override `__getitem__` to return a fallback value for missing keys, and watch `dict.get()` ignore it completely:

```python
class DefaultingMap(dict):
    """Returns a fallback for missing keys via bracket access."""

    def __init__(self, *args: object, fallback: object = None, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._fallback = fallback

    def __getitem__(self, key: object) -> object:
        try:
            return super().__getitem__(key)
        except KeyError:
            return self._fallback
```

Bracket access honors the override. The `.get()` method does not:

```python
env = DefaultingMap({"HOME": "/root"}, fallback="<unset>")

print(env["HOME"])          # /root — key exists
print(env["EDITOR"])        # <unset> — override returns fallback
print(env.get("EDITOR"))    # None — .get() bypassed __getitem__
```

The `.get()` call returned `None` — its own built-in default — instead of consulting the `__getitem__` override that would have produced `"<unset>"`. The C implementation of `dict.get()` performed the lookup internally and never dispatched through Python's attribute resolution.

The same pattern affects `__contains__`, `__delitem__`, and `setdefault` in various contexts. Any C-level method may shortcut past your Python-level override, and there is no comprehensive list documenting which methods bypass which dunders. The behavior can even change between CPython releases. This unpredictability is what makes `dict` subclassing genuinely dangerous: your tests might pass today because they exercise only the paths that happen to call your override, while other paths silently skip it.

---

### Why Built-in Types Cheat

Object-oriented languages rely on a principle called **late binding**: when an object calls one of its own methods, the runtime should start the method search from the receiver's actual class, not from wherever the calling code lives in the hierarchy. This is what makes polymorphism work — a subclass override should intercept calls regardless of which internal method triggered them.

CPython's built-in types violate this principle for performance. The `dict` type is implemented in C, and its methods call C-level siblings directly through function pointers. When `dict.update()` needs to insert a key, it calls an internal C function rather than the Python-level `__setitem__`. This avoids the overhead of Python method dispatch — attribute lookup, descriptor protocol, frame allocation — on every single key insertion. For a type as fundamental as `dict`, which underpins namespaces, keyword arguments, and class attribute storage, that overhead would compound across the entire interpreter.

The tradeoff is documented explicitly: CPython offers no formal specification for which built-in methods call which overridable dunder methods. The behavior is implementation-defined and may change between versions. PyPy, an alternative Python runtime, dispatches through overrides consistently — subclassing `dict` works as expected there. But code that depends on PyPy's stricter behavior will break silently on CPython, which remains the dominant runtime by a wide margin.

---

### UserDict: The Base Class That Plays Fair

The `collections` module provides `UserDict`, a pure-Python wrapper around a regular `dict`. Because `UserDict` is written entirely in Python, standard method dispatch applies. Override `__setitem__` in a `UserDict` subclass, and every insertion path — constructor, `update`, `setdefault`, bracket assignment — routes through your override without exception.

Here is the validated mapping rebuilt on the correct foundation:

```python
from collections import UserDict


class ValidatedMap(UserDict):
    """A mapping that only accepts string keys."""

    def __setitem__(self, key: object, value: object) -> None:
        if not isinstance(key, str):
            raise TypeError(f"keys must be strings, got {type(key).__name__}")
        super().__setitem__(key, value)
```

Every entry point now fires the validation:

```python
# Constructor validates keys
try:
    broken = ValidatedMap({99: "bad"})
except TypeError as exc:
    print(exc)
# keys must be strings, got int

# update() validates keys
config = ValidatedMap(host="localhost")
try:
    config.update({42: "bad"})
except TypeError as exc:
    print(exc)
# keys must be strings, got int

# Bracket assignment still works
config["port"] = "5432"
print(config)
# {'host': 'localhost', 'port': '5432'}
```

The same validation logic, the same one-method override — but now it runs everywhere. `UserDict` stores its data in an internal `self.data` attribute, which is an ordinary `dict`. Every public method that modifies the mapping delegates through `__setitem__`, and every method that reads keys delegates through `__getitem__`. If you need direct access to the underlying dictionary — for serialization, interop with C extensions, or bulk operations — `self.data` is always available.

The performance cost of this indirection is negligible for most applications. Both `dict` and `UserDict` provide O(1) average-case lookups and insertions. The per-operation overhead of Python-level dispatch adds microseconds, not milliseconds — invisible unless you are processing millions of insertions in a tight loop.

The `collections` module offers the same pattern for other built-in types. `UserList` wraps a `list`, and `UserString` wraps a `str`. Both exist for exactly the same reason: their built-in counterparts bypass overridden methods in subclasses, and these wrappers restore correct dispatch behavior.

---

### When to Subclass dict Directly

`UserDict` is not always necessary. If you are adding *new* methods to a mapping without overriding any existing dunder methods, subclassing `dict` works fine. A class that inherits `dict` and adds a `to_json()` convenience method never conflicts with C-level dispatch because it never redefines what `dict` already implements.

The decision comes down to one question: **are you overriding a dunder method?**

If yes, use `UserDict`. If you want full control over the mapping interface — exposing only a subset of the protocol — `collections.abc.MutableMapping` offers an abstract base class that requires only `__getitem__`, `__setitem__`, `__delitem__`, `__len__`, and `__iter__`. It then provides every remaining method (`get`, `pop`, `update`, `keys`, `values`, `items`, and more) as mixins built on top of those five. This approach gives you the tightest possible contract: you implement the primitives, and the ABC handles the derived operations correctly.

For the rare case where you need to override dunders *and* pass `isinstance(x, dict)` checks — because a third-party library explicitly tests for `dict` — consider composition. Store a `dict` internally, delegate to it, and expose only the interface you control. The `isinstance` requirement is worth pushing back on; well-designed APIs should accept `Mapping` or `MutableMapping`, not `dict`.

---

### Conclusion

Subclassing `dict` and overriding `__setitem__`, `__getitem__`, or any other dunder method produces code that passes simple tests and fails silently in production. CPython's C implementation routes internal operations through C-level functions that never consult your Python method overrides. Bracket-assignment tests succeed; constructor, `update`, and `get` calls quietly bypass your logic.

The fix is one import away: use `collections.UserDict` as your base class. It is pure Python, honors late binding, and routes every operation through your overrides. Reserve direct `dict` subclassing for cases where you extend without overriding — and reach for `UserDict` the moment you write `def __setitem__`.
