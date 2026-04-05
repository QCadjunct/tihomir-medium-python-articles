# What Makes a Dictionary Key? A Deep Dive into Hashability
#### Why [1, 2] can’t be a dictionary key, but (1, 2) can.

**By Tihomir Manushev**  
*Oct 24, 2025 · 8 min read*

---

Ever been tripped up by a `TypeError: unhashable type: ‘list’`? You have a dictionary, you try to use a list as a key, and Python throws its hands up in protest. But then, you swap the list’s square brackets for a tuple’s parentheses, and suddenly, everything works perfectly.

```python
my_data = {}
a_list = [1, 2, 3]
a_tuple = (1, 2, 3)

# This works just fine!
my_data[a_tuple] = "This is the value"

# But this will crash and burn...
# my_data[a_list] = "This will raise a TypeError"
# TypeError: unhashable type: 'list'
```

This isn’t some arbitrary rule or a syntax quirk. It’s a direct consequence of the brilliant design that makes Python’s dictionaries one of the most efficient and powerful data structures in any programming language. The secret lies beneath the surface, in a concept called a **hash table**, and the ticket required to play is something called **hashability**.

Understanding hashability is like learning how the engine in your car works. You don’t need it for a short trip to the store, but knowing it will make you a much better driver — and a much better programmer. Let’s lift the hood and see what’s really going on.

---

### The Magic of the Hash Table: A Library Analogy

Imagine you’re in a library the size of a city, with millions of books. There’s no catalog and no Dewey Decimal System. The librarian tells you, “To find the book you want, you have to start at the first aisle and check every single shelf until you find it.”

This is how a Python list works when you search for an item. The `in` operator has to potentially scan every element one by one. For a list with ten items, it’s instant. For ten million items, it’s a nightmare.

Now, imagine a different, magical library. You walk up to the librarian and say, “I’m looking for Moby Dick.” The librarian doesn’t search for it. Instead, they perform a special calculation on the title — a “hash function” — and instantly tell you, “Go to Building 7, Aisle 3, Shelf 5.” You walk directly to the spot, and there’s your book.

This is a hash table, and it’s the engine that powers Python’s `dict`s and `set`s. It provides an almost instantaneous way to look up information.

*   **The key** is the book’s title (‘Moby Dick’).
*   **The value** is the book itself (the data you want to store).
*   **The hash function** is the librarian’s special calculation.
*   **The hash code** (or hash value) is the resulting location (Building 7, Aisle 3, Shelf 5).

This is why dictionary lookups are considered to be **O(1)**, or “constant time.” The size of the dict has almost no impact on the time it takes to find a single key. It’s a direct flight, not a cross-country road trip.

But for this magical system to work, the keys — the book titles — must follow two very strict, non-negotiable rules. These are the two golden rules of hashability.

---

### The Two Golden Rules of Hashability

An object is considered “hashable” if it satisfies both of these conditions. If it violates even one, Python will refuse to let it be a dict key.

#### Rule #1: A Hash Code Must Be Constant

An object’s hash code must never, ever change during its lifetime.

Think back to our library. You use the key ‘Project Plan’ to store a document. The hash function calculates a location, and Python places your document there.

Now, imagine that key was a list: `project_plan = [‘Step 1: Research’, ‘Step 2: Develop’]`. You use this list as a key. Python hashes it and stores your value.

```python
# Fictional code - this doesn't actually work!
project_plan = ['Step 1: Research', 'Step 2: Develop']
my_docs = {}
# Python hashes the list's current state and stores the value
my_docs[project_plan] = 'Top Secret Document'
```

But what happens when the plan changes? You modify the list in place.

```python
# Now, let's change the key itself
project_plan.append('Step 3: Profit!')
# The list is now ['Step 1: Research', 'Step 2: Develop', 'Step 3: Profit!']
```

The key has changed! If you now try to look up `my_docs[project_plan]`, Python will run the hash function on the new list content. This will produce a completely different hash code and point to a different, empty shelf in the library. Your original document is now lost forever, stranded in a part of the dictionary you can no longer reach.

This is the core reason why mutable objects cannot be hashable. Their value can change, which means their hash code would change, and the entire hash table system would collapse into chaos.

This explains our original problem:

*   **Lists, dictionaries, and sets** are mutable, so they are not hashable.
*   **Integers, strings, booleans, and floats** are immutable, so they are hashable.
*   **Tuples** are immutable containers, so they are generally hashable.

#### Rule #2: Equal Objects Must Have Equal Hashes

The second rule is just as important: if two objects are considered equal, they must have the same hash code.

In Python, this means: if `a == b` is True, then `hash(a) == hash(b)` must also be True.

This rule is essential for making lookups work correctly. For example, the integer `100` and the float `100.0` are considered equal in Python.

```python
print(100 == 100.0)
# Output: True
```

Because of Rule #2, Python guarantees they will have the same hash.

```python
print(hash(100))
print(hash(100.0))
# Output: (Same hash code)
```

Why does this matter? It allows the dict to treat them as the same key. You can store a value using the integer and retrieve it using the float, and it works seamlessly.

```python
price_info = {}
price_info[100] = 'One Hundred Dollars'

# Because hash(100) == hash(100.0), Python looks in the same spot!
print(price_info[100.0])
```

If they had different hashes, the dictionary would be inconsistent and unpredictable. The `__eq__` method (which powers the `==` operator) serves as the final check. If two different keys happen to have the same hash code (a “hash collision”), Python uses `==` to see if the key stored on that shelf is truly the one you’re looking for.

---

### Hashability in Practice: The Dos and Don’ts

Let’s summarize which common types you can and can’t use as keys.

#### Hashable (The “Dos”):

*   `int`, `float`, `complex`, `bool`, `str`, `bytes`
*   `None`
*   `frozenset`: The immutable version of a set.
*   `tuple`: **But with a big caveat!** A tuple is only hashable if every single element inside it is also hashable.

This last point is a common gotcha. A tuple containing a list is not hashable.

```python
# This is hashable: a tuple of strings and integers
location = ('USA', 'California', 34.0522)
print(hash(location)) # Works!

# This is NOT hashable: a tuple containing a list
bad_key = ('USA', 'California', ['Los Angeles', 'San Francisco'])
print(hash(bad_key))
```

The `TypeError` comes from the list buried deep inside the tuple. The moment Python’s hash function encounters that list, it stops.

#### Unhashable (The “Don’ts”):

*   `list`
*   `set`
*   `dict`

Their mutability makes them break Rule #1.

---

### What About Your Own Custom Objects?

This is where things get really interesting. What if you create your own `Person` class?

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

p1 = Person('Alice', 30)
p2 = Person('Bob', 42)

employee_roles = {p1: 'Engineer', p2: 'Manager'} # This works!
```

By default, instances of your custom classes are hashable. Why? Because their default hash is based on their `id()`, which is their unique memory address. Since an object’s memory address never changes, it satisfies Rule #1. And since no two objects have the same `id()`, the equality rule is never a problem.

But watch what happens when we define our own logic for equality. Let’s say two `Person` objects are equal if their names are the same.

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def __eq__(self, other):
        return isinstance(other, Person) and self.name == other.name

p1 = Person('Alice', 30)
p2 = Person('Alice', 99) # A different Alice

print(p1 == p2) # This is now True!

# Now let's try to use it as a key...
employee_roles = {p1: 'Engineer'}
```

**Crash!** The moment you defined `__eq__`, Python saw that you were creating your own rules for equality. But you didn’t provide a matching `__hash__` method that follows Rule #2 (`a == b` implies `hash(a) == hash(b)`). To prevent you from creating a broken, inconsistent object, Python defensively makes your class unhashable.

To fix it, you must also define `__hash__` and ensure it follows the rule. The standard practice is to hash a tuple of the same attributes you use for your equality check.

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def __eq__(self, other):
        return isinstance(other, Person) and self.name == other.name

    def __hash__(self):
        # Hash a tuple of the attributes that define the object's identity
        return hash(self.name)

p1 = Person('Alice', 30)
p2 = Person('Alice', 99)

# Now it works!
employee_roles = {p1: 'Engineer'}
# Because p1 and p2 are equal and have the same hash, 
# this overwrites the first entry
employee_roles[p2] = 'Senior Engineer'

print(employee_roles)
print(len(employee_roles))
```

---

### Conclusion

Hashability isn’t just academic trivia; it’s the bedrock of Python’s high-performance lookup structures. It’s the reason dicts and sets are so fast and reliable.

The next time you see that unhashable type error, don’t just swap a list for a tuple and move on. Take a moment to appreciate the “why” behind it. Remember the two golden rules:

1.  **A key’s hash must be constant**, which is why keys must be immutable.
2.  **Equal keys must have equal hashes**, ensuring the dict is consistent and predictable.

Mastering this concept will not only help you debug tricky errors but will give you a deeper understanding of what makes Python’s core data structures tick. It’s the key — pun intended — to writing more robust, efficient, and truly Pythonic code.