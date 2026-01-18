# Protocols vs. ABCs: The Evolution of Python Interfaces
#### Mastering Structural Subtyping and the transition from Abstract Base Classes to PEP 544 Protocols

**By Tihomir Manushev**  
*Jan 17, 2026 · 8 min read*

---

For decades, Object-Oriented Programming (OOP) was dominated by a singular dogma: inheritance is the only path to polymorphism. If you wanted a function to handle a generic Shape, you forced every circle, square, and triangle to inherit from a Shape base class.

Python, however, has always danced to a different beat. From its inception, Python prioritized behavior over lineage. This philosophy, known as Duck Typing, treated the type of an object as less important than what the object could actually do.

However, as Python codebases scaled from simple scripts to million-line enterprise systems, the looseness of Duck Typing became a double-edged sword. We needed more rigor. This drove the evolution of Python interfaces from informal conventions to Abstract Base Classes (ABCs), and finally, to the modern era of Static Protocols.

In this article, we will deconstruct this evolution. We will look at how to define interfaces that satisfy both the dynamic nature of the Python interpreter and the strict requirements of modern static type checkers like Mypy.

---

### The Old Guard: Dynamic Protocols (Duck Typing)

In languages like Java or C++, an interface is a rigid contract enforced by the compiler. In Python, a “protocol” was traditionally just a gentleman’s agreement — an informal interface defined only in documentation, not in code.

The most famous example is the Sequence Protocol. To create a custom sequence (like a list or tuple), you don’t need to inherit from list. You simply need to implement two special methods: `__len__` and `__getitem__`.

If your object “quacks” like a sequence (by implementing these methods), the Python interpreter treats it as one.

Let’s build a custom data structure called `AuditLog`. It holds a series of timestamped events. We won’t inherit from anything, yet we will make it behave exactly like a list.

```python
import time

class AuditLog:
    """A specific container for audit events."""
    
    def __init__(self, events: list[str] | None = None):
        self._events = list(events) if events else []
        self._timestamp = time.time()

    def __len__(self):
        return len(self._events)

    def __getitem__(self, position):
        return self._events[position]

    def add_event(self, event: str):
        self._events.append(event)
        
    def __repr__(self):
        return f"AuditLog({len(self)} events)"

# Usage
log = AuditLog(["User Login", "File Accessed"])

# Iteration works because of __getitem__ (fallback behavior)
for event in log:
    print(f"Event: {event}")

# Slicing works automatically
print(log[0:1])
```

When we iterate over log, the interpreter checks for `__iter__`. Finding none, it falls back to `__getitem__`, calling it with index 0, 1, 2, until an `IndexError` is raised. We achieved polymorphism without inheritance.

The problem arises when we need to enforce constraints. If I write a function `def process_data(data: Sequence):`, and pass it an object that looks like a sequence but is missing `__len__`, the error only happens at runtime, potentially deep inside the execution logic.

---

### The Middle Ground: Abstract Base Classes (ABCs)

To address the “wild west” nature of Duck Typing, Python 2.6 (and solidified in Python 3) introduced Abstract Base Classes (ABCs) via the `abc` module and `collections.abc`.

ABCs allow for Nominal Typing. This means an object is considered an instance of a type if it explicitly inherits from it (or is registered with it). ABCs provide two main benefits:

1.  **Runtime Checking:** We can use `isinstance(obj, SomeABC)`.
2.  **Implementation Enforcement:** If you inherit from an ABC but fail to implement an abstract method, instantiation fails immediately.

However, ABCs are invasive. You must modify your source code to inherit from them. This is problematic when using third-party libraries where you cannot change the class definition.

---

### The Modern Era: Static Protocols (PEP 544)

Python 3.8 brought a paradigm shift with PEP 544: Protocols: Structural subtyping.

This bridges the gap between the flexibility of Duck Typing and the safety of Type Checking. A Protocol allows you to define an interface that checks structure (what methods exist) rather than ancestry (what class you inherited from).

If a class implements the methods defined in a Protocol, it is considered a subtype, even if it doesn’t know the Protocol exists. This is Structural Subtyping.

Let’s imagine we are building a rendering engine. We want to accept any object that can render itself to HTML, regardless of whether it’s a User, a Report, or a Graph.

We define a Protocol `HTMLRenderable`.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class HTMLRenderable(Protocol):
    """
    Any object that implements this protocol can be passed 
    to our rendering engine.
    """
    def as_html(self) -> str:
        ...

class UserProfile:
    """
    A concrete class. Note: It does NOT inherit from HTMLRenderable.
    """
    def __init__(self, username: str):
        self.username = username

    def as_html(self) -> str:
        return f"<div class='user'>{self.username}</div>"

class SystemStatus:
    """Another concrete class, totally unrelated to UserProfile."""
    def __init__(self, is_up: bool):
        self.up = is_up

    def as_html(self) -> str:
        color = "green" if self.up else "red"
        return f"<span style='color:{color}'>●</span>"

def render_page(elements: list[HTMLRenderable]) -> str:
    return "\n".join(e.as_html() for e in elements)
```

1.  **Zero Coupling:** `UserProfile` and `SystemStatus` do not need to import `HTMLRenderable`. This solves the dependency hell often found with ABCs.
2.  **Static Verification:** If we try to pass an object to `render_page` that lacks the `as_html` method, specific type checkers (like Mypy or Pyright) will flag this as an error before the code ever runs.
3.  **Runtime Options:** By adding the `@runtime_checkable` decorator, we can still perform `isinstance(user, HTMLRenderable)` checks if necessary, effectively making the Protocol function like a sophisticated ABC.

---

### The Data Source Protocol

Let’s look at a production-grade example involving data ingestion. We want to ingest data from various sources (Database, API, CSV), but we don’t want to enforce a strict inheritance hierarchy on the driver classes.

We will define a `DataSource` protocol using Python 3.10+ syntax.

```python
from typing import Protocol, Any, runtime_checkable

# 1. Define the Protocol (The Interface)
@runtime_checkable
class DataSource(Protocol):
    """
    Defines the structural contract for any readable data source.
    """
    @property
    def is_connected(self) -> bool:
        ...

    def fetch_batch(self, size: int) -> list[dict[str, Any]]:
        ...

    def close(self) -> None:
        ...

# 2. Define Concrete Implementation A (No inheritance needed)
class RedisStream:
    def __init__(self, stream_key: str):
        self.stream_key = stream_key
        self._active = True

    @property
    def is_connected(self) -> bool:
        return self._active

    def fetch_batch(self, size: int) -> list[dict[str, Any]]:
        if not self._active:
            raise ConnectionError("Stream closed")
        # Simulating data fetch
        return [{"id": i, "source": "redis"} for i in range(size)]

    def close(self) -> None:
        print(f"Closing Redis stream {self.stream_key}")
        self._active = False

# 3. Define Concrete Implementation B (Totally different internal structure)
class FileIngestor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._handle = open(filepath, 'r') if filepath else None

    @property
    def is_connected(self) -> bool:
        return self._handle is not None and not self._handle.closed

    def fetch_batch(self, size: int) -> list[dict[str, Any]]:
        # Simulating file reading logic
        return [{"line": i, "content": "data"} for i in range(size)]

    def close(self) -> None:
        if self._handle:
            print(f"Closing file {self.filepath}")
            self._handle.close()

# 4. The Consumer Function
def run_ingestion(source: DataSource, batch_count: int):
    """
    This function is type-safe. Mypy guarantees 'source' has 
    'fetch_batch' and 'close'.
    """
    if not source.is_connected:
        print("Source is offline.")
        return

    print(f"Ingesting from {type(source).__name__}...")
    data = source.fetch_batch(batch_count)
    print(f"Processed {len(data)} items.")
    source.close()

# 5. Execution
if __name__ == "__main__":
    # Both classes satisfy the DataSource protocol implicitly
    redis_source = RedisStream("events_v1")
    file_source = FileIngestor("tmp/logs.txt")

    run_ingestion(redis_source, 5)
    run_ingestion(file_source, 3)

    # Runtime check demonstration
    print(f"Is RedisStream a DataSource? {isinstance(redis_source, DataSource)}")
```

Notice the elegance of `isinstance(redis_source, DataSource)`. Even though `RedisStream` never inherited from `DataSource`, Python’s `abc` machinery (which backs `@runtime_checkable`) inspects the class `__dict__`, sees the required methods, and returns `True`.

If we were to remove `close()` from `RedisStream`, the code would run fine until `run_ingestion` called `.close()`, causing a crash. However, if we ran mypy over this file, it would output an error flagging the missing method.

This is the power of Static Protocols: catching “duck typing” errors at build time.

---

### Best Practices for Modern Interfaces

When designing interfaces in Python 3.10+, follow these guidelines to balance flexibility and safety.

**1. Prefer Protocols for Library Code**
If you are writing a library meant to be used by others, define your input requirements as Protocols. This adheres to the Interface Segregation Principle (the “I” in SOLID). It allows users to pass any object that works, without forcing them to inherit from your base classes.

**2. Keep Protocols Narrow**
Don’t create a “God Protocol” with 20 methods. Create small, specific protocols like `Readable`, `Writable`, or `Closable`. You can compose them using inheritance if needed:

```python
class ReadWriteClose(Readable, Writable, Closable, Protocol):
    ...
```

**3. Use ABCs for Shared Implementation**
If you want to provide helper methods or default behavior to subclasses, use an ABC. Protocols cannot contain implementation logic (mostly). If you need code reuse and an interface, an ABC is still the correct tool. Use Protocols purely for type checking interfaces.

**4. Naming Conventions**
While not enforced, it is common to explicitly suffix protocols (e.g., `WritableProtocol`) or use capability-based naming (e.g., `Renderable`, `Hashable`, `Sizable`) to distinguish them from concrete classes.

---

### Conclusion

Python’s journey from dynamic protocols (Duck Typing) to ABCs, and finally to static Protocols, reflects the language’s maturity. We haven’t lost the soul of Python — the flexibility to pass objects based on behavior remains. However, we have gained the tools to rigorously describe that behavior.

By adopting `typing.Protocol`, we allow our code to remain loosely coupled while gaining the compile-time safety nets traditionally reserved for statically typed languages. We no longer check if it is a duck; we check if it implements the Quackable protocol.
