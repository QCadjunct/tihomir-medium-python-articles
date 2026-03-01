# Composing Narrow Protocols: The Go-Inspired Approach to Python Interface Design

#### Start with single-method protocols, compose them into richer contracts, and let static type checkers do the enforcement — no inheritance required

**By Tihomir Manushev**

*Feb 24, 2026 · 7 min read*

---

You are designing a content rendering pipeline. Some content blocks can be rendered to HTML. Some can be exported to PDF. Some support both. You reach for an ABC with `render()`, `export()`, `word_count()`, and `summarize()` — a wide interface that captures everything any content block might do.

Six months later, half your classes implement methods they do not need. The `PlainTextBlock` raises `NotImplementedError` from `export()` because plain text does not support PDF export. The `ImageBlock` returns zero from `word_count()` because images have no words. Your wide interface forced every class to carry dead methods, and the `NotImplementedError`s are just runtime traps waiting to fire.

The Go community solved this problem a decade ago: **keep interfaces small**. Define a one-method or two-method protocol for each capability. Compose wider contracts by combining narrow ones. Python adopted this philosophy with `typing.Protocol` in Python 3.8 — and after years of real-world use, the verdict is clear: narrow protocols are more useful, more flexible, and easier to test than wide ABCs.

---

### Why Narrow Beats Wide

A wide interface forces every implementor to support *all* of its methods, even when a particular class only needs a subset. This leads to three problems: stub methods that raise `NotImplementedError`, meaningless return values that satisfy the type checker but mislead callers, and tight coupling between unrelated capabilities.

Narrow protocols eliminate this by representing **single capabilities** rather than complete role descriptions. Instead of one `ContentBlock` ABC with five methods, you define five single-method protocols. Each class implements only the protocols it actually supports. A function that renders content asks for `Renderable` — nothing more. A function that counts words asks for `Measurable` — nothing more. Neither forces the other's requirements onto your classes.

This is the **Interface Segregation Principle**: clients should not depend on interfaces they do not use. In Go, this principle is foundational. In Python, `typing.Protocol` makes it practical.

---

### Your First Protocol: One Method, One Capability

A `typing.Protocol` subclass defines a structural contract. Any class that implements the required methods satisfies the protocol — no inheritance, no registration, no decoration needed:

```python
from typing import Protocol


class Renderable(Protocol):
    """Any content that can produce an HTML string."""

    def render(self) -> str: ...
```

The ellipsis `...` is not a placeholder — it is the complete method body. Protocol methods declare *what* must exist, not *how* it works. Now any class with a `render()` method that returns a `str` satisfies `Renderable`:

```python
class MarkdownBlock:
    def __init__(self, text: str) -> None:
        self._text = text

    def render(self) -> str:
        return f"<p>{self._text}</p>"


class AlertBanner:
    def __init__(self, message: str, level: str = "info") -> None:
        self._message = message
        self._level = level

    def render(self) -> str:
        return f'<div class="alert-{self._level}">{self._message}</div>'
```

Neither class inherits from `Renderable`. Neither imports it. Neither knows it exists. Yet both satisfy it:

```python
def render_all(blocks: list[Renderable]) -> str:
    """Render a sequence of content blocks into a single HTML string."""
    return "\n".join(block.render() for block in blocks)


output = render_all([MarkdownBlock("Hello world"), AlertBanner("Disk full", "error")])
print(output)
# <p>Hello world</p>
# <div class="alert-error">Disk full</div>
```

A static type checker like mypy or pyright verifies that every object in the list has a `render()` method returning `str`. If you pass an object that lacks the method, the type checker flags it *before* the code runs. No `isinstance` check needed. No ABC machinery. Just structural compatibility.

---

### Composing Protocols: From Atoms to Molecules

Real-world functions often need more than one capability. A table-of-contents generator needs content that is both renderable *and* measurable. Instead of creating a wide `ContentBlock` protocol with both methods, compose two narrow protocols:

```python
from typing import Protocol


class Renderable(Protocol):
    def render(self) -> str: ...


class Measurable(Protocol):
    def word_count(self) -> int: ...


class Exportable(Protocol):
    def export(self, format: str) -> bytes: ...
```

Three protocols, three capabilities, completely independent. A function that needs two of them declares the intersection:

```python
class RenderableAndMeasurable(Renderable, Measurable, Protocol):
    """Content that can be both rendered and measured."""
    ...
```

This derived protocol inherits method declarations from both parents. Any class that implements `render()` and `word_count()` satisfies it — again, without inheriting from anything:

```python
class ArticleBlock:
    def __init__(self, title: str, body: str) -> None:
        self._title = title
        self._body = body

    def render(self) -> str:
        return f"<article><h2>{self._title}</h2><p>{self._body}</p></article>"

    def word_count(self) -> int:
        return len(self._body.split())


def build_toc_entry(block: RenderableAndMeasurable) -> str:
    """Generate a table-of-contents line with word count."""
    preview = block.render()[:80]
    return f"{preview}... ({block.word_count()} words)"


entry = build_toc_entry(ArticleBlock("Protocols", "Narrow protocols are powerful"))
print(entry)
# <article><h2>Protocols</h2><p>Narrow protocols are powerful</p></article>... (4 words)
```

The composed protocol did not add any new methods. It simply combined existing ones. This is the molecule-from-atoms pattern: build narrow protocols for individual capabilities, then compose them when a function needs multiple capabilities. Each atom remains independently useful.

---

### Protocol vs ABC: When to Choose Which

Protocols and ABCs both define interfaces, but they solve different problems.

**Protocols** are structural. A class satisfies a protocol if it has the right methods — no inheritance link needed. This makes protocols ideal for type-checking code you do not control: third-party libraries, standard library types, legacy classes. Protocols carry no runtime cost and impose no coupling.

**ABCs** are nominal. A class satisfies an ABC by explicitly inheriting from it or registering with it. This makes ABCs ideal when you need **concrete mixin methods** — shared behavior that subclasses inherit for free. The `collections.abc.MutableSequence` ABC provides `append()`, `extend()`, `pop()`, and more. A protocol cannot do this because there is no inheritance relationship to carry behavior.

The decision rule: if you need to **enforce method existence** without providing shared implementation, use a Protocol. If you need to **provide shared behavior** through concrete mixin methods, use an ABC. Most interface-only contracts — especially narrow ones — belong as Protocols.

---

### The Gotcha: @runtime_checkable Has Limits

Protocols are primarily a static type-checking tool. But Python offers `@runtime_checkable` to enable `isinstance` checks at runtime:

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str: ...
```

```python
block = MarkdownBlock("test")
print(isinstance(block, Renderable))  # True
```

This looks convenient, but it has the same limitation as ABC-based `isinstance` checks: it verifies method **existence**, not **signatures**. A class with a `render()` method that takes three parameters and returns an `int` will still pass the check:

```python
class Broken:
    def render(self, width: int, height: int) -> int:
        return width * height


print(isinstance(Broken(), Renderable))  # True — wrong signature, but method exists
```

Two additional caveats. First, `@runtime_checkable` is not inherited — if you compose a new protocol from a runtime-checkable parent, you must apply the decorator again on the derived protocol. Second, runtime-checkable protocols cannot check data attributes or properties, only methods.

Use `@runtime_checkable` for lightweight guards at system boundaries. Rely on static type checkers for thorough signature verification.

---

### Naming Conventions: The Typeshed Standard

Python's typeshed repository — the source of type stubs for the standard library — established naming conventions for protocols that have become community practice:

**Plain names** for protocols that represent well-known concepts: `Iterator`, `Container`, `Sequence`. These map to established patterns with long histories.

**`SupportsX`** for protocols that require callable methods: `SupportsInt`, `SupportsFloat`, `SupportsComplex`. The name signals "this object can be converted to X" or "this object supports the X operation."

**`HasX`** for protocols that require readable or writable attributes: `HasFileno`, `HasItems`. The name signals "this object exposes attribute X."

For your own protocols, follow the same pattern. A single-method protocol for rendering is `Renderable`. A protocol requiring a `word_count()` method is `Measurable` or `SupportsWordCount`. A protocol requiring a `.metadata` attribute is `HasMetadata`. Consistent naming makes protocol purpose immediately clear from the type hint alone.

---

### Conclusion

The Go community learned through a decade of practice that narrow interfaces compose better than wide ones. Python's `typing.Protocol` brings this philosophy to a dynamically typed language, giving you structural contracts that require no inheritance, no registration, and no runtime cost.

Start with the smallest useful protocol — one method, one capability. Compose wider contracts by combining narrow protocols through inheritance. Let static type checkers verify conformance, and reach for `@runtime_checkable` only when you need a lightweight guard at a system boundary.

The result is code where each function declares exactly the capabilities it needs, each class implements exactly the capabilities it provides, and no object is forced to carry methods it will never use. That is the Interface Segregation Principle in practice — and it starts with keeping your protocols narrow.
