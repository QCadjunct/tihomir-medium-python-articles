# The @overload Decorator: Teaching Python Functions to Have Multiple Signatures

#### Python functions accept different argument types all the time — @overload tells the type checker exactly what comes back for each combination.

**By Tihomir Manushev**

*Mar 22, 2026 · 6 min read*

---

A Python function that returns different types depending on its input is perfectly normal. Pass a string to `json.loads` and you might get a `dict`, a `list`, an `int`, or a `bool`. Call `open` with `mode="r"` and you get a `TextIOWrapper`; call it with `mode="rb"` and you get a `BufferedReader`. The language handles this effortlessly at runtime.

Type checkers do not. A function signature like `def fetch(raw: bool = False) -> str | bytes` tells Mypy the return type is always `str | bytes`, even when you know that `raw=True` always returns `bytes`. Every call site must now handle both possibilities — or silence the checker with a cast. The type signature is technically correct but practically useless.

The `@overload` decorator from the `typing` module solves this. It lets you declare multiple signatures for the same function, each mapping a specific input pattern to a precise return type. The type checker picks the matching overload at each call site and narrows the return type accordingly. Your code stays dynamic. Your types stay precise.

---

### How @overload Works

An overloaded function has two parts: the **overload declarations** and the **implementation**. The declarations carry the type information. The implementation carries the logic. Only the implementation runs at runtime — the overload declarations exist solely for the type checker.

Consider a function that formats a timestamp. Pass an `int` (Unix epoch) and it returns a `datetime`. Pass a `str` (ISO format) and it returns a `str` with a human-readable format. Without overloads, the signature would be `def parse_timestamp(value: int | str) -> datetime | str` — forcing callers to narrow the return type manually every time.

With `@overload`, each input-output relationship gets its own declaration:

```python
from datetime import datetime, timezone
from typing import overload


@overload
def parse_timestamp(value: int) -> datetime: ...
@overload
def parse_timestamp(value: str) -> str: ...
def parse_timestamp(value: int | str) -> datetime | str:
    """Convert a Unix epoch to datetime, or reformat an ISO string."""
    if isinstance(value, int):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    return datetime.fromisoformat(value).strftime("%B %d, %Y at %H:%M")
```

The ellipsis (`...`) in each overload body is not a placeholder you fill in later — it is the required syntax. Overload declarations must have no implementation. The actual function body appears only in the final, non-decorated definition.

Now the type checker knows the exact return type at every call site:

```python
epoch: int = 1_700_000_000
result_dt = parse_timestamp(epoch)
# Mypy infers: datetime

iso_string: str = "2024-11-14T22:13:20"
result_str = parse_timestamp(iso_string)
# Mypy infers: str
```

No unions, no casts, no `isinstance` checks at the call site. The type checker matches the argument type to the correct overload and narrows the return type automatically.

---

### When @overload Earns Its Keep

The `parse_timestamp` example is clean but simple. The real power of `@overload` shows up when the return type depends on an argument's *value*, not just its type — particularly with boolean flags and literal types.

A common pattern in Python APIs is a `raw` or `as_bytes` flag that changes the return type. Without overloads, callers get a union:

```python
from typing import Literal, overload


@overload
def read_config(path: str, *, as_bytes: Literal[False] = ...) -> str: ...
@overload
def read_config(path: str, *, as_bytes: Literal[True]) -> bytes: ...
def read_config(path: str, *, as_bytes: bool = False) -> str | bytes:
    """Read a config file as text or raw bytes."""
    mode = "rb" if as_bytes else "r"
    with open(path, mode) as fh:
        return fh.read()
```

`Literal[True]` and `Literal[False]` let the type checker distinguish between the two modes. When a caller writes `read_config("app.toml")`, Mypy infers `str`. When they write `read_config("app.toml", as_bytes=True)`, Mypy infers `bytes`. The function is one implementation, but the type checker sees two distinct contracts.

This pattern appears throughout Python's standard library. The `open` built-in uses overloads in *typeshed* — Python's repository of type stubs — to map mode strings like `"r"`, `"rb"`, and `"w"` to their corresponding return types. The `json.dumps` function uses overloads to narrow its return type based on whether `default` is provided.

---

### Overloading on Argument Count

Overloads also handle functions that behave differently depending on how many arguments they receive. A factory function that returns a single object or a list of objects is a common case:

```python
from typing import overload


@overload
def make_tag(name: str) -> str: ...
@overload
def make_tag(name: str, *attributes: str) -> list[str]: ...
def make_tag(name: str, *attributes: str) -> str | list[str]:
    """Create an HTML tag, or multiple tags with attributes."""
    if not attributes:
        return f"<{name}></{name}>"
    return [f'<{name} {attr}></{name}>' for attr in attributes]
```

```python
single = make_tag("div")
# Mypy infers: str

multiple = make_tag("input", 'type="text"', 'type="email"')
# Mypy infers: list[str]
```

The type checker uses argument count to select the correct overload. One argument maps to `str`, two or more to `list[str]`.

---

### The Rules You Must Follow

The `@overload` decorator has strict rules. Violating them produces errors from the type checker, silent type mismatches, or both.

**Rule 1: Overloads are for type checkers only.** At runtime, Python ignores overload declarations entirely. Calling an overloaded function invokes only the implementation — the final, non-decorated definition. If you forget the implementation and only write overloads, the function raises a `TypeError` at runtime.

**Rule 2: The implementation signature must be compatible with all overloads.** The implementation's parameter types must be a union of all overload parameter types, and its return type must cover all overload return types. Mypy will flag an implementation that is too narrow.

**Rule 3: Overloads are matched top to bottom.** The type checker tries each overload in declaration order and picks the first match. Place more specific overloads before more general ones — a catch-all `str | int` overload placed first will shadow a more precise `int`-only overload below it.

**Rule 4: At least two overloads are required.** A single overload with an implementation is pointless — the implementation already provides the signature. Mypy will warn you.

---

### The Gotcha: Overloads in Modules vs. Stub Files

You can write overloads directly in your `.py` files or in separate `.pyi` stub files. The behavior differs in a subtle way.

In a `.py` file, the overload declarations and the implementation must appear together, with the implementation last:

```python
@overload
def compress(data: str) -> str: ...
@overload
def compress(data: bytes) -> bytes: ...
def compress(data: str | bytes) -> str | bytes:
    # implementation here
    ...
```

In a `.pyi` stub file, you write only the overload declarations — no implementation. The ellipsis body is the entire function definition:

```python
# compress.pyi
@overload
def compress(data: str) -> str: ...
@overload
def compress(data: bytes) -> bytes: ...
```

The trap is mixing these up. If you write overloads in a `.py` file without an implementation, the function exists at import time (Python binds the last `@overload`-decorated version) but behaves incorrectly — it returns `None` or raises, because overload-decorated functions are replaced by a no-op wrapper. Always include the implementation in `.py` files.

---

### When Not to Overload

Not every function with a union return type needs `@overload`. If the return type does not depend on the input types — for example, a parser that returns `int | float | str` regardless of what you pass — overloads cannot help. The type checker cannot narrow a return type that genuinely varies at runtime independent of the arguments.

Similarly, if your function has only one call pattern but returns a union, a simple `-> str | None` annotation is clearer than an overload. Reserve `@overload` for functions where distinct input patterns map to distinct output types. If you cannot draw a clear line between "this input always produces this output," the function does not need overloads — it needs a union.

---

### Conclusion

`@overload` bridges the gap between Python's dynamic flexibility and the type checker's need for precision. It lets you declare that `int` in means `datetime` out, that `raw=True` means `bytes`, that one argument means a scalar and three arguments mean a list — all without runtime overhead.

The pattern is simple: write the overload declarations for the type checker, write the implementation for Python, and let each tool see what it needs. Your functions stay dynamic. Your call sites get precise types. And your IDE finally stops suggesting `.decode()` on a value you know is already a string.
