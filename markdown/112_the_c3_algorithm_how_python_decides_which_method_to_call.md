# The C3 Algorithm: How Python Decides Which Method to Call

#### C3 linearization turns a tangled inheritance graph into a single, deterministic lookup sequence — here is how it works, step by step

**By Tihomir Manushev**

*Mar 03, 2026 · 7 min read*

---

You define a class that inherits from two parents. Both parents share a common ancestor. Both override the same method. You create an instance and call that method. Which version runs?

If your answer involves depth-first search, you are thinking of Python 2.1 and earlier. If you said breadth-first, you are thinking of a language that is not Python. Since version 2.3, Python uses an algorithm called **C3 linearization**, originally published by Barrett, Cassels, Haahr, Moon, Playford, and Withington in 1996 for the Dylan programming language. C3 takes any valid inheritance graph and flattens it into a single ordered tuple — the **Method Resolution Order**, stored in every class's `__mro__` attribute. That tuple governs every `super()` call, every attribute lookup, and every `isinstance()` check for the lifetime of the class.

Without understanding C3, you cannot predict where `super()` will dispatch, cannot diagnose the dreaded `TypeError: Cannot create a consistent method resolution order`, and cannot design hierarchies that compose cleanly. This article walks through the algorithm by hand, shows when and why it rejects a hierarchy, and demonstrates a common gotcha that silently changes runtime behavior.

---

### The Diamond Problem in Sixty Seconds

The classic ambiguity in multiple inheritance is the **diamond problem**: a class inherits from two parents that share a common ancestor, forming a diamond shape in the inheritance graph. Without a well-defined resolution strategy, the runtime has no principled way to choose between two equally valid method implementations. Some languages ban this configuration entirely. Python embraces it — and relies on C3 to resolve the ambiguity deterministically.

Consider a game engine where every entity descends from a single base:

```python
class GameObject:
    """Base entity in the game world."""

    def update(self, delta_time: float) -> str:
        return "GameObject.update"


class Renderable(GameObject):
    """Adds drawing capability to an entity."""

    def update(self, delta_time: float) -> str:
        return "Renderable.update"


class Collidable(GameObject):
    """Adds physics collision to an entity."""

    def update(self, delta_time: float) -> str:
        return "Collidable.update"


class PlayerCharacter(Renderable, Collidable):
    """The player-controlled entity."""
    pass


hero = PlayerCharacter()
print(hero.update(0.016))
# Renderable.update
```

`PlayerCharacter` does not override `update`, yet calling it produces a definite answer: `Renderable.update`. This is not arbitrary, and it is not simply "the first parent wins." Python consulted the MRO that C3 computed at the moment `PlayerCharacter` was defined, found `Renderable` before `Collidable` in the flattened sequence, and dispatched there. With single inheritance, the MRO is trivial — a straight line from child to parent to `object`. With multiple inheritance, the graph branches and reconverges, and C3 must flatten it into a single path that respects every class's relationship to its ancestors. The rest of this article explains exactly how C3 produces that sequence.

---

### C3 Linearization, Step by Step

The C3 algorithm computes the linearization `L[C]` of a class `C` using a recursive formula:

```
L[C] = C + merge(L[B1], L[B2], ..., L[Bn], [B1, B2, ..., Bn])
```

`B1` through `Bn` are the base classes of `C`, listed in the order they appear in the `class` statement. The `merge` operation is where the real work happens.

**The merge rule:** scan the head (first element) of each input list from left to right. Pick the first head that does not appear in the *tail* (everything except the first element) of any other list. Append that class to the result, remove it from every list where it appears, and repeat until every list is empty. If at any step no valid head exists — every candidate appears in the tail of some other list — the linearization is impossible and Python raises a `TypeError`.

Why check the tails specifically? A class appearing in another list's tail means some other class must appear before it. Selecting it now would violate that ordering constraint. By only picking "safe" heads, C3 builds the linearization without ever contradicting a parent's existing commitments.

Let's compute `L[PlayerCharacter]` by hand. Start with the base cases:

```
L[GameObject] = [GameObject, object]
L[Renderable] = [Renderable] + merge([GameObject, object], [GameObject])
             = [Renderable, GameObject, object]
L[Collidable] = [Collidable] + merge([GameObject, object], [GameObject])
             = [Collidable, GameObject, object]
```

Now the interesting one:

```
L[PlayerCharacter] = [PlayerCharacter] + merge(
    [Renderable, GameObject, object],   # L[Renderable]
    [Collidable, GameObject, object],   # L[Collidable]
    [Renderable, Collidable]            # base class list
)
```

**Step 1:** Heads are `Renderable`, `Collidable`, `Renderable`. Check `Renderable` — does it appear in the tail of any list? The tails are `[GameObject, object]`, `[GameObject, object]`, and `[Collidable]`. No. Pick `Renderable`, remove it everywhere:

```
merge([GameObject, object], [Collidable, GameObject, object], [Collidable])
```

**Step 2:** Heads are `GameObject`, `Collidable`, `Collidable`. Check `GameObject` — it appears in the tail `[GameObject, object]` of the second list. Skip it. Check `Collidable` — tails are `[object]`, `[GameObject, object]`, and `[]`. Not found in any tail. Pick `Collidable`, remove it:

```
merge([GameObject, object], [GameObject, object])
```

**Step 3:** Head is `GameObject`. Only tail is `[object]` in both lists. Not found. Pick `GameObject`:

```
merge([object], [object])
```

**Step 4:** Pick `object`. All lists are empty. Done.

The final result:

```
L[PlayerCharacter] = [PlayerCharacter, Renderable, Collidable, GameObject, object]
```

Verify in Python:

```python
print([cls.__name__ for cls in PlayerCharacter.__mro__])
# ['PlayerCharacter', 'Renderable', 'Collidable', 'GameObject', 'object']
```

C3 guarantees two invariants. First, **monotonicity**: a child always appears before its parents. If `Renderable` inherits from `GameObject`, then `Renderable` will always precede `GameObject` in the MRO of any class that includes both. Second, **local precedence**: the left-to-right order of bases in the `class` statement is preserved. `Renderable` was listed before `Collidable` in `class PlayerCharacter(Renderable, Collidable)`, so `Renderable` precedes `Collidable` in the MRO. These two constraints, combined with the requirement that shared ancestors appear only after all their descendants, make the linearization unique and deterministic for any given set of class definitions.

---

### When C3 Refuses to Linearize

C3 is not just an ordering algorithm — it is also a validator. Some inheritance graphs are impossible to linearize without violating the invariants, and Python raises a `TypeError` at class definition time rather than silently producing a wrong order.

```python
class AudioSource(GameObject):
    """Produces game audio."""
    pass


class SpatialAudio(AudioSource, Collidable):
    """Audio with 3D positioning derived from collision bounds."""
    pass
```

`SpatialAudio` linearizes cleanly: its MRO places `AudioSource` before `Collidable`. Now try to build a class that lists `Collidable` *before* `SpatialAudio`:

```python
try:
    class BrokenEntity(Collidable, SpatialAudio):
        pass
except TypeError as exc:
    print(exc)
# Cannot create a consistent method resolution order (MRO)
# for bases Collidable, SpatialAudio
```

The merge fails because `BrokenEntity` demands `Collidable` before `SpatialAudio` (local precedence), but `SpatialAudio.__mro__` already commits to `AudioSource` before `Collidable`. Placing `Collidable` first would violate `SpatialAudio`'s existing linearization. Every remaining head appears in the tail of another list — the algorithm deadlocks, and Python rejects the class before a single instance is created.

This is a feature, not a limitation. A silently incorrect MRO would cause methods to dispatch to the wrong implementation at runtime — a bug that is far harder to find than a `TypeError` at import time. C3's strictness catches contradictory designs early.

The fix is almost always the same: reorder the bases so the more specialized class comes first. `class FixedEntity(SpatialAudio, Collidable)` works because it respects the ordering commitments that `SpatialAudio` has already made.

---

### The Gotcha: Base Order Changes Everything

Many developers treat the order of base classes in a `class` statement as cosmetic — like alphabetizing imports. It is not. Swapping the order changes the MRO and therefore changes which method wins at runtime:

```python
class RenderFirst(Renderable, Collidable):
    """Renderable listed first."""
    pass


class CollideFirst(Collidable, Renderable):
    """Collidable listed first."""
    pass


print([c.__name__ for c in RenderFirst.__mro__])
# ['RenderFirst', 'Renderable', 'Collidable', 'GameObject', 'object']

print([c.__name__ for c in CollideFirst.__mro__])
# ['CollideFirst', 'Collidable', 'Renderable', 'GameObject', 'object']

print(RenderFirst().update(0.016))
# Renderable.update

print(CollideFirst().update(0.016))
# Collidable.update
```

The only difference between these two classes is the order of bases in the `class` statement. The MRO flips, and so does the runtime behavior. `RenderFirst` uses `Renderable.update`; `CollideFirst` uses `Collidable.update`. A refactor that reorders bases "for readability" or "alphabetical consistency" silently changes which methods get called. If your tests do not cover the affected methods, the bug ships unnoticed.

This is the most common source of subtle bugs in multiple inheritance hierarchies. A developer adds a new base class, another developer reorders the bases during code review, and suddenly an entirely different method implementation is active in production.

Treat the order of bases as a **semantic choice**. When a class inherits from multiple parents that override the same method, the first base listed takes priority. Document the intent with a comment when it matters, and write tests that verify which implementation is active.

---

### Inspecting the MRO at Runtime

Python provides two ways to examine the MRO. The `__mro__` attribute is a tuple, computed once when the class is created and cached permanently. The `.mro()` method returns a fresh list each time — useful if you need a mutable copy, but the data is identical.

```python
def show_mro(cls: type) -> None:
    """Print the MRO of a class as a readable chain."""
    chain = " -> ".join(c.__name__ for c in cls.__mro__)
    print(f"{cls.__name__}: {chain}")


show_mro(PlayerCharacter)
# PlayerCharacter: PlayerCharacter -> Renderable -> Collidable -> GameObject -> object

show_mro(SpatialAudio)
# SpatialAudio: SpatialAudio -> AudioSource -> Collidable -> GameObject -> object

# __mro__ is a tuple; .mro() returns a list — same data, different container
assert PlayerCharacter.__mro__ == tuple(PlayerCharacter.mro())
```

A useful debugging technique is comparing the MRO of two classes that you expect to behave differently. If `show_mro(ClassA)` and `show_mro(ClassB)` produce the same sequence for the classes you care about, they will dispatch identically for those methods — regardless of how different their inheritance graphs look.

One performance detail worth knowing: C3 runs at class creation time, not at method dispatch time. The algorithm is O(n²) in the number of classes in the hierarchy, but it executes exactly once per class definition. After that, every `super()` call and every attribute lookup walks the cached `__mro__` tuple — a simple linear scan with zero algorithmic overhead. You pay the cost of C3 when the class is defined, and never again.

---

### Conclusion

Python does not use depth-first search, breadth-first search, or any ad hoc rule to resolve method calls in multiple inheritance. It uses C3 linearization — an algorithm that merges the linearizations of all parent classes into a single, deterministic tuple stored in `__mro__`. Two hard constraints drive every decision: children appear before parents, and the left-to-right order of bases in the `class` statement is preserved. Any hierarchy that makes these constraints contradictory is rejected at class definition time with a `TypeError`.

The order of base classes is not cosmetic. Swapping two bases changes the MRO and changes which method runs. Treat base ordering as a design decision, test the methods it affects, and inspect `__mro__` when the dispatch surprises you. Once you can trace the merge algorithm by hand, multiple inheritance stops being a source of mystery and becomes a tool you control.
