# Reading Type Hints at Runtime: What __annotations__ Actually Contains

#### Python stores your type hints in __annotations__ dictionaries — but forward references, string literals, and evaluation timing turn reading them into a minefield.

**By Tihomir Manushev**

*Apr 01, 2026 · 6 min read*

---

Type hints in Python are not just decoration for your editor. The interpreter reads them at import time, evaluates them, and stores them in `__annotations__` dictionaries attached to functions, classes, and modules. This makes type hints available for runtime inspection — and opens the door to frameworks that build validators, serializers, and ORMs from annotations alone.

But reading annotations correctly is harder than it looks. A forward reference to a class that has not been defined yet becomes a string instead of a type. A hint that uses `from __future__ import annotations` delays evaluation entirely, turning every annotation into a string. And the difference between accessing `__annotations__` directly and using `typing.get_type_hints` can mean the difference between working code and a `NameError`.

Understanding how Python stores, evaluates, and resolves annotations is essential for anyone building tools that consume type hints — and useful for anyone who wants to understand what their annotations actually mean at runtime.

---

### Where Annotations Live

Python stores annotations in three places, each as a plain dictionary mapping names to their annotated types.

**Functions** store parameter and return annotations in `function.__annotations__`:

```python
def send_alert(message: str, severity: int, silent: bool = False) -> None:
    pass


print(send_alert.__annotations__)
# {'message': <class 'str'>, 'severity': <class 'int'>,
#  'silent': <class 'bool'>, 'return': None}
```

The `return` key holds the return type annotation. Parameter defaults are not included — only the types.

**Classes** store field annotations in `cls.__annotations__`, but only for fields declared in that class, not inherited ones:

```python
class Sensor:
    name: str
    unit: str
    precision: int = 2


print(Sensor.__annotations__)
# {'name': <class 'str'>, 'unit': <class 'str'>, 'precision': <class 'int'>}
```

**Modules** store top-level variable annotations in the module's `__annotations__` dictionary, accessible via `vars(module)["__annotations__"]` or directly as `__annotations__` at module scope.

In all three cases, the annotations are evaluated at import time and stored as Python objects — `str` becomes `<class 'str'>`, `list[int]` becomes `list[int]`, and `None` becomes `<class 'NoneType'>`.

---

### The Forward Reference Problem

Evaluation at import time breaks when a type hint references a name that does not exist yet. This happens most commonly when a class method returns an instance of its own class:

```python
class TreeNode:
    value: int
    children: list["TreeNode"]  # Forward reference — quoted string

    def __init__(self, value: int) -> None:
        self.value = value
        self.children = []

    def add_child(self, value: int) -> "TreeNode":
        """Create and attach a child node."""
        child = TreeNode(value)
        self.children.append(child)
        return child


print(TreeNode.__annotations__)
# {'value': <class 'int'>, 'children': list['TreeNode']}
```

The `children` annotation contains the string `'TreeNode'` rather than the actual class, because Python evaluates the annotation before the class body finishes executing. The string is a **forward reference** — a promise that the name will exist later.

This is not a problem for type checkers. Mypy resolves forward references during analysis. But runtime code that reads `__annotations__` directly sees the raw string and must resolve it manually.

---

### get_type_hints Resolves What __annotations__ Cannot

The `typing.get_type_hints` function reads `__annotations__` and resolves forward references by evaluating string annotations in the correct namespace:

```python
from typing import get_type_hints


class TreeNode:
    value: int
    children: list["TreeNode"]

    def __init__(self, value: int) -> None:
        self.value = value
        self.children = []

    def add_child(self, value: int) -> "TreeNode":
        child = TreeNode(value)
        self.children.append(child)
        return child


print(get_type_hints(TreeNode))
# {'value': <class 'int'>, 'children': list[TreeNode]}

print(get_type_hints(TreeNode.add_child))
# {'value': <class 'int'>, 'return': <class '__main__.TreeNode'>}
```

Where `__annotations__` shows `list['TreeNode']` with a string, `get_type_hints` returns `list[TreeNode]` with the actual class. It evaluates the string `'TreeNode'` in the module's global namespace, finds the class, and substitutes it.

This is why frameworks like Pydantic and dataclasses use `get_type_hints` instead of reading `__annotations__` directly — it handles forward references transparently.

---

### The __future__ Annotations Twist

PEP 563 introduced `from __future__ import annotations`, which changes annotation evaluation fundamentally. With this import, Python does not evaluate annotations at import time at all. Instead, it stores every annotation as a string:

```python
from __future__ import annotations


class Pipeline:
    name: str
    stages: list[Stage]  # No error — 'Stage' is stored as a string


class Stage:
    label: str
    timeout: int


print(Pipeline.__annotations__)
# {'name': 'str', 'stages': 'list[Stage]'}
```

Without the future import, `list[Stage]` would raise a `NameError` because `Stage` is not defined when `Pipeline` is evaluated. With the import, Python stores the literal string `'list[Stage]'` and moves on. No evaluation, no error.

This means `__annotations__` becomes a dictionary of strings rather than types. Code that expects type objects — `isinstance` checks, type comparisons — breaks silently. The annotations look like type hints but are actually strings.

`get_type_hints` handles this correctly. It evaluates the stored strings in the proper namespace and returns resolved type objects:

```python
from __future__ import annotations
from typing import get_type_hints


class Pipeline:
    name: str
    stages: list[str]


print(Pipeline.__annotations__)
# {'name': 'str', 'stages': 'list[str]'}

print(get_type_hints(Pipeline))
# {'name': <class 'str'>, 'stages': list[str]}
```

The rule is straightforward: **never read `__annotations__` directly if you need resolved types.** Always use `get_type_hints`.

---

### inspect.get_annotations: The Modern Alternative

Python 3.10 introduced `inspect.get_annotations` as a more robust way to read annotations. It handles the edge cases that direct `__annotations__` access gets wrong — missing dictionaries, inherited annotations, and evaluation control:

```python
import inspect


class BaseModel:
    id: int
    created_at: float


class User(BaseModel):
    name: str
    email: str


# __annotations__ shows only the declaring class's fields
print(User.__annotations__)
# {'name': <class 'str'>, 'email': <class 'str'>}

# inspect.get_annotations with eval_str resolves string annotations
print(inspect.get_annotations(User, eval_str=True))
# {'name': <class 'str'>, 'email': <class 'str'>}
```

The `eval_str=True` parameter tells `inspect.get_annotations` to evaluate string annotations — similar to what `get_type_hints` does, but with fewer surprises around `typing`-specific features like `ClassVar` and `Final`.

For new code targeting Python 3.10+, `inspect.get_annotations` is the recommended approach. For code supporting older versions, `typing.get_type_hints` remains the reliable choice.

---

### The Gotcha: Annotations Are Not Inherited

A common surprise: `__annotations__` on a class includes only the annotations declared in that class, not those from its parents:

```python
class Vehicle:
    make: str
    year: int


class Truck(Vehicle):
    payload_kg: float


print(Truck.__annotations__)
# {'payload_kg': <class 'float'>}  — no 'make' or 'year'
```

`make` and `year` are not in `Truck.__annotations__` because they belong to `Vehicle`. If you need all annotations including inherited ones, walk the MRO manually or use `typing.get_type_hints`, which collects annotations from the entire class hierarchy:

```python
from typing import get_type_hints

print(get_type_hints(Truck))
# {'make': <class 'str'>, 'year': <class 'int'>, 'payload_kg': <class 'float'>}
```

This is another reason to prefer `get_type_hints` over raw `__annotations__` access — it does the MRO traversal for you.

---

### Conclusion

Python annotations are accessible at runtime, but accessing them correctly requires understanding how they are stored and when they are evaluated. `__annotations__` gives you the raw dictionary — strings for forward references, strings for everything under `from __future__ import annotations`, and only the declaring class's fields for classes.

`typing.get_type_hints` resolves strings, follows the MRO, and returns actual type objects. `inspect.get_annotations` offers finer control on Python 3.10+. In both cases, the principle is the same: never trust raw `__annotations__` for resolved types. Use the tools Python provides to read what the annotations actually mean, not just what they literally contain.
