# TypedDict: When Your Dictionary Deserves a Schema

#### Python's TypedDict gives your dictionaries named keys and typed values — but it vanishes at runtime, and that changes everything.

**By Tihomir Manushev**

*Mar 24, 2026 · 6 min read*

---

Python dictionaries are the universal data container. API responses, configuration files, database rows, message payloads — they all arrive as `dict[str, Any]`. The type checker sees that annotation and shrugs. Any key might exist. Any value might be anything. You are on your own.

`TypedDict` changes this. It lets you declare a dictionary schema — specific keys with specific types — so the type checker can verify that you access the right keys and assign the right value types. A function that accepts a `UserProfile` instead of `dict[str, Any]` communicates its expectations precisely, and Mypy catches misspelled keys before your code reaches production.

But `TypedDict` is not a dataclass. It is not a Pydantic model. It creates a plain `dict` at runtime with zero validation. Understanding what it does — and what it deliberately does not do — determines whether it simplifies your code or gives you a false sense of safety.

---

### Declaring a TypedDict

A `TypedDict` definition looks like a class, but it behaves like a schema declaration for the type checker:

```python
from typing import TypedDict


class ServerConfig(TypedDict):
    host: str
    port: int
    debug: bool
    max_connections: int
```

At runtime, calling `ServerConfig` is identical to calling `dict`. It produces a plain dictionary with no special attributes, no validation, and no instance methods beyond what every `dict` has:

```python
config = ServerConfig(
    host="localhost",
    port=8080,
    debug=True,
    max_connections=100,
)

print(type(config))   # <class 'dict'>
print(config["host"]) # localhost
```

The type checker, however, now knows exactly what `config` contains. Accessing `config["hostname"]` triggers a Mypy error — the key does not exist in the schema. Assigning `config["port"] = "not_a_number"` fails too — the value must be `int`.

---

### Optional Keys with NotRequired

Not every key needs to be present in every instance. Python 3.11 introduced `NotRequired` to mark individual keys as optional:

```python
from typing import TypedDict, NotRequired


class DeploymentSpec(TypedDict):
    image: str
    replicas: int
    namespace: NotRequired[str]
    cpu_limit: NotRequired[str]
```

A `DeploymentSpec` must have `image` and `replicas`. The `namespace` and `cpu_limit` keys may be absent entirely — not `None`, but missing from the dictionary. The type checker understands this distinction:

```python
minimal: DeploymentSpec = {"image": "api:latest", "replicas": 3}
# Valid — optional keys are absent

full: DeploymentSpec = {
    "image": "api:latest",
    "replicas": 3,
    "namespace": "production",
    "cpu_limit": "500m",
}
# Also valid — optional keys are present
```

If most keys are optional and only a few are required, flip the default with `total=False` and mark the required ones explicitly:

```python
from typing import TypedDict, Required


class PatchPayload(TypedDict, total=False):
    name: str
    email: str
    role: str
    active: Required[bool]
```

Here, `active` must always be present. Everything else is optional. This is cleaner than marking a dozen keys with `NotRequired` individually.

---

### The Runtime Trap

`TypedDict` exists for the type checker. At runtime, it provides no guardrails. This is the most important thing to understand about it — and the source of most confusion.

A function that declares a `TypedDict` parameter accepts any `dict` at runtime without complaint:

```python
from typing import TypedDict


class Metric(TypedDict):
    name: str
    value: float
    unit: str


def record_metric(metric: Metric) -> None:
    """Store a metric reading."""
    print(f"{metric['name']}: {metric['value']} {metric['unit']}")


# Mypy catches this — wrong type for 'value'
# But Python runs it without error
garbage = {"name": "cpu", "value": "not_a_float", "unit": "percent"}
record_metric(garbage)  # prints: cpu: not_a_float percent
```

Mypy flags the `garbage` dictionary because `"not_a_float"` is not a `float`. But Python executes the call without hesitation — `garbage` is a `dict`, and that is all `record_metric` checks at runtime. There is no `isinstance` guard, no schema validation, no runtime type enforcement. The `TypedDict` annotation is invisible to the interpreter.

This means `TypedDict` is the wrong tool for validating external data. API responses, user input, and file contents can contain anything. If you need runtime validation, use Pydantic or write explicit checks. `TypedDict` protects you from your own code — not from the outside world.

---

### TypedDict vs Dataclass: Choosing the Right Tool

Both `TypedDict` and `@dataclass` define structured data with named fields and types. The difference is fundamental: a `TypedDict` produces a `dict`, and a `@dataclass` produces a custom class instance.

```python
from dataclasses import dataclass
from typing import TypedDict


class EventTD(TypedDict):
    name: str
    severity: int


@dataclass
class EventDC:
    name: str
    severity: int


td = EventTD(name="disk_full", severity=3)
dc = EventDC(name="disk_full", severity=3)

print(td["name"])     # dict access — bracket notation
print(dc.name)        # attribute access — dot notation

print(type(td))       # <class 'dict'>
print(type(dc))       # <class '__main__.EventDC'>
```

Use `TypedDict` when you are working with data that is already a dictionary — JSON payloads, legacy code, third-party APIs that return `dict`. Adding a schema to an existing `dict` flow costs nothing and changes no runtime behavior.

Use `@dataclass` when you own the data structure. Dataclasses give you `__init__`, `__repr__`, `__eq__`, attribute access, and the ability to add methods. They are real objects with real behavior.

The rule is simple: if the data arrives as a `dict` and stays a `dict`, use `TypedDict`. If you are creating the data structure from scratch, use `@dataclass`.

---

### Inheritance and Composition

`TypedDict` supports inheritance, which lets you build schemas incrementally:

```python
from typing import TypedDict, NotRequired


class BaseEvent(TypedDict):
    event_id: str
    timestamp: float


class ErrorEvent(BaseEvent):
    message: str
    stack_trace: NotRequired[str]


class MetricEvent(BaseEvent):
    metric_name: str
    value: float
```

`ErrorEvent` inherits `event_id` and `timestamp` from `BaseEvent` and adds its own fields. The type checker treats each subtype as a distinct schema — an `ErrorEvent` is not interchangeable with a `MetricEvent`, even though both share the base fields.

One restriction: you cannot mix `total=True` and `total=False` fields in a single class without inheritance. If you need some required and some optional keys, either use `Required`/`NotRequired` markers or split the schema into a required base and an optional subclass.

---

### The Gotcha: Structural Compatibility

`TypedDict` uses structural typing — any `dict` with the right keys and value types satisfies the schema. This works in your favor when passing plain `dict` literals to functions expecting a `TypedDict`. But it also means the type checker cannot distinguish between two unrelated `TypedDict` types that happen to have the same fields:

```python
from typing import TypedDict


class Coordinate(TypedDict):
    x: float
    y: float


class Dimension(TypedDict):
    x: float
    y: float


def plot_point(point: Coordinate) -> None:
    print(f"Plotting ({point['x']}, {point['y']})")


size: Dimension = {"x": 1920.0, "y": 1080.0}
plot_point(size)  # Mypy allows this — same structure
```

`Dimension` and `Coordinate` are structurally identical, so Mypy treats them as interchangeable. If semantic distinction matters, a `@dataclass` or `NamedTuple` — which use nominal typing — is the better choice. Two classes with the same fields but different names are different types.

---

### Conclusion

`TypedDict` fills a specific gap: it adds type checker visibility to dictionaries that must remain dictionaries. It does not validate data, create custom objects, or add runtime behavior. It is a lens that lets Mypy see structure in what would otherwise be an opaque `dict[str, Any]`.

Use it for JSON payloads, legacy dictionary flows, and API boundaries where changing the data structure is not an option. Reach for `@dataclass` when you control the data model. And never rely on `TypedDict` to catch bad data at runtime — that is a job for validation libraries, not type annotations.
