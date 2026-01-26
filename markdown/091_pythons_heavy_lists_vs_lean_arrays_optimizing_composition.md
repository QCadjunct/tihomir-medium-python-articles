# Python’s Heavy Lists vs. Lean Arrays: Optimizing Composition
#### Leveraging C-Style Arrays and Protocol Composition for High-Performance Python Collections

**By Tihomir Manushev**  
*Jan 19, 2026 · 6 min read*

---

One of Python’s greatest strengths — its “everything is an object” philosophy — is also one of its most treacherous performance pitfalls. We often default to the list as our primary data structure for collections. It is flexible, ubiquitous, and easy to use. However, when building custom data structures meant to hold millions of numerical values — such as high-frequency trading tickers, telemetry sensor logs, or vector embeddings — composition using a standard list is a memory catastrophe waiting to happen.

In this article, we will explore why Python lists are surprisingly heavy, how the standard library’s array module offers a C-efficient alternative, and how to compose a sequence class that leverages contiguous memory for massive efficiency gains.

---

### The Hidden Cost of “Everything is an Object”

To understand why we need `array`, we must first understand the anatomy of a list.

When you write `data = [1.0, 2.0, 3.0]`, you are not creating a contiguous block of three floats in memory (like a C array or a Fortran vector). You are creating a dynamic array of pointers.

*   **The List Head:** The list object itself contains its size, its allocated capacity, and a pointer to an array of object references.
*   **The References:** This internal array contains pointers (memory addresses) to other Python objects.
*   **The Objects:** Each float value (e.g., `1.0`) is a full-blown `PyFloatObject`. This structure contains:
    *   `ob_refcnt`: An integer for reference counting (Garbage Collection).
    *   `ob_type`: A pointer to the float type object.
    *   `ob_fval`: The actual C double holding the value.

On a standard 64-bit CPython build, a single float object consumes 24 bytes. The pointer in the list consumes another 8 bytes. This means every single number in your sequence costs 32 bytes of overhead, minimum. Furthermore, because these `PyFloatObject` instances are allocated on the heap individually, they are scattered across memory. Iterating over a large list causes CPU cache misses because the data is not spatially local.

---

### The array Module: Contiguous Memory in Python

The `array` module is often overlooked, yet it provides exactly what high-performance architectures need: a thin Python wrapper around a raw C array.

When you create an `array('d', [1.0, 2.0])`, Python allocates a single contiguous block of memory. It stores the raw 64-bit IEEE 754 double-precision floats directly in that block. There are no `PyFloatObject` wrappers for the elements stored inside.

*   **Memory Footprint:** 8 bytes per item.
*   **Cache Locality:** Excellent (sequential memory access).
*   **Overhead:** Negligible.

We can achieve a 4x memory reduction simply by swapping the backing store of our custom classes from `list` to `array`.

---

### The SensorBuffer Class

Let’s implement a production-grade custom sequence type designed to hold sensor telemetry data. We will use Composition — holding an array as a private attribute — rather than Inheritance. Inheriting from built-ins is generally discouraged because of the method resolution quirks in CPython. Instead, we will implement the `Sequence` protocol.

We will use `array` to store the data, ensuring our class remains lightweight even when holding millions of readings.

---

### The Implementation

Here is how we compose a memory-efficient sequence in Python 3.10+.

```python
import array
from collections.abc import Sequence
from typing import Iterator, Union, overload

class SensorBuffer(Sequence):
    """
    A memory-efficient, immutable sequence for high-frequency 
    sensor readings, backed by a C-style array.
    """
    
    # 'd' is the type code for double-precision float (8 bytes)
    TYPE_CODE = 'd'

    __slots__ = ('_buffer',)

    def __init__(self, data: Union[Sequence[float], 'SensorBuffer']):
        """
        Initialize the buffer from an iterable of numbers.
        Using array ensures we store raw doubles, not Python objects.
        """
        self._buffer = array.array(self.TYPE_CODE, data)

    def __len__(self) -> int:
        return len(self._buffer)

    @overload
    def __getitem__(self, index: int) -> float: ...

    @overload
    def __getitem__(self, index: slice) -> 'SensorBuffer': ...

    def __getitem__(self, index: Union[int, slice]) -> Union[float, 'SensorBuffer']:
        """
        Retrieve items. If a slice is requested, return a new SensorBuffer
        instance instead of a plain array or list.
        """
        if isinstance(index, slice):
            # Delegate slicing to the underlying array, then wrap it
            return self.__class__(self._buffer[index])
        
        # Return the specific float value
        return self._buffer[index]

    def __iter__(self) -> Iterator[float]:
        """Delegate iteration to the efficient underlying array."""
        return iter(self._buffer)

    def __repr__(self) -> str:
        """
        Provide a concise representation. 
        For massive buffers, we shouldn't print everything.
        """
        cls_name = self.__class__.__name__
        if len(self) > 10:
            sample = list(self._buffer[:10])
            return f'<{cls_name} first=10 items={sample} ... len={len(self)}>'
        return f'<{cls_name} items={list(self._buffer)}>'

    def __eq__(self, other: object) -> bool:
        """
        Efficient equality check. 
        Arrays support value equality optimization in C.
        """
        if isinstance(other, SensorBuffer):
            return self._buffer == other._buffer
        return NotImplemented
```

*   **Composition:** We hold `self._buffer` as a private attribute. By defining `__slots__ = ('_buffer',)`, we prevent the creation of a `__dict__` for the instance, saving even more RAM per `SensorBuffer` instance.
*   **Protocol Adherence:** By implementing `__len__` and `__getitem__`, our class behaves exactly like a list. Users can use `buffer[0]`, `buffer[:5]`, or `for x in buffer`.
*   **Slicing Awareness:** Notice the `__getitem__` implementation. A naive implementation would return the raw array or a list when sliced. To maintain the object-oriented design, when the user asks for a slice, we wrap the result back into a new `SensorBuffer`. This ensures the type remains consistent throughout the pipeline.

---

### Zero-Copy Serialization

One of the most powerful features of using `array` in composition is the ability to interact with binary interfaces. If you are sending this data over a network or saving it to disk, pickling a list is slow and produces large files.

Because `array` holds contiguous bytes, we can dump the memory directly. Let’s extend our class to support fast binary serialization and deserialization using `memoryview`.

```python
    def to_bytes(self) -> bytes:
        """Dump the raw memory content to a bytes object."""
        return self._buffer.tobytes()

    @classmethod
    def from_bytes(cls, raw_data: bytes) -> 'SensorBuffer':
        """
        Zero-copy reconstruction from raw bytes.
        
        This uses memoryview to cast the bytes directly to the 
        target type without intermediate copying.
        """
        # Create a memoryview of the raw bytes (zero-copy)
        mem_view = memoryview(raw_data)
        
        # Cast the bytes to the correct format code (e.g., 'd' for doubles)
        # This treats the byte stream as an array of doubles
        cast_view = mem_view.cast(cls.TYPE_CODE)
        
        # Initialize the class with the cast view
        return cls(cast_view)
```

In `from_bytes`, we see a pattern that distinguishes senior engineers from the rest: the use of `memoryview`.

If we simply passed `raw_data` into a parser, Python might copy that data multiple times. By using `memoryview(raw_data).cast('d')`, we are telling the interpreter: “Look at this chunk of memory. Do not move it. Do not copy it. Just treat every 8 bytes as a double-precision float.”

This allows us to instantiate a `SensorBuffer` containing 100 million items from a binary file almost instantly, limited only by disk I/O speed, with zero CPU overhead for parsing numbers.

---

### When to use numpy?

A common counter-argument to using `array` is: “Why not just use NumPy?”

This is a valid question. If you need to perform vector algebra (dot products, matrix multiplication, broadcasting), NumPy is absolutely the correct tool. However, NumPy introduces a heavy dependency. It compiles complex C/Fortran extensions and significantly increases the size of your deployment artifacts (Docker images, AWS Lambda layers).

If your goal is simply data storage, transport, and sequential access — acting as a buffer or a container — the standard library’s `array` module is superior. It is built-in, lightweight, and requires no external dependencies. It strictly adheres to the “Pythonic” sequence protocol, whereas NumPy arrays have their own non-standard behavior (e.g., how they handle boolean evaluation).

---

### Conclusion

Efficiency in Python is often about knowing what happens under the hood. The list is a general-purpose tool optimized for flexibility, not storage density. By composing your custom collection classes around the `array` module, you strip away the massive overhead of `PyObject` wrappers and pointer indirection.

The result is a class that quacks like a duck (behaves like a sequence) but runs like a Ferrari (C-array performance). When you combine this with `__slots__` and `memoryview` based serialization, you create robust, production-ready data structures capable of handling data scales that would otherwise choke the Python interpreter.
