# Nominal vs. Structural Typing in Python
#### Mastering the trade-offs between Nominal and Structural typing to build robust, decoupled Python 3 architectures

**By Tihomir Manushev**  
*Jan 31, 2026 · 7 min read*

---

For the first two decades of its existence, Python operated under a single, unifying philosophy regarding types: **Duck Typing**. If an object walked like a duck (implemented `__iter__`) and quacked like a duck (implemented `__getitem__`), the Python interpreter treated it as a duck (a sequence). It didn’t matter if the object was actually a list, a tuple, or a strange bespoke class you wrote at 3 AM.

However, as Python codebases grew into millions of lines, the freedom of Duck Typing began to feel like chaos. We needed order. We needed interfaces.

Today, modern Python (3.10+) offers two distinct, yet often confused, ways to define interfaces: **Goose Typing** (via Abstract Base Classes) and **Static Duck Typing** (via Protocols). While they may look similar on the surface, they represent fundamentally different philosophies: **Nominal Typing** versus **Structural Typing**.

As a senior engineer, knowing which one to choose isn’t just a matter of syntax — it is an architectural decision that dictates the coupling and flexibility of your system.

---

### The Old Guard: Goose Typing and the ABC

“Goose Typing” is a term coined by Alex Martelli. It refers to a runtime check against an Abstract Base Class (ABC). When you use an ABC, you are engaging in **Nominal Typing**.

Nominal typing means that the identity of the object matters. An object is considered a valid input only if it explicitly declares, “I am a child of this parent.” It is a badge of lineage. You inherit from the ABC, and in doing so, you sign a contract with the framework.

---

### When to use ABCs: The Framework Foundation

ABCs are the tool of choice when you are building the bedrock of an application or a plugin architecture. They are prescriptive. They say, “If you want to play in this playground, you must follow these exact rules.”

Let’s imagine we are building a payment processing engine. We cannot afford ambiguity here. We need a strict hierarchy.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Transaction:
    amount: float
    timestamp: datetime
    currency: str

class PaymentGateway(ABC):
    """
    The Strict Contract. 
    Any subclass acts as a nominal subtype of PaymentGateway.
    """
    
    @abstractmethod
    def process(self, transaction: Transaction) -> bool:
        """Execute the payment."""
        pass

    @abstractmethod
    def refund(self, transaction_id: str) -> None:
        """Refund a previous transaction."""
        pass
    
    @staticmethod
    def log_transaction(t: Transaction) -> None:
        """Concrete method provided to all implementations."""
        print(f"[{t.timestamp}] Processing {t.currency} {t.amount}")
```

In this scenario, `PaymentGateway` is an *Is-A* relationship. A PayPal adapter *is a* `PaymentGateway`.

---

### The Mechanics of Enforcement

The beauty (and rigidity) of the ABC comes from how Python enforces it. This happens at two distinct times: instantiation and runtime inspection.

If a developer tries to create a class that inherits from `PaymentGateway` but forgets to implement `refund`, Python’s `ABCMeta` (the metaclass powering ABCs) will throw a `TypeError` the moment they try to instantiate the class. This is a “Fail Fast” mechanism that prevents incomplete implementations from leaking into your runtime logic.

```python
class StripeAdapter(PaymentGateway):
    def process(self, transaction: Transaction) -> bool:
        print("Stripe processing...")
        return True
    # Oops, we forgot 'refund'

# This raises TypeError immediately:
gateway = StripeAdapter()
```

Furthermore, functions that consume this class check the pedigree:

```python
def execute_batch(gateway: PaymentGateway, transactions: list[Transaction]):
    if not isinstance(gateway, PaymentGateway):
        raise TypeError("Invalid gateway provider")
    # ... logic ...
```

This `isinstance` check is the heart of Goose Typing. It provides runtime safety, but it couples the `StripeAdapter` tightly to the `PaymentGateway` definition. The adapter must import the ABC and inherit from it.

---

### The Modern Challenger: Static Duck Typing and Protocols

Introduced in Python 3.8 (PEP 544), Protocols brought a feature that statically typed languages like Go and TypeScript have enjoyed for years: **Structural Subtyping**.

In Structural Subtyping, the lineage doesn’t matter. The name of the class doesn’t matter. All that matters is: *Does it have the required methods?*

This is “Static Duck Typing.” It bridges the gap between the flexibility of dynamic Python and the safety of Mypy static analysis.

---

### When to use Protocols: The Client-Side Interface

Protocols shine when you need to define an interface for what your function needs, rather than what the object is. This is often called the “Role Interface” pattern. You define the protocol in the code that consumes the object, not in the library that defines the object.

Consider a logging system. Your logger might need to dump data to a file, a network socket, or a memory buffer. You don’t care if the object is a `File`, a `Socket`, or a `StringIO`. You certainly don’t want to force all those classes to inherit from a common `MyCustomLogger` ABC. You just need them to be writable.

```python
from typing import Protocol

# We use a Protocol to define the *capability* we need.
class Writable(Protocol):
    def write(self, data: str) -> int:
        ...

class AuditLog:
    def __init__(self, output: Writable):
        self.output = output

    def record(self, message: str):
        # Mypy guarantees 'output' has a .write() method
        self.output.write(f"AUDIT: {message}\n")
```

Now, look at the implementations. Notice they do not inherit from `Writable`. They don’t even know `Writable` exists.

```python
class TextFileHandler:
    def __init__(self, filename: str):
        self.f = open(filename, 'a')

    def write(self, data: str) -> int:
        return self.f.write(data)

class NetworkSocketHandler:
    def write(self, data: str) -> int:
        print(f"Sending {len(data)} bytes over network...")
        return len(data)

# Both work perfectly with AuditLog
# Mypy is happy. Python is happy.
file_log = AuditLog(TextFileHandler("audit.txt"))
net_log = AuditLog(NetworkSocketHandler())
```

The power here is loose coupling. `NetworkSocketHandler` might come from a third-party library (`boto3`, `requests`, etc.) that you cannot modify. You cannot retroactively force a library class to inherit from your ABC.

With Protocols, you don’t have to. You define the Protocol in your application code, and if the third-party class happens to match the signature (structure), the static type checker treats it as a subtype. This solves the “Wrapper Hell” problem where developers wrap 3rd party classes just to make them fit an ABC hierarchy.

---

### The Architectural Trade-off: Coupling vs. Control

So, how do you choose? The decision comes down to the relationship between the components.

#### Control and Intent (ABC Wins)

If you own both sides of the architecture — the interface definition and the concrete implementations — and you want to enforce a strict taxonomy, use ABCs.

ABCs are better at signalling design intent. Inheriting from `PaymentGateway` is a declaration: “I intend to be a payment gateway.” It prevents accidental matching. A class might coincidentally have a `process` method, but that doesn’t mean it handles payments. Nominal typing avoids these “false positives.”

#### Interoperability and Flexibility (Protocol Wins)

If you are writing a library function that accepts objects from the “outside world” (standard library objects, third-party packages), use Protocols.

Applying the Interface Segregation Principle (ISP) is much easier with Protocols. Instead of asking for a monolithic file object (which implies read, write, seek, close, and flush), your function can ask for exactly what it needs:

```python
class Closer(Protocol):
    def close(self) -> None: ...

def safe_shutdown(resource: Closer):
    resource.close()
```

This makes `safe_shutdown` incredibly reusable. It works with DB connections, files, sockets, and GUI windows, without any shared inheritance.

---

### The Hybrid Approach: Runtime Checkable Protocols

One distinct advantage Goose Typing used to have was `isinstance` checks. Protocols are primarily a static analysis tool; by default, they vanish at runtime.

However, Python provides a bridge: `@runtime_checkable`.

```python
@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str: ...

class Report:
    def render(self) -> str:
        return "Final Report"

r = Report()
# This returns True!
print(isinstance(r, Renderable))
```

When you use `@runtime_checkable`, Python inspects the object’s `__dir__` to ensure the methods exist.

**Warning: This comes with a performance cost and a semantic caveat.**

1.  **Performance:** It requires inspecting the object structure at runtime, which is slower than a standard MRO (Method Resolution Order) check used by ABCs.
2.  **Semantics:** It only checks for the presence of the method, not the signature. If `Report.render` required 5 arguments but the Protocol expected 0, `isinstance` would still return `True`, but the call would crash. ABCs and Mypy catch this; runtime Protocols do not.

---

### Conclusion

A helpful heuristic for navigating this divide is an adaptation of Postel’s Law (the Robustness Principle): *“Be conservative in what you do, be liberal in what you accept from others.”*

In Python typing terms:

*   **Be conservative in what you do:** When defining your core business logic and domain models, use ABCs. Be strict. define clear hierarchies. Ensure your internal classes explicitly inherit from these models to verify they fulfill the contract.
*   **Be liberal in what you accept:** When defining function arguments or APIs that interact with the outside world, use Protocols. Allow users to pass in any object that “quacks” correctly, regardless of its pedigree.

By understanding the distinction between the nominal identity of Goose Typing and the structural capability of Static Duck Typing, you move beyond simply making the code “run.” You begin designing systems that are both robust in their definition and flexible in their integration — the hallmark of high-quality Python engineering.
