# Sorting in Python: list.sort() vs. sorted()
#### The Swiss Army Knife vs. the Scalpel for Sorting in Python

**By Tihomir Manushev**  
*Oct 18, 2025 · 8 min read*

---

Sorting is one of those fundamental tasks in programming that you just can’t escape. Whether you’re organizing a list of user scores, arranging products by price, or just trying to make sense of a chaotic dataset, bringing order to information is critical. Python, in its characteristically elegant way, gives us two primary tools for this job: the `sorted()` built-in function and the `list.sort()` method.

At first glance, they seem to do the same thing. And in a way, they do — they both sort things. But the *how* is critically different, and understanding this difference is a hallmark of a proficient Python developer. One method is a versatile, safe, and universal tool, while the other is a specialized, in-place operator.

Let’s dive in and sort out the details.

---

### The sorted() Built-in Function: Your Universal Sorter

Think of `sorted()` as your friendly, neighborhood sorting utility. It’s a built-in function, which means it’s not tied to any specific object type. You can hand it almost any collection of items — what Python calls an “iterable” — and it will know what to do.

The most important thing to remember about `sorted()` is this: **it always returns a brand new, sorted list, leaving the original collection completely untouched.**

This is a huge deal. It means you can sort data without worrying about causing unintended side effects elsewhere in your code. The original data remains pristine.

Let’s see it in action.

---

### Sorting a Simple List

Here’s the most common use case. We have a list of numbers in a jumbled order, and we want a sorted version.

```python
# Our original, unsorted list of scores
scores = [88, 91, 77, 95, 82]

print(f"Original scores: {scores}")

# Let's use sorted() to get a new, sorted list
sorted_scores = sorted(scores)

print(f"Sorted scores:   {sorted_scores}")
print(f"Original scores are still the same: {scores}")
```

Notice how `scores` is unchanged after the operation. `sorted()` took a look, created a new sorted list, and handed it back to us. We stored that new list in the `sorted_scores` variable.

---

### Sorting Other Iterables

The true power of `sorted()` is its versatility. It doesn’t just work on lists. You can give it a tuple, a string, a set, or even a dict. The result, however, is always a list.

```python
# Sorting a tuple
my_tuple = ('apple', 'orange', 'banana', 'cherry')
sorted_list_from_tuple = sorted(my_tuple)
print(f"Sorted list from tuple: {sorted_list_from_tuple}")
# The original tuple is, of course, unchanged.

# Sorting a string
my_string = "python"
sorted_list_from_string = sorted(my_string)
print(f"Sorted list from string: {sorted_list_from_string}")

# Sorting a set (which has no inherent order)
my_set = {10, 5, 20, 15}
sorted_list_from_set = sorted(my_set)
print(f"Sorted list from set: {sorted_list_from_set}")
```

This makes `sorted()` incredibly reliable. You give it a collection, you get a sorted list back. No surprises.

---

### The list.sort() Method: The In-Place Specialist

Now let’s turn to `list.sort()`. The first clue is in its name: it’s a method of the list object. This means it can only be called on lists. You can’t call `.sort()` on a tuple or a string, because they don’t have this method.

The second, and most critical, difference is its behavior. `list.sort()` modifies the list directly — it sorts it **“in-place”** — and returns `None`.

Let that sink in. It doesn’t create a new list. It shuffles the elements around inside the existing list object.

```python
# Our list of tasks
tasks = ['write article', 'walk the dog', 'buy groceries']

print(f"Original tasks: {tasks}")
print(f"ID of original list: {id(tasks)}")

# Let's sort the list in-place
tasks.sort()

print(f"Sorted tasks:   {tasks}")
print(f"ID of list after sorting: {id(tasks)}")
```

As you can see, the list itself was modified. The `id()` of the object remains the same before and after the call, proving that we are still working with the exact same list in memory. The original order is gone forever.

---

### The None Return Value: An Important Convention

Why does `.sort()` return `None`? This is a deliberate and important design choice in Python. Functions or methods that operate in-place, modifying the object they are called on, should return `None` to make it clear that no new object was created.

This helps prevent a common bug. A beginner might mistakenly write:

```python
# This is a common mistake!
my_numbers = [3, 1, 2]
sorted_numbers = my_numbers.sort() # WRONG!

print(f"The sorted list is: {sorted_numbers}")
print(f"The original list is now: {my_numbers}")
```

The programmer expected `sorted_numbers` to contain `[1, 2, 3]`, but instead it holds `None`. The list `my_numbers` was sorted, but the return value was lost. By returning `None`, Python signals to the developer, “Hey, I changed your original list for you. Don’t look for a new one.”

---

### Advanced Sorting: The key and reverse Arguments

Both `sorted()` and `list.sort()` are more powerful than they first appear. They both accept two optional keyword arguments: `key` and `reverse`.

#### Descending Order with reverse

This one is straightforward. If you want to sort from largest to smallest, just add `reverse=True`.

```python
numbers = [5, 2, 8, 1, 9]

# Using sorted()
print(sorted(numbers, reverse=True))

# Using .sort()
numbers.sort(reverse=True)
print(numbers)
```

#### Custom Sort Logic with key

This is where Python’s sorting tools truly shine. The `key` argument lets you provide a function that will be called on every element before comparisons are made. The list is then sorted based on the return values of this key function.

This is much more efficient than traditional comparison functions because the key function is only called once for each item.

**Example: Case-Insensitive Sorting**

By default, Python sorts strings based on their character codes, which means uppercase letters come before lowercase ones (‘Z’ comes before ‘a’). This is often not what we want.

```python
words = ["Apple", "banana", "Cherry", "date"]
print(f"Default sort: {sorted(words)}")

# To sort alphabetically, we use str.lower as the key function
print(f"Case-insensitive sort: {sorted(words, key=str.lower)}")
```

Here, `str.lower` is a function. For each word, Python calls `.lower()` on it (‘apple’, ‘banana’, ‘cherry’, ‘date’) and uses those temporary, lowercase values for the comparison. The final output still contains the original items.

**Example: Sorting by Length**

What if we want to sort a list of words by their length? Just use the built-in `len` function as the key!

```python
words = ["apple", "banana", "cherry", "date"]
print(sorted(words, key=len))
```

**Example: Sorting Complex Data**

The `key` argument is essential when working with lists of dictionaries or objects. Imagine you have a list of products and want to sort them by price.

```python
products = [
    {'name': 'Laptop', 'price': 1200},
    {'name': 'Mouse', 'price': 25},
    {'name': 'Keyboard', 'price': 75},
]

# Use a lambda function to extract the price for sorting
sorted_by_price = sorted(products, key=lambda product: product['price'])

# Let's print it nicely
for product in sorted_by_price:
    print(product)
```

---

### Stability: Python’s Sorting Superpower

One last concept that’s incredibly useful is stability. Python’s sort is guaranteed to be stable. This means that if two items have an equal key, their original relative order in the list will be preserved.

This might sound abstract, but it’s amazing for multi-level sorting. Imagine you have a list of students, and you want to sort them primarily by grade (descending) and secondarily by name (alphabetically). With a stable sort, you can do this in two passes:

```python
students = [
    ('Alice', 'B'),
    ('Charlie', 'A'),
    ('Bob', 'B'),
    ('David', 'A'),
]

# 1. First, sort by name (the secondary criterion)
students.sort(key=lambda s: s[0])
print(f"After sorting by name: {students}")
# Output: [('Alice', 'B'), ('Bob', 'B'), ('Charlie', 'A'), ('David', 'A')]

# 2. Now, sort by grade (the primary criterion)
students.sort(key=lambda s: s[1], reverse=True) # A grades first
print(f"After sorting by grade: {students}")
```

This final output is not what a beginner might expect. `reverse=True` will sort the grades Z-A. The correct way to sort grades A, B, C… is without reversing.

Let’s correct the example:

```python
students = [
    ('Alice', 'B'),
    ('Charlie', 'A'),
    ('Bob', 'B'),
    ('David', 'A'),
]

# 1. First, sort by name (the secondary criterion)
students.sort(key=lambda s: s[0])
# students is now [('Alice', 'B'), ('Bob', 'B'), ('Charlie', 'A'), ('David', 'A')]


# 2. Now, sort by grade (the primary criterion)
students.sort(key=lambda s: s[1])
# students is now [('Charlie', 'A'), ('David', 'A'), ('Alice', 'B'), ('Bob', 'B')]

print(f"Final sorted list: {students}")
```

Look at the final result! The students are grouped by grade (‘A’s then ‘B’s). And within the ‘A’ grade, Charlie comes before David. Within the ‘B’ grade, Alice comes before Bob. Their alphabetical order from the first sort was preserved because the second sort was stable.

---

### Conclusion: Which One Should You Use?

Here’s the simple rule of thumb:

*   **When in doubt, use `sorted()`.** It’s safer, more versatile, and the fact that it doesn’t modify your original data prevents a whole class of bugs. It’s the right choice 95% of the time.
*   **Use `list.sort()` only when you are certain you no longer need the original ordering of a list and you are looking to optimize for memory.** If you’re working with a list containing millions of items, sorting it in-place avoids creating a second massive list in memory, which can be a significant saving. But unless you’re in that specific situation and have profiled your code, stick with the clarity and safety of `sorted()`.

Mastering these two sorting tools — and especially the power of the `key` argument — is a major step toward writing clean, efficient, and truly Pythonic code.