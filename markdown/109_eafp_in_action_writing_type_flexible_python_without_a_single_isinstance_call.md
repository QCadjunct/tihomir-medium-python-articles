# EAFP in Action: Writing Type-Flexible Python Without a Single isinstance Call

#### Try the operation first, catch the exception second — and your functions will handle types they have never seen before

**By Tihomir Manushev**

*Feb 27, 2026 · 7 min read*

---

You write a configuration loader that accepts a dictionary. A week later, someone wants to pass a JSON string instead. You add an `isinstance(config, str)` check. Next month, someone wants to pass a file path. You add another `isinstance` check. Soon your function opens with a cascade of type tests — a brittle chain that must be updated every time a new input format appears.

There is a better way. Instead of asking "what type is this?", ask "what can this object do?" Try to use it as a dictionary. If that fails, try to parse it as JSON. If that fails, try to open it as a file. Each attempt either succeeds — in which case you have your answer — or raises a specific exception that tells you to try the next interpretation. This is **EAFP**: Easier to Ask Forgiveness than Permission.

EAFP is not just a philosophy. It is a concrete dispatch mechanism — a way to write functions that accept multiple input shapes without a single `isinstance` call, and that automatically support new types as long as those types implement the right operations.

---

### LBYL: The Cascade That Doesn't Scale

The opposite of EAFP is **LBYL** — Look Before You Leap. Check the type first, then act. A configuration loader written in LBYL style looks like this:

```python
import json
from pathlib import Path
from typing import Any


def load_config_lbyl(source: Any) -> dict[str, Any]:
    """Load configuration from a dict, JSON string, or file path."""
    if isinstance(source, dict):
        return source
    elif isinstance(source, str):
        path = Path(source)
        if path.is_file():
            return json.loads(path.read_text())
        else:
            return json.loads(source)
    elif isinstance(source, Path):
        return json.loads(source.read_text())
    else:
        raise TypeError(f"Cannot load config from {type(source).__name__}")
```

This works, but it has three problems.

**It is closed to extension.** If a colleague creates a `ConfigSource` class with a `.to_dict()` method, the function rejects it. Every new type requires a new `elif` branch and a code change.

**It over-specifies.** The `isinstance(source, str)` check forces you to distinguish between a JSON string and a file path *inside* the string branch — two unrelated concerns tangled together because the type check groups them.

**It couples to concrete types.** The function knows about `dict`, `str`, and `Path` by name. Any object that behaves like a dictionary but is not literally a `dict` — an `OrderedDict`, a `ChainMap`, a custom mapping — gets rejected.

---

### EAFP: Try, Catch, Dispatch

The EAFP version replaces type checks with operation attempts. Each `try` block tests a capability. Each `except` block signals "that interpretation did not work, try the next one":

```python
import json
from pathlib import Path
from typing import Any


def load_config(source: Any) -> dict[str, Any]:
    """Load configuration from a mapping, JSON string, or file path."""
    # Attempt 1: treat it as a mapping
    try:
        return dict(source.items())
    except AttributeError:
        pass

    # Attempt 2: treat it as a file path
    try:
        text = Path(source).read_text()
        return json.loads(text)
    except (OSError, TypeError):
        pass

    # Attempt 3: treat it as a JSON string
    try:
        result = json.loads(source)
        if isinstance(result, dict):
            return result
        raise ValueError("JSON did not produce a dictionary")
    except (json.JSONDecodeError, TypeError):
        pass

    raise TypeError(
        f"Cannot load config from {type(source).__name__}: "
        f"expected a mapping, file path, or JSON string"
    )
```

No `isinstance` checks. No type names hard-coded in conditions. Each block tests a *capability*, not an *identity*:

```python
# Dict input
print(load_config({"debug": True, "workers": 4}))
# {'debug': True, 'workers': 4}

# JSON string input
print(load_config('{"debug": false, "workers": 8}'))
# {'debug': False, 'workers': 8}

# Any mapping — OrderedDict, ChainMap, custom class
from collections import OrderedDict
print(load_config(OrderedDict(host="localhost", port=5432)))
# {'host': 'localhost', 'port': '5432'}
```

The function never asks "is this a dict?" It asks "does this have an `.items()` method?" Any object that does — `dict`, `OrderedDict`, `ChainMap`, a custom database-backed mapping — passes the first attempt without the function knowing the class exists.

---

### Why Exception Choice Matters

The exceptions you catch are the hinges of EAFP dispatch. Catching the wrong exception silently swallows real errors. Catching too broadly turns bugs into wrong results.

In `load_config`, each except clause targets the specific failure mode:

- **`AttributeError`** — the object does not have `.items()`. It is not a mapping. Move on.
- **`OSError`** — the path does not point to a readable file. It is not a file path. Move on.
- **`TypeError`** — `Path()` cannot accept this object (e.g., it is an integer). Move on.
- **`json.JSONDecodeError`** — the string is not valid JSON. Move on.

Never catch bare `Exception`. A function that catches `Exception` in its dispatch chain will swallow `KeyboardInterrupt` signals, memory errors, and bugs in your own code. Catch only the exceptions that indicate "this interpretation does not apply" — nothing more.

The ordering of attempts also matters. Try the most specific interpretation first. If you tried JSON parsing before the mapping check, a dictionary-like object with a `.items()` method would be serialized to a string and re-parsed — wasteful and fragile. The mapping check is cheapest and most specific, so it goes first.

---

### EAFP for Multi-Format Arguments

The pattern extends naturally to any function that accepts flexible input. Consider a function that normalizes tags — accepting a comma-separated string, a list of strings, or a single string:

```python
def normalize_tags(raw: str | list[str]) -> list[str]:
    """Accept tags as a comma-separated string or a list of strings."""
    try:
        segments = raw.split(",")
        return [tag.strip().lower() for tag in segments if tag.strip()]
    except AttributeError:
        return [tag.strip().lower() for tag in raw]
```

```python
print(normalize_tags("Python, Type Hints, EAFP"))
# ['python', 'type hints', 'eafp']

print(normalize_tags(["Python", "Type Hints", "EAFP"]))
# ['python', 'type hints', 'eafp']

print(normalize_tags(("Python", "Type Hints")))
# ['python', 'type hints']
```

The function tries `.split(",")` first. If the object has the method, it is treated as a string. If `AttributeError` fires, it falls through to the iterable path. Tuples, generators, sets — anything iterable works in the second branch without being listed by name.

This is more expressive than a type hint of `str | list[str]`. The type hint cannot capture "a string of comma-separated values." The EAFP dispatch handles the semantic difference that the type system cannot express.

---

### The Gotcha: Strings Are Always Iterable

EAFP dispatch has one recurring pitfall: strings implement nearly every sequence operation. If your fallback branch iterates over the input, a string will iterate over its *characters* instead of raising an exception:

```python
def process_items(data):
    try:
        return list(data.values())  # Mapping path
    except AttributeError:
        return list(data)           # Iterable path


print(process_items({"a": 1, "b": 2}))  # [1, 2] — correct
print(process_items([10, 20, 30]))        # [10, 20, 30] — correct
print(process_items("hello"))             # ['h', 'e', 'l', 'l', 'o'] — wrong!
```

The string has no `.values()` method, so it falls through to the iterable path, where it iterates over characters. No exception is raised — the result is silently wrong.

The fix is to try the string-specific path *before* the generic iterable path, as `normalize_tags` does above. If your function should treat strings as atomic values rather than character sequences, check for the string-specific operation first. The EAFP chain naturally handles this when ordered correctly: string operations first, generic iteration last.

When neither ordering solves the ambiguity — when a string and a list should be processed identically but a string should not be iterated character-by-character — this is the one case where an `isinstance(raw, str)` guard is justified. Not as a type check, but as a disambiguation between two equally valid iterable interpretations.

---

### When EAFP Loses to LBYL

EAFP is not universally superior. It has costs:

**Exception overhead.** When an exception is raised, CPython builds a traceback object and unwinds the call stack — roughly 10 to 100 times slower than a conditional branch. If you expect the first attempt to fail *most of the time*, a conditional check is faster. EAFP is optimal when the happy path dominates.

**Readability in long chains.** Three or four try/except blocks are readable. Ten become a maze. If your function needs to dispatch across many types, consider a registry pattern (a dictionary mapping types to handlers) instead of a linear EAFP chain.

**Swallowed errors.** A try/except block that catches `AttributeError` will also catch `AttributeError` raised *inside* the attempted operation — not just the one you expected. If `.items()` internally calls a helper that has a bug raising `AttributeError`, your dispatch chain will silently skip the mapping path and try JSON parsing instead. Keep the code inside each `try` block minimal to reduce the risk surface.

---

### Conclusion

EAFP turns exception handling into a dispatch mechanism. Instead of asking an object what it *is*, you ask what it can *do* — and the answer comes from whether the operation succeeds or raises a specific exception. Functions written this way accept types they have never seen, require no code changes when new types appear, and express semantic distinctions that the type system cannot capture.

The pattern is simple: try the most specific interpretation first. Catch only the exception that means "this interpretation does not apply." Fall through to the next attempt. If nothing works, raise a clear error.

Python's own interpreter uses this pattern internally — trying `__iter__` before falling back to `__getitem__` for iteration, trying `__contains__` before falling back to a sequential scan for membership. When you write EAFP dispatch, you are programming in the same style as Python itself.
