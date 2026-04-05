# The Hashable Contract: Implementing __eq__ and __hash__ Correctly
#### Understanding the deep relationship between object identity, value equality, and dictionary performance in Python

**By Tihomir Manushev**  
*Jan 5, 2026 · 7 min read*

---

Every intermediate Python developer eventually encounters the dreaded `TypeError: unhashable type`. Usually, this happens when you attempt to place a list inside a set or use a `dict` as a key for another dict.

We intuitively understand why a list is unhashable: its contents can change. But when we build our own custom classes, the rules become murky. By default, user-defined objects are hashable, but they compare based on identity (memory address), not value. The moment you implement `__eq__` to give your object meaningful value comparisons, you inadvertently break its hashability.

This relationship between equality and hashing is not an implementation detail; it is a strict contract enforced by the Python interpreter. Violating it leads to subtle bugs, silent data loss, and dictionary lookups that return `KeyError` for keys that clearly exist.

In this deep dive, we will explore the mechanics of Python’s hash tables, the mathematical contract binding `__eq__` and `__hash__`, and how to implement robust, immutable value objects that play nicely with Python’s data model.

---

### The Mechanics of the Hash Map

To understand the contract, we must look briefly at CPython’s internals. Both `set` and `dict` are implemented as hash tables.

When you write `my_dict[key] = value`, Python performs the following steps:

1.  It calls `hash(key)` to generate a large integer.
2.  It uses a masking operation (essentially modulo) on that integer to find a specific “bucket” (index) in the underlying C array.
3.  If the bucket is empty, it stores the key and value there.

However, collisions are inevitable. Two different objects might yield the same hash (or at least map to the same bucket). When a collision occurs, Python uses a strategy called open addressing to find the next available slot.

This brings us to the retrieval step (`value = my_dict[key]`). Python cannot simply look at the hash; it must verify that the object in the bucket is actually the one you are looking for. It does this by checking for equality.

Therefore, the lookup algorithm logic is roughly:

1.  Calculate the hash of the query key.
2.  Jump to the corresponding bucket.
3.  **Check 1:** Do the hashes match?
4.  **Check 2:** Does `stored_key == query_key`?

If you mess up step 1, step 4 never happens.

---

### The Golden Rule

The dependency described above leads us to the Hashable Contract:

> **If `a == b`, then `hash(a)` must equal `hash(b)`.**

The inverse does not have to be true (hash collisions are permitted), but the forward implication is non-negotiable.

If two objects compare as equal but generate different hash values, they will map to different buckets. You will put an object into a set, check if it’s there using an identical instance, and Python will tell you `False`.

---

### The Trap of Mutability

Why does Python prevent lists from being hashed? Because of the bucket problem.

If an object is mutable, and you modify it after inserting it into a dictionary, its hash value would theoretically change (if the hash is based on its values). However, the object is already sitting in a specific bucket based on the old hash. When you try to look it up again, Python calculates the new hash, looks in a new bucket, finds nothing, and raises a `KeyError`.

Your object is now lost inside the dictionary — a “zombie” entry that takes up memory but can never be retrieved.

To prevent this, production-grade hashable objects should be immutable.

---

### The Broken Implementation

Let’s look at a custom class representing a connection configuration. We want two configurations to be equal if their IP and Port are the same.

```python
class ConnectionConfig:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConnectionConfig):
            return NotImplemented
        return self.ip == other.ip and self.port == other.port

    def __repr__(self) -> str:
        return f"ConnectionConfig(ip='{self.ip}', port={self.port})"

# --- Testing the implementation ---

c1 = ConnectionConfig("192.168.1.10", 8080)
c2 = ConnectionConfig("192.168.1.10", 8080)

print(f"Equality check: {c1 == c2}") 

try:
    config_set = {c1, c2}
except TypeError as e:
    print(f"Error: {e}")
```

When we implemented `__eq__`, Python detected that we defined custom equality logic. Since the default `__hash__` implementation relies on object identity (memory address), keeping it would violate the Golden Rule (two equal objects would have different memory addresses and thus different hashes).

To protect us, Python effectively sets `ConnectionConfig.__hash__ = None`.

---

### Best Practice Implementation: Immutability and XOR

To fix this, we need to:

1.  Make the object immutable so the hash remains stable over its lifetime.
2.  Implement `__hash__` to return an integer derived from the components used in `__eq__`.

The standard way to combine hash values of multiple attributes is to mix them using the XOR operator (`^`) or, more simply, by hashing a tuple of the components.

Here is the robust, production-ready implementation:

```python
from typing import Any

class ImmutableConnection:
    __slots__ = ('_ip', '_port')  # Optimization: saves memory

    def __init__(self, ip: str, port: int):
        # We simulate immutability by using "private" attributes
        # and not providing setters.
        self._ip = ip
        self._port = port

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    def __eq__(self, other: Any) -> bool:
        """
        Check value equality based on IP and Port.
        """
        if not isinstance(other, ImmutableConnection):
            # Returning NotImplemented lets Python try the reverse comparison
            return NotImplemented
        return self.ip == other.ip and self.port == other.port

    def __hash__(self) -> int:
        """
        Compute a hash based on the tuple of components.
        This ensures that if a == b, hash(a) == hash(b).
        """
        return hash((self.ip, self.port))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(ip='{self.ip}', port={self.port})"

# --- Verification ---

conn1 = ImmutableConnection("10.0.0.1", 22)
conn2 = ImmutableConnection("10.0.0.1", 22)
conn3 = ImmutableConnection("10.0.0.5", 80)

# 1. Verification of Equality
assert conn1 == conn2
assert conn1 != conn3

# 2. Verification of Hashing
# They are distinct objects in memory...
assert conn1 is not conn2
# ...but they share the same hash.
assert hash(conn1) == hash(conn2)

# 3. Usage in Sets
server_registry = {conn1, conn3}
print(f"Set size: {len(server_registry)}") 

# Adding the 'duplicate' conn2 does not increase the size
server_registry.add(conn2)
print(f"Set size after adding duplicate: {len(server_registry)}")

# 4. Immutability Check
try:
    conn1.port = 443
except AttributeError:
    print("Correctly raised AttributeError: can't set attribute")
```

#### Implementation Details Explained

*   **The Read-Only Properties:** We used `@property` decorators and stored the actual data in `_ip` and `_port`. We did not implement setters. While Python cannot strictly enforce privacy, this signals to other developers (and the IDE) that these attributes should not be changed. This stability is crucial for the object to remain findable in a hash map.
*   **The `__hash__` Method:** We used `hash((self.ip, self.port))`. This delegates the complexity of mixing bits to the tuple class, which has a highly optimized C implementation for combining hashes. Alternatively, you might see manual XOR implementations like: `return hash(self.ip) ^ hash(self.port)`. While XOR is fast, the tuple approach is generally preferred because it handles symmetry better (e.g., distinguishing between `(1, 2)` and `(2, 1)`).
*   **`__eq__` Safety:** Notice the `isinstance` check. If we compare our object to a `str` or `int`, we return `NotImplemented` rather than `False`. This is a polite way of telling the Python interpreter: “I don’t know how to compare myself to this type; ask the other object if it knows how to compare itself to me.” If both return `NotImplemented`, Python falls back to `False`.

---

### The Modern Approach: Data Classes

Modern Python (3.7+) offers a shortcut that handles this boilerplate correctly: `dataclasses`.

If you need a hashable value object, using `@dataclass(frozen=True)` is often the superior architectural choice.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ModernConnection:
    ip: str
    port: int

# Python automatically generates:
# 1. __init__
# 2. __repr__
# 3. __eq__ (checking all fields)
# 4. __hash__ (because frozen=True)
```

By setting `frozen=True`, the dataclass mimics the manual implementation we wrote above: it makes instances immutable and generates a `__hash__` method based on the class fields.

---

### Conclusion

The interaction between `__eq__` and `__hash__` is a fundamental pillar of the Python Data Model. It is a system designed to balance the flexibility of dynamic types with the performance rigidity of C-based hash tables.

When defining custom objects, remember that you are defining the identity of your data. If your object represents a value (like a database connection string, a complex number, or a vector) rather than a stateful entity, implement value equality. But remember the contract: if you implement equality, you must implement hashing, and if you implement hashing, you must enforce immutability.

Failure to adhere to this contract results in the most frustrating kind of bugs — the ones where the data is staring you in the face, but Python refuses to see it.
