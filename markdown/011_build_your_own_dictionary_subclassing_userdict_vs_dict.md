# Build Your Own Dictionary: Subclassing UserDict vs. dict
#### The Right Way to Build Custom Dictionaries in Python

**By Tihomir Manushev**  
*Oct 25, 2025 · 7 min read*

---

Ever found yourself wishing a Python dictionary had just one more trick up its sleeve? Maybe you need keys to be case-insensitive. Perhaps you want to log every time a value is set. Or maybe, like in our example today, you want a dictionary that gracefully handles keys of different types by converting them all to strings.

If you’ve dipped your toes into object-oriented programming, your first instinct is probably to reach for inheritance. It feels natural, right?

```python
class MyAwesomeDict(dict):
    # ... my awesome code here ...
    pass
```

This seems like the most straightforward path. You want something that acts like a dictionary, so you inherit from `dict`. But be warned, this path is fraught with peril. The built-in `dict` is a highly optimized, C-level powerhouse, and its implementation contains shortcuts that can make subclassing a frustrating and bug-prone experience.

There is a better way. A safer, more Pythonic way, tucked away in the standard library: `collections.UserDict`.

In this article, we’ll go on a journey to build a custom dictionary, a `StrKeyDict`, that stores all its keys as strings. We’ll build it twice: once by subclassing the treacherous `dict`, and once using the elegant `UserDict`. By the end, you’ll not only understand how to build custom mappings but also grasp the deeper software design principle of why composition is often better than inheritance.

---

### The Tempting Trap: Inheriting Directly from dict

Our goal is simple: create a dictionary where any key provided is converted to a string. `my_dict[1]` should be the same as `my_dict['1']`, and `my_dict.get(2)` should work just fine if the key `'2'` exists.

Let’s start down the intuitive but dangerous path of subclassing `dict`.

We know we need to intercept key lookups. A clever way to handle missing keys is the special `__missing__` method. When you use bracket notation (`d[key]`), Python calls the internal `__getitem__` method. If `__getitem__` can’t find the key, it then makes a special, second-chance call to a method named `__missing__`, if it exists. This is our hook!

```python
# The "don't do this at home" example
class StrKeyDict0(dict):
    
    def __missing__(self, key):
        # If the key is missing, try its string version
        return self[str(key)]

    def __setitem__(self, key, item):
        # Store all keys as strings
        super().__setitem__(str(key), item)
```

This looks promising. When we set an item, we convert the key to a string. When we try to get an item and it’s missing, we try looking it up again, but this time using its string representation.

But watch what happens when we ask for a key that truly doesn’t exist, not even in its string form:

```python
d = StrKeyDict0()
d[1] = 'one'

print(d['1'])
print(d[1])  # Works via __missing__
print(d[2])  # Fails via __missing__
```

A `RecursionError`! Why? Let’s trace the execution:

1.  We call `d[2]`.
2.  Python’s `dict.__getitem__` doesn’t find the integer key `2`.
3.  It calls our `__missing__(2)`.
4.  Inside `__missing__`, we execute `self[str(2)]`, which is `self['2']`.
5.  This calls `dict.__getitem__` again, this time with the string key `'2'`.
6.  It doesn’t find `'2'`, so it calls our `__missing__('2')`.
7.  Inside this second call to `__missing__`, we execute `self[str('2')]`, which is still `self['2']`.
8.  Go back to step 5. We’re trapped in an infinite loop.

To fix this, we need to add a guard clause. We should only try the string conversion if the key isn’t already a string.

```python
# Still the "don't do this" example, but slightly fixed
class StrKeyDict0(dict):

    def __missing__(self, key):
        if isinstance(key, str):
            # If it's a string and it's missing, it's really missing.
            raise KeyError(key)
        # Otherwise, try its string version.
        return self[str(key)]

    def __setitem__(self, key, item):
        super().__setitem__(str(key), item)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
```

We’ve dodged the recursion error. But what about membership testing with the `in` operator?

```python
d = StrKeyDict0()
d[1] = 'one'

print('1' in d)
print(1 in d)
```

This is maddening! The `in` operator doesn’t trigger our `__missing__` logic. It turns out that `in` calls the `__contains__` method directly, and the default `dict` version has no reason to know about our clever `__missing__` hook. To get consistent behavior, we have to override `__contains__` as well.

```python
# Final "don't do this" version. It works, but look how much work it was.
class StrKeyDict0(dict):

    def __missing__(self, key):
        if isinstance(key, str):
            raise KeyError(key)
        return self[str(key)]

    def __contains__(self, key):
        # Check for the key as is, or its string version
        return key in self.keys() or str(key) in self.keys()

    def __setitem__(self, key, item):
        super().__setitem__(str(key), item)

    def get(self, key, default=None):
        # We also have to override get() to be consistent
        try:
            return self[key]
        except KeyError:
            return default
```

We finally have something that works, but it feels like we’ve been fighting the tool instead of using it. We had to know the intricate internal call order of `dict`, manually fix recursion, and override three separate methods (`__missing__`, `__contains__`, `get`) just to get consistent behavior. This is fragile. What if a future Python version changes how `dict` internals work? Our code could break.

This is the core problem with inheriting from complex, highly-optimized built-ins. You’re not just inheriting their public API; you’re inheriting their implementation details, warts and all.

---

### The Pythonic Path: Composition with UserDict

Let’s start over, but this time, let’s use the tool designed for this exact job: `collections.UserDict`.

Unlike `dict`, `UserDict` does not inherit from `dict`. Instead, it wraps a dictionary. It holds a regular `dict` instance inside an attribute called `data`. This is a classic example of composition over inheritance. Our class *has-a* dictionary; it isn’t *is-a* dictionary.

This small difference changes everything. It means we are completely in control of the public interface, and we can delegate the actual work to the internal `self.data` object without worrying about C-level trickery or recursive side effects.

Here is the entire implementation of `StrKeyDict` using `UserDict`:

```python
import collections

class StrKeyDict(collections.UserDict):
    
    def __missing__(self, key):
        # This implementation avoids recursion by directly accessing
        # the underlying data store.
        if isinstance(key, str):
            raise KeyError(key)
        return self.data[str(key)]

    def __contains__(self, key):
        # Membership testing is now trivial and safe.
        return str(key) in self.data

    def __setitem__(self, key, item):
        # We delegate the actual storage to the internal dict.
        self.data[str(key)] = item
```

Let’s break down why this is so much better:

*   **Simplicity in `__setitem__`**: Look at `__setitem__`. We aren’t calling `super()`. We are directly manipulating `self.data`, which is just a plain, boring `dict`. There’s no risk of weird side effects.
*   **Safety in `__contains__`**: Our `__contains__` method is now a single, readable line. We just check for the string version of the key in `self.data`. No recursion, no problem.
*   **Correctness in `__missing__`**: The `__missing__` implementation should perform the fallback lookup directly on the wrapped dictionary (`self.data`). Using `self.data[str(key)]` looks up the stringified key in the plain underlying dict and will raise `KeyError` if not found — exactly the correct behavior. If we instead used `self[str(key)]`, that would call the `StrKeyDict`'s `__getitem__` again and could re-enter `__missing__`, creating the same recursion problem we avoided when subclassing `dict`. Accessing `self.data` avoids that trap because `self.data` is an ordinary Python `dict` and does not call our `StrKeyDict` hooks.
*   **You Get Methods for Free**: The best part? `UserDict` is designed to be subclassed. Its own methods, like `update()` and `__init__`, are written in Python and are designed to call your overridden versions of `__setitem__`. The built-in `dict` often doesn’t do this; its internal C methods might modify the dictionary’s contents directly, bypassing your custom logic entirely. With `UserDict`, your rules are always respected.

Let’s test it.

```python
d = StrKeyDict()
d[1] = 'one'
print(d)

print(d[1]) # Works via __missing__

print(1 in d) # Works via our __contains__

print(d.get(2, 'default')) # .get() works without us overriding it!
```

It just works. The code is cleaner, safer, and more robust. We are working with the framework, not against it.

---

### The Deeper Lesson: Inheritance vs. Composition

What we’ve seen is a textbook case of the “composition over inheritance” principle.

*   **Inheritance (*is-a* relationship):** Our `StrKeyDict0` *was-a* `dict`. This created a very tight coupling. We inherited a massive, complex implementation and were forced to tiptoe around its internal optimizations.
*   **Composition (*has-a* relationship):** Our `StrKeyDict` *has-a* `dict` (its `self.data`). This is a much looser coupling. We define our own behavior and use the contained object as a simple storage engine. We delegate responsibility instead of inheriting it.

When you’re dealing with fundamental, highly-optimized built-in types in Python (like `dict`, `list`, or `str`), composition is almost always the safer and more maintainable choice. They weren’t originally designed with inheritance in mind, and the `collections.abc` module (which includes `UserDict`, `UserList`, and `UserString`) was created specifically to provide safe, wrappable alternatives for this purpose.

---

### Conclusion

The next time you feel the urge to create a custom, dictionary-like object, pause before you type `class MyDict(dict):`. Remember the struggles with recursion and the need to override multiple methods just to maintain consistency.

Instead, import the `collections` module and reach for `UserDict`. By favoring composition over inheritance in this context, you’ll write code that is not only simpler and more readable but also more robust and future-proof. It’s the Pythonic way to build the specialized tools you need without getting burned by the implementation details of the powerful primitives you’re building upon.