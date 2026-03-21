# Building a Real-World App with Python’s @dataclass
#### A Practical Guide to Using @dataclass for More Than Just Data Storage

**By Tihomir Manushev**  
*Nov 16, 2025 · 8 min read*

---

If you’ve spent any time with Python’s object-oriented features, you’ve written this class a dozen times: a simple container for data. You write the `__init__` method, dutifully listing every parameter twice. Then you write the `__repr__` method so your debug logs don’t just show a useless memory address. Then you write `__eq__` because you need to compare two objects. It’s a rite of passage, but it’s also a lot of boilerplate code for a simple task.

Enter the `@dataclass` decorator, introduced in Python 3.7. It’s a gift from the Python gods, designed to automatically generate that boilerplate for you. While most tutorials show you how to create a simple Point or Person class, the true power of data classes shines when you use them as the building blocks for a larger, more meaningful application.

In this article, we’ll go beyond the simple examples. We will build a mini-application for managing a bookstore’s inventory. Along the way, you’ll see how data classes help us model complex data cleanly and how they interact with regular classes that contain our application’s business logic.

---

### Step 1: Modeling the Core Data

Every application starts with its data model. For our bookstore, the core entities are authors and books. These are perfect candidates for data classes because they primarily exist to hold information.

#### The Immutable Author

Let’s start with an Author. An author has a name and a birth year. Once an author object is created, these facts shouldn’t change. We can enforce this by making our data class immutable.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Author:
    """Represents an author with a name and birth year.
    
    This class is immutable, meaning its instances cannot be changed
    after creation. This is great for data that should be constant.
    """
    name: str
    birth_year: int

# Let's create an author
author_orwell = Author(name="George Orwell", birth_year=1903)
print(author_orwell)

# Trying to change it will raise an error:
# author_orwell.name = "Eric Arthur Blair"
```

By adding `@dataclass(frozen=True)`, we get more than just an `__init__` and `__repr__`. We get a class that protects its data from accidental modification, leading to more robust and predictable code. Notice how the `print()` output is already clean and informative — that’s the free `__repr__` at work!

#### The Complex Book

A book is more complex. It has an ISBN, a title, a list of authors, and a publication year. This is where we encounter one of the most important features of data classes: handling mutable default values.

You might be tempted to write `authors: list = []`, but this is a classic Python pitfall! That empty list would be shared across all instances of Book. Instead, we use `field` and `default_factory`.

```python
from dataclasses import field, dataclass
from typing import List

# ...

@dataclass
class Book:
    """Represents a book in our inventory."""
    isbn: str
    title: str
    publication_year: int
    authors: List[Author] = field(default_factory=list)
    language: str = "English"


# Create a couple of authors first
author_tolkien = Author(name="J.R.R. Tolkien", birth_year=1892)
author_lewis = Author(name="C.S. Lewis", birth_year=1898)

# Now, create books
book_hobbit = Book(
    isbn="978-0345339683",
    title="The Hobbit",
    publication_year=1937,
    authors=[author_tolkien]
)

book_narnia = Book(
    isbn="978-0064471046",
    title="The Lion, the Witch and the Wardrobe",
    publication_year=1950,
    authors=[author_lewis]
)

print(book_hobbit)
```

In this Book class:

1.  `authors: List[Author]` is type-hinted to be a list of our Author objects. This makes our code self-documenting.
2.  `field(default_factory=list)` tells the data class to create a new empty list for each Book instance by calling `list()`. This avoids the mutable default trap and is the correct way to handle fields like lists or dictionaries.
3.  `language: str = "English"` shows a simple, default value, which works just as you’d expect.

---

### Step 2: Adding Behavior with a Manager Class

Data classes are fantastic for holding data, but where does the logic go?

The solution is to create manager classes that contain the business logic. Our `Inventory` class will not be a data class; it will be a regular class that uses our Book data class.

```python
class Inventory:
    """Manages the collection of books, their stock, and prices."""
    
    def __init__(self):
        # A private dictionary to store inventory details
        self._stock = {}

    def add_book(self, book: Book, quantity: int, price: float):
        """Adds a book to the inventory."""
        if not isinstance(book, Book):
            raise TypeError("Can only add Book objects to inventory.")
        if quantity < 0 or price < 0:
            raise ValueError("Quantity and price cannot be negative.")

        self._stock[book.isbn] = {
            "book": book,
            "quantity": quantity,
            "price": price
        }
        print(f"Added '{book.title}' to inventory.")

    def get_book_details(self, isbn: str):
        """Retrieves the full details for a book in stock."""
        return self._stock.get(isbn)

    def find_books_by_author(self, author_name: str) -> List[Book]:
        """Finds all books written by a given author."""
        found_books = []
        for item in self._stock.values():
            book = item['book']
            for author in book.authors:
                if author_name.lower() in author.name.lower():
                    found_books.append(book)
        return found_books
```

This design gives us the best of both worlds:

*   **Clean Data Containers:** Our `Book` and `Author` classes are lean and focused solely on representing data.
*   **Organized Logic:** Our `Inventory` class has a clear responsibility: managing the collection of books. Its methods contain the “verbs” (add, find, get) that act on our data “nouns.”

---

### Step 3: Putting It All Together

Now, let’s run our bookstore! We can create our authors and books, add them to the inventory, and use our manager methods to interact with the data.

```python
from dataclasses import field, dataclass
from typing import List


@dataclass(frozen=True)
class Author:
    """Represents an author with a name and birth year.

    This class is immutable, meaning its instances cannot be changed
    after creation. This is great for data that should be constant.
    """
    name: str
    birth_year: int


@dataclass
class Book:
    """Represents a book in our inventory."""
    isbn: str
    title: str
    publication_year: int
    authors: List[Author] = field(default_factory=list)
    language: str = "English"


class Inventory:
    """Manages the collection of books, their stock, and prices."""

    def __init__(self):
        # A private dictionary to store inventory details
        self._stock = {}

    def add_book(self, book: Book, quantity: int, price: float):
        """Adds a book to the inventory."""
        if not isinstance(book, Book):
            raise TypeError("Can only add Book objects to inventory.")
        if quantity < 0 or price < 0:
            raise ValueError("Quantity and price cannot be negative.")

        self._stock[book.isbn] = {
            "book": book,
            "quantity": quantity,
            "price": price
        }
        print(f"Added '{book.title}' to inventory.")

    def get_book_details(self, isbn: str):
        """Retrieves the full details for a book in stock."""
        return self._stock.get(isbn)

    def find_books_by_author(self, author_name: str) -> List[Book]:
        """Finds all books written by a given author."""
        found_books = []
        for item in self._stock.values():
            book = item['book']
            for author in book.authors:
                if author_name.lower() in author.name.lower():
                    found_books.append(book)
        return found_books


# 1. Create our data objects
author_tolkien = Author(name="J.R.R. Tolkien", birth_year=1892)
book_lotr = Book(
    isbn="978-0618640157",
    title="The Lord of the Rings",
    publication_year=1954,
    authors=[author_tolkien]
)
book_silmarillion = Book(
    isbn="978-0618391110",
    title="The Silmarillion",
    publication_year=1977,
    authors=[author_tolkien]
)

# 2. Create our manager and add books
bookstore_inventory = Inventory()
bookstore_inventory.add_book(book_lotr, quantity=20, price=25.00)
bookstore_inventory.add_book(book_silmarillion, quantity=5, price=22.50)

# 3. Use the inventory to find information
print("\n--- Searching for Tolkien's books ---")
tolkien_books = bookstore_inventory.find_books_by_author("Tolkien")
for book in tolkien_books:
    # Look how readable this is!
    print(f"- {book.title} ({book.publication_year})")

print("\n--- Getting stock details ---")
lotr_details = bookstore_inventory.get_book_details("978-0618640157")
print(f"Details: {lotr_details}")
```

The output is clean and readable, thanks in large part to the auto-generated `__repr__` on our data classes. The interactions are intuitive because the responsibilities are clearly separated.

---

### Step 4: Customizing with Advanced Features

What if we need to sort our books? For example, by publication year. The `@dataclass` decorator has us covered with the `order=True` argument, which automatically generates comparison methods (`__lt__`, `__gt__`, etc.).

But what if the default sort order isn’t what we want? A data class will sort fields in the order they are defined. To get more control, we can use the `__post_init__` method. This special method is called after the object has been initialized, allowing for extra setup or validation.

Let’s modify our Book class to support custom sorting by publication year, then by title.

```python
@dataclass(order=True)
class Book:
    """A book class that supports custom sorting."""
    
    # We create a field for sorting that is not part of the constructor.
    # It's also excluded from the repr for cleanliness.
    sort_index: tuple = field(init=False, repr=False, compare=True)

    # The rest of the fields should not be used for comparison
    title: str = field(compare=False)
    isbn: str = field(compare=False)
    publication_year: int = field(compare=False)
    authors: List[Author] = field(default_factory=list, compare=False)
    
    def __post_init__(self):
        # This is where we define our custom sort order.
        # We want to sort by publication year, then title.
        self.sort_index = (self.publication_year, self.title)

# Let's create a list of books to sort
book1 = Book(title="A", publication_year=2005, isbn="1")
book2 = Book(title="C", publication_year=2001, isbn="2")
book3 = Book(title="B", publication_year=2005, isbn="3")

books_to_sort = [book1, book2, book3]
books_to_sort.sort()

print("\n--- Sorted Books ---")
for book in books_to_sort:
    print(f"- {book.title} published in {book.publication_year}")
```

This is an incredibly powerful pattern. We’ve enabled rich comparison logic without cluttering our `__init__` method or writing six different dunder methods by hand. The `__post_init__` hook allows us to derive computed fields, run validation, or perform any other setup we need.

---

### Conclusion

Python’s data classes are more than just a shortcut for writing less code. They encourage you to think clearly about the separation of data and behavior in your applications. By using them as dedicated, well-defined data containers, you can build systems that are easier to read, maintain, and reason about.

We’ve built the foundation of a real-world application, modeling our domain with immutable and complex data classes, handling tricky default values with `default_factory`, and separating our concerns with a manager class. We even customized the behavior with advanced features like `order=True` and `__post_init__`. So the next time you find yourself writing another `__init__`, take a moment and let `@dataclass` do the heavy lifting for you.