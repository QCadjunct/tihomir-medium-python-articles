# Sets: Python’s Hidden Gem for High-Performance Code
#### How to write faster, cleaner Python code by replacing your lists with this powerful data type.

**By Tihomir Manushev**  
*Oct 26, 2025 · 8 min read*

---

Let’s be honest. When you’re faced with a collection of items in Python, your first instinct is to reach for a list. It’s the Swiss Army knife of Python data structures — versatile, easy to understand, and always there when you need it. We use lists for everything: storing user IDs, managing to-do items, and wrangling data from APIs.

But what if I told you that in many common scenarios, your trusty list is the wrong tool for the job? What if it’s silently slowing your application down and cluttering your code with unnecessary loops and conditionals?

Enter the Python set.

If the list is the dependable multi-tool, the set is the specialized, high-precision instrument. It’s a fundamental data structure that many developers — even experienced ones — tend to overlook. But once you understand its purpose, you’ll start seeing opportunities everywhere to write code that is not just faster, but also dramatically more expressive and readable. This isn’t just about micro-optimizations; it’s about a fundamentally better way to solve a whole class of problems.

---

### What Exactly Is a Set?

At its core, a Python set is an unordered collection of unique, hashable items. Let’s break that down, because every word is important.

*   **Unordered:** Unlike a list, a set does not maintain the insertion order of its elements. You can’t ask for the “first” or “last” item in a set, because there’s no inherent sequence. This might sound like a limitation, but it’s the very thing that enables its incredible performance.
*   **Unique:** This is the hallmark feature. A set cannot contain duplicate elements. If you try to add an item that’s already in the set, nothing happens. The set simply ensures the item is present, but only once.
*   **Hashable:** This is the secret sauce behind a set’s speed. Every item in a set must be “hashable,” meaning it can be converted into a fixed-size integer (a “hash”) that never changes during its lifetime. This allows Python to store and retrieve items with breathtaking speed. All of Python’s immutable built-in types — like strings, numbers, booleans, and tuples containing only hashable elements — are hashable. Mutable types like lists and dictionaries are not.

You can create a set in two main ways:

```python
# Using the literal syntax with curly braces
tech_skills = {'python', 'git', 'sql', 'docker'}
print(tech_skills)

# Using the set() constructor with an iterable (like a list)
names = ['Alice', 'Bob', 'Charlie', 'Alice']
unique_names = set(names)
print(unique_names)
```

One crucial syntax quirk to remember: an empty pair of curly braces `{}` creates an empty dictionary, not an empty set. To create an empty set, you must use the constructor:

```python
# This creates an empty dictionary
empty_dict = {}
print(type(empty_dict))

# This is the correct way to create an empty set
empty_set = set()
print(type(empty_set))
```

---

### The Need for Speed: Membership Testing

This is where sets truly shine and leave lists in the dust. Imagine you’re building a service that needs to check a new username against a massive blocklist of millions of banned names.

With a list, your code would look like this:

```python
import time

# Simulate a huge blocklist with 10 million names
banned_users_list = [f'user_{i}' for i in range(10_000_000)]
# The name we want to check is the very last one
username_to_check = 'user_9999999'

start_time = time.time()
if username_to_check in banned_users_list:
    print(f"'{username_to_check}' is banned.")
end_time = time.time()

print(f"List lookup took: {end_time - start_time:.6f} seconds")
```

When you run this, you’ll notice a significant delay. That’s because to check if `username_to_check` is in the list, Python has to perform a linear scan. It starts at the first element and checks every single item, one by one, until it finds a match or reaches the end. In our worst-case scenario, it has to check all 10 million items. The time this takes grows directly with the size of the list (this is known as O(n) complexity).

Now, let’s do the exact same thing with a set:

```python
import time

# Create a set from the same data
banned_users_set = {f'user_{i}' for i in range(10_000_000)}
username_to_check = 'user_9999999'

start_time = time.time()
if username_to_check in banned_users_set:
    print(f"'{username_to_check}' is banned.")
end_time = time.time()

print(f"Set lookup took: {end_time - start_time:.6f} seconds")
```

The result is nearly instantaneous. It’s so fast it might register as 0.000000 seconds.

How is this possible? Because of hashing. When you check for an item in a set, Python doesn’t scan anything. It computes the hash of the item and uses that value to calculate an index where the item should be in memory. It jumps directly to that spot and checks if the item is there. This operation takes roughly the same amount of time whether the set has 10 items or 10 million (this is O(1), or constant time, complexity).

The takeaway: If you need to repeatedly check for the existence of an item in a large collection, a set is unequivocally the right choice.

---

### From Messy Loops to Elegant Logic: Set Operations

Beyond raw speed, sets provide a beautiful, declarative syntax for logical operations that would otherwise require cumbersome loops and conditionals. These operations, based on mathematical set theory, allow you to express complex relationships between collections in a single, readable line.

Let’s imagine we’re managing user permissions for a content platform.

```python
admins = {'alice', 'bob', 'charlie'}
editors = {'charlie', 'david', 'eve'}
viewers = {'frank', 'grace', 'alice'}
```

#### 1. Intersection (&): Finding the Overlap

What if you need to find users who are both an admin and an editor? Without sets, you’d write a loop:

```python
# The old way
admin_editors_list = []
for user in admins:
    if user in editors:
        admin_editors_list.append(user)
# admin_editors_list -> ['charlie']
```

With sets, this becomes a simple intersection operation:

```python
# The set way
admin_editors = admins & editors
print(admin_editors)
# Output: {'charlie'}
```

This is not only shorter but also more clearly states your intent: “Give me the intersection of admins and editors.”

#### 2. Union (|): Combining All Unique Items

Now, you want to send a notification to everyone who has any role on the platform. You need a single collection of all unique users.

```python
# The set way
all_users = admins | editors | viewers
print(all_users)
# Output: {'eve', 'bob', 'grace', 'frank', 'david', 'charlie', 'alice'}
```

The union operator `|` combines all the sets and automatically handles the duplicates for you. Achieving this with lists would require more complex logic to avoid adding users multiple times.

#### 3. Difference (-): Finding What’s Not in Another Set

This is an incredibly useful operation. Suppose you want to find users who are admins but are not editors, perhaps to grant them a new permission.

```python
# The set way
admins_only = admins - editors
print(admins_only)
# Output: {'bob', 'alice'}
```

The difference operator `-` gives you the elements in the first set that do not exist in the second. Again, this replaces a loop and a conditional with a single, intuitive expression.

#### 4. Symmetric Difference (^): Finding Mutually Exclusive Items

A less common but equally powerful tool is the symmetric difference. It gives you all the elements that are in one set or the other, but not in both. For example, let’s find the people who are either an admin or an editor, but not both.

```python
# The set way
exclusive_roles = admins ^ editors
print(exclusive_roles)
# Output: {'eve', 'bob', 'alice', 'david'}
```

This operator is perfect for identifying items that are unique to each collection.

---

### Practical Recipes and Final Gotchas

*   **Deduplicating a List:** This is the most common use case for sets. To remove duplicates from a list, just convert it to a set and back.

```python
numbers = [1, 5, 2, 8, 2, 5, 5, 1]
unique_numbers = list(set(numbers))
# unique_numbers -> [1, 2, 5, 8] (order is not guaranteed!)
```

If you need to preserve the original order, a clever trick using dictionary keys (which are also unique) is the modern way:

```python
ordered_unique_numbers = list(dict.fromkeys(numbers))
# ordered_unique_numbers -> [1, 5, 2, 8] (order preserved!)
```

*   **Set Comprehensions:** Just like list comprehensions, you can build sets with a concise and readable syntax.

```python
# Create a set of squares of even numbers from 0 to 10
squares_of_evens = {x**2 for x in range(11) if x % 2 == 0}
# squares_of_evens -> {0, 64, 4, 36, 100, 16}
```

*   **Immutability and frozenset:** What if you need to put a set inside another set? You can’t, because sets are mutable and therefore not hashable. The solution is `frozenset` — an immutable version of a set. Once created, it cannot be changed, making it hashable.

```python
set_of_sets = {frozenset({1, 2}), frozenset({2, 3})}
# This works perfectly!
```

---

### Conclusion

The Python list will always be a core part of your toolkit. But it’s time to recognize its limitations. The set is not an obscure, academic data structure; it is a high-performance, expressive tool designed to solve real-world problems with elegance and speed.

The next time you find yourself writing `if item not in my_list: my_list.append(item)`, stop. That’s a signal. The next time you need to find the common elements between two lists, listen. Your code is telling you it needs a set. By learning to recognize these patterns, you won’t just be optimizing your code — you’ll be elevating your craft as a Python developer.