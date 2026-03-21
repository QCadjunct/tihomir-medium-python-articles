# Defensive Programming in Python: Stop Your Classes from Destroying Your Data
#### We need to talk about trust.

**By Tihomir Manushev**  
*Nov 25, 2025 · 8 min read*

---

When you use a library, a framework, or even a class written by a colleague, you operate on a baseline of trust. If you pass a list of data into a function to be analyzed, you implicitly trust that the function won’t erase that data from your hard drive. You also trust — perhaps a bit too naively — that the function won’t modify your list in memory unless it explicitly says it will.

In Python, however, that trust is easily broken. Because of how Python handles memory and object references, a simple assignment statement can create a wormhole between your class and the outside world, leading to one of the most frustrating categories of bugs: unexpected mutation.

If you have ever passed a list to a class, only to find that your original list was mysteriously emptied or scrambled later in your program, you have fallen victim to the aliasing trap.

Today, we are going to look at how to code defensively. We will explore how to handle mutable arguments (like lists and dictionaries) safely, ensuring that your classes follow the “Principle of Least Astonishment” and don’t cannibalize the data given to them.

---

### The Mechanism of the Crime: Call by Sharing

To understand the bug, we have to understand how Python passes arguments. Python is neither “pass by value” (like C ints) nor strictly “pass by reference” (like C pointers). It uses a mechanism often called “Call by Sharing.”

When you pass a list into a function or a class constructor, you aren’t passing the actual bucket of data. You are passing a label (a reference) that points to that bucket.

If your class accepts that label and simply sticks it onto an instance variable, your class and the outside code are now holding onto the exact same object. If your class decides to delete an item from that list, it disappears from the outside code too.

Let’s look at a concrete example.

---

### The Scenario: The Greedy Playlist

Imagine we are building a music application. We have a class called `PartyPlaylist`. Its job is to take a list of songs, queue them up, and remove them from the queue as they are played.

Here is the naive implementation. This looks like perfectly standard Python code, but it harbors a dangerous side effect.

```python
class PartyPlaylist:
    """A playlist that queues songs and plays them one by one."""
    
    def __init__(self, songs):
        # DANGER: Direct assignment aliases the external list!
        self.queue = songs
        
    def play_next(self):
        if not self.queue:
            print("The music has stopped!")
            return
        
        # Pop removes the item from the list
        current_song = self.queue.pop(0)
        print(f"Now playing: {current_song}")
        
    def remaining_tracks(self):
        return len(self.queue)
```

At first glance, this logic seems sound. We initialize with songs, and `play_next` removes the top song to play it. Efficiency!

But let’s see what happens from the perspective of the user who keeps a master list of their favorite tracks.

```python
# My master list of favorites
my_all_time_favorites = [
    "Bohemian Rhapsody", 
    "Hotel California", 
    "Stairway to Heaven", 
    "Imagine"
]

# I create a playlist for the party using my favorites
friday_night_party = PartyPlaylist(my_all_time_favorites)

print(f"Songs before party: {len(my_all_time_favorites)}")

# The party starts! We play a few songs.
friday_night_party.play_next()

friday_night_party.play_next()

# The party is over. I want to check my master list again.
print(f"Songs after party: {len(my_all_time_favorites)}")
```

Look at the final output. `my_all_time_favorites` lost two songs!

The user of this class did not ask for their master list to be modified. They just wanted to seed the playlist with those songs. But because `PartyPlaylist` operated on the list in place, the data vanished from the original variable `my_all_time_favorites`.

This violates the Principle of Least Astonishment. A user expects a playlist to manage its own internal state, not to reach out and modify the data structures passed to it during initialization.

The bug occurred in this line:

```python
self.queue = songs
```

In Python, variables are not boxes that contain data; they are sticky notes attached to objects.

1.  Outside the class, the sticky note `my_all_time_favorites` is attached to a list object in memory.
2.  We pass that list to `__init__`. The argument `songs` is a temporary sticky note attached to that same list object.
3.  We perform `self.queue = songs`. Now, `self.queue` is a third sticky note attached to that same list object.

We don’t have two lists. We have one list with multiple names. When `self.queue.pop(0)` runs, it reaches into that one shared list and rips out the first item. Everyone looking at that list sees the damage.

---

### The Fix: Defensive Copying

The solution is simple but vital: Defensive Programming.

When your class accepts a mutable object (like a list, set, or dictionary) that it intends to store or modify, you should create your own local copy of that data. You break the link between the argument and the instance attribute.

Here is the `SafePlaylist`:

```python
class SafePlaylist:
    """A playlist that manages its own internal copy of the queue."""
    
    def __init__(self, songs=None):
        if songs is None:
            self.queue = []
        else:
            # SAFETY: We create a new list from the input
            self.queue = list(songs)
            
    def play_next(self):
        if not self.queue:
            print("Silence...")
            return
            
        current_song = self.queue.pop(0)
        print(f"Now playing: {current_song}")

my_all_time_favorites = ["Bohemian Rhapsody", "Hotel California"]

# Initialize the safe version
saturday_party = SafePlaylist(my_all_time_favorites)

saturday_party.play_next()

# Check the master list
print(my_all_time_favorites)
```

The master list is untouched. By using `list(songs)`, we instructed Python to iterate over the input data and build a new list container in memory. `self.queue` now points to this new object. The external world remains safe.

---

### Why use list(songs)?

You might ask, “Why not use `songs.copy()` or `songs[:]`?”

Those methods work perfectly fine if you are certain `songs` is a list. However, using the `list()` constructor is the most robust, “Pythonic” approach for two reasons:

1.  **Polymorphism:** The user might pass a tuple, a set, or even a generator (like `range(10)` or a database cursor) to your class. `songs.copy()` would crash if `songs` is a tuple (tuples don’t have a `.copy()` method). `list(songs)` will happily accept any iterable and convert it into a fresh, mutable list.
2.  **Explicit Intent:** It clearly signals to the reader, “I am enforcing that this attribute is a list, regardless of what was passed in.”

---

### Handling Mutable Defaults

While we are discussing mutable arguments, we must address the most famous “gotcha” in Python, which often appears alongside the aliasing bug.

It is tempting to write the constructor like this to handle the empty case:

```python
# DO NOT DO THIS
def __init__(self, songs=[]):
    self.queue = songs
```

This creates a Mutable Default Argument. In Python, default parameter values are evaluated once, when the function is defined (usually when the module is imported), not every time the function is called.

If you use `songs=[]`, that specific empty list object is created once and stored inside the `__init__` function itself.

1.  Playlist A is created with no arguments. It uses the default list. It adds a song.
2.  Playlist B is created with no arguments. It also uses the default list.
3.  Playlist B suddenly sees the song that Playlist A added.

The default list becomes a shared dumping ground for every instance of the class that didn’t provide its own list.

---

### The Defensive Pattern for Defaults

The standard pattern to solve this is using `None` as the sentinel value:

```python
def __init__(self, songs=None):
    if songs is None:
        self.queue = []  # Create a fresh list for this instance
    else:
        self.queue = list(songs)  # Create a copy of the provided list
```

This covers both bases: it prevents shared defaults between instances, and it prevents aliasing of external arguments.

---

### Shallow vs. Deep Copies

A word of warning: the `list()` constructor creates a shallow copy.

This means it creates a new list container, but fills it with references to the same items that were in the original list. If your list contains strings or integers (immutable objects), this is fine.

However, if your playlist contained mutable objects — say, `Song` objects that have a mutable `rating` attribute — sharing might still occur at the item level.

```python
original = [song_obj_1, song_obj_2]
copy = list(original)
```

If you do `copy.pop()`, `original` is unaffected (the list structure is separate). But if you do `copy[0].rating = 5`, `original[0]` is affected, because both lists point to the same `Song` object in memory.

For most cases (like our playlist where we are adding/removing items), a shallow copy is exactly what you need. If you need to completely duplicate a nested structure so that nothing is shared, you need the `copy.deepcopy()` function from Python’s `copy` module. But beware: deep copies are computationally expensive.

---

### When Should You Mutate?

Is mutation always evil? No.

Sometimes, the entire point of a function is to modify an object in place. For example, `random.shuffle(my_list)` shuffles the list in place. It doesn’t return a new list. This is efficient for large datasets.

However, the convention in Python is that if a function modifies the list in place, it should return `None`. If it creates a new list, it should return that list.

If you are writing a class, you have to decide: Is this class the Owner or the Viewer of the data?

*   **The Viewer:** If your class just needs to look at the data to calculate something (like a Statistics class), it shouldn’t change it.
*   **The Owner:** If your class represents a manager (like our Playlist), it should own its own data. If it is initialized with external data, it should take ownership by making a copy.

---

### Conclusion

Python’s reference-based model is powerful and memory-efficient, but it places the burden of safety on the developer. Variables are labels, not boxes, and passing a mutable object is essentially handing over the keys to your house.

When designing classes, assume that the data passed to you is precious to the caller. Don’t modify it unless that is the explicit purpose of your component. By implementing defensive copying using `list()` (or `dict()`, `set()`, etc.) inside your constructors, and by avoiding mutable default arguments, you ensure your code is robust, reusable, and bug-free.

Don’t let your objects become traitors. Copy your inputs, and keep your data safe.