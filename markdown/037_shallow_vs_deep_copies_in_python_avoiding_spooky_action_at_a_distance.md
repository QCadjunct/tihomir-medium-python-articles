# Shallow vs. Deep Copies in Python: Avoiding Spooky Action at a Distance
#### How to stop your variables from haunting each other using Python’s memory management secrets

**By Tihomir Manushev**  
*Nov 22, 2025 · 8 min read*

---

Einstein famously dismissed quantum entanglement as “spooky action at a distance.” He was skeptical that affecting one particle could instantly change the state of another particle miles away.

If Einstein had been a Python developer, he wouldn’t have been so skeptical. He would have called it a Tuesday.

In Python, “spooky action at a distance” is a common bug. You change a value in variable A, and suddenly, variable B — which should be totally unrelated — changes too. You fix a bug in a configuration dictionary for your development environment, and the production environment crashes.

The culprit is almost always a misunderstanding of how Python handles memory, specifically the difference between shallow copies and deep copies.

To write robust Python code, you need to stop trusting the equals sign (=) and understand what actually happens when you duplicate data.

---

### The Illusion of Assignment

Before we dive into copying, we have to unlearn a bad habit from other languages: assuming that assignment creates a copy.

In many contexts, we visualize variables as boxes. If I say `x = 10`, I put the number 10 in box x. If I then say `y = x`, I copy the number 10 into box y. If I change x, y stays the same.

In Python, variables are not boxes; they are labels (or references) attached to objects.

When you execute `list_a = [1, 2, 3]` and then `list_b = list_a`, you haven’t created a second list. You have simply slapped a second sticky note that says `list_b` onto the exact same object in memory.

```python
alpha_squad = ["Raptor", "Hawk", "Eagle"]
bravo_squad = alpha_squad

# Let's rename the first member of Alpha
alpha_squad[0] = "Chicken"

print(bravo_squad)
```

Both variables point to the same memory address. This is aliasing, not copying. To actually duplicate the data so you can modify one without wrecking the other, you need to explicitly clone the object.

This is where the rabbit hole opens.

---

### The Shallow Copy: The “Good Enough” Solution

The most common way to copy a collection in Python is to perform a shallow copy. You do this all the time, perhaps without knowing the terminology.

If you use the list constructor `list(original)`, the slice operator `original[:]`, or the `copy()` method on a dictionary, you are creating a shallow copy.

A shallow copy creates a new container, but it populates that container with references to the same items held by the original.

Think of it like a physical file folder containing legal contracts.

*   **Aliasing** is two people holding onto the exact same folder.
*   **Shallow Copying** is buying a brand new folder, but simply moving the original contracts into it.

If the contracts are immutable (like read-only PDFs), this is fine. But if the contracts are editable documents, you have a problem.

---

### When Shallow Copies Work

If your list contains only immutable objects (like integers, strings, or tuples containing immutables), a shallow copy is perfectly safe and memory-efficient.

```python
original_scores = [99, 85, 76]
# Create a shallow copy using slicing
backup_scores = original_scores[:] 

backup_scores[0] = 100 

print(original_scores)
print(backup_scores)
```

Because integers are immutable, assigning 100 to index 0 of `backup_scores` puts a new object into the new container. The original container remains untouched.

---

### The Trap: Mutable Contents

The “spooky action” occurs when you shallow copy a collection that holds mutable items, like lists inside lists, or class instances inside a dictionary.

Let’s look at a Role-Playing Game (RPG) inventory system to illustrate this. We will define a backpack that contains some immutable items (strings) and a mutable item (a list of potions).

```python
# A list containing strings and an inner list
hero_inventory = ["Sword", "Shield", ["Health Potion", "Mana Potion"]]

# Make a shallow copy for a generic NPC based on the hero
npc_inventory = list(hero_inventory)

print(f"Hero: {hero_inventory}")
print(f"NPC:  {npc_inventory}")

# 1. The NPC drops the Sword (immutable string)
npc_inventory[0] = "Dagger"

# 2. The NPC drinks a Health Potion (mutating the inner list)
npc_inventory[2].remove("Health Potion")

print("\n--- AFTER CHANGES ---")
print(f"NPC:  {npc_inventory}")
print(f"Hero: {hero_inventory}")
```

What just happened?

1.  Changing “Sword” to “Dagger” worked fine. The `npc_inventory` list slot 0 now points to a new string object. The `hero_inventory` slot 0 still points to the old one.
2.  However, removing the potion modified the inner list. Both the Hero and the NPC share a reference to the exact same list object for their potions.

When `list(hero_inventory)` ran, Python created a new outer list, but it didn’t recursively copy the objects inside. It just copied the pointers. The Hero and the NPC are fighting over the exact same bag of potions.

This behavior causes subtle bugs. You might pass a configuration dictionary to a function, create a shallow copy to “play it safe,” modify a nested setting, and mistakenly corrupt the global configuration.

---

### Deep Copies: The Nuclear Option

To sever the connection completely, you need a deep copy.

A deep copy constructs a new compound object and then, recursively, inserts copies into it of the objects found in the original. It walks the entire object tree, cloning everything it finds.

To do this in Python, you need the `copy` module.

Let’s fix our RPG inventory bug:

```python
import copy

hero_inventory = ["Sword", "Shield", ["Health Potion", "Mana Potion"]]

# Use deepcopy instead of list()
npc_inventory = copy.deepcopy(hero_inventory)

# The NPC drinks a potion
npc_inventory[2].remove("Health Potion")

print(f"NPC Potions:  {npc_inventory}")
print(f"Hero Potions: {hero_inventory}")
```

Success! The `deepcopy` function saw the inner list of potions, realized it was mutable, and created a brand new list for the NPC, populating it with copies of the strings. The two objects are now completely independent.

---

### Handling Cyclic References

You might be wondering: “What happens if object A contains object B, and object B contains a reference back to object A? Will deepcopy enter an infinite loop and crash my program?”

This is known as a cyclic reference. It’s common in data structures like graphs, doubly linked lists, or parent/child relationships in ORMs.

Let’s simulate a relationship between a Driver and a Car.

```python
import copy

class Car:
    def __init__(self, model):
        self.model = model
        self.driver = None

class Driver:
    def __init__(self, name):
        self.name = name
        self.car = None

# Create objects
delorean = Car("Delorean")
marty = Driver("Marty")

# Create the cycle
delorean.driver = marty
marty.car = delorean

# Verify the cycle
print(f"Marty drives a {marty.car.model}")
print(f"The {delorean.model} is driven by {delorean.driver.name}")

# Attempt a deep copy
marty_clone = copy.deepcopy(marty)

print("\n--- CLONE STATUS ---")
print(f"Clone Name: {marty_clone.name}")
print(f"Clone's Car: {marty_clone.car.model}")
print(f"Is the clone's car the same object? {marty_clone.car is delorean}")
```

Python’s `deepcopy` implementation is smart. It keeps a “memo” dictionary of objects it has already copied during the current operation. When it encounters the link from the Car back to the Driver, it recognizes that it has already processed the Driver and assigns the reference to the copy it is currently building, rather than starting over.

The `marty_clone` is a new object. His car is a new object. And his car’s driver points back to `marty_clone`, preserving the cycle logic without crashing the stack.

---

### When to Use Which?

If `deepcopy` is so safe, why don’t we use it for everything?

**1. Performance Overhead**
Deep copying is expensive. It has to recursively walk every attribute of every object. If you have a massive dataset — say, a list of 10,000 complex objects — `deepcopy` will chew up CPU cycles and double your memory usage. Shallow copies are instant and lightweight.

**2. External Resources**
Sometimes, you want sharing. If you are copying an object that holds a reference to a database connection, a file handle, or a singleton (like `None` or a specialized Sentinel object), you usually don’t want to clone that resource. You want the copy to point to the same open file or database session.

**3. Defensive Programming**
A common pattern in Python classes is to accept a list as an argument. A naive implementation stores the list directly:

```python
class GradeBook:
    def __init__(self, grades):
        # DANGER: Aliasing!
        self.grades = grades
```

If the caller modifies their list later, your class’s internal state changes. To defend against this, use a shallow copy:

```python
class GradeBook:
    def __init__(self, grades):
        # SAFER: Shallow copy
        self.grades = list(grades)
```

This protects the structure of the list. If `grades` contains only numbers, you are 100% safe. If `grades` contains mutable student objects, you must decide: do I trust the caller not to mutate the students? If not, you might need `deepcopy`, but be wary of the performance hit.

---

### Summary

Understanding memory references is what separates someone who writes Python scripts from someone who engineers Python systems.

Here is the cheat sheet for your next code review:

*   **Assignment (=)** creates an alias (a new label), not a copy.
*   **Shallow Copy (`list[:]`, `copy.copy`)** copies the outer container. Inner elements are shared. This is fast and usually sufficient for immutable data.
*   **Deep Copy (`copy.deepcopy`)** recursively clones everything. It is safer for nested, mutable data but slower and memory-hungry.
*   **Cyclic References** are handled automatically by `deepcopy`, so don’t fear the infinite loop.

The next time you see a bug where data changes “on its own” in a different part of your application, don’t call a ghostbuster. Check your `.append()` calls, check your mutable defaults, and check if you need to switch from a shallow copy to a deep one.