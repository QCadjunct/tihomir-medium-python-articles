# Strategy Pattern in 3 Lines: The Power of First-Class Functions
#### How to replace complex Object-Oriented boilerplate with clean, functional Python using callables, type hints, and dispatch tables

**By Tihomir Manushev**  
*Dec 3, 2025 · 7 min read*

---

In the world of classical object-oriented programming — particularly in languages like Java or C++ — we are often taught to design systems as “Kingdoms of Nouns.” If you want to do something, you cannot simply do it. You must create an object, instantiate it, and then ask that object to do it for you.

Nowhere is this more evident than in the Strategy Pattern.

The textbook definition of the Strategy Pattern is sound: define a family of algorithms, encapsulate each one, and make them interchangeable. It allows the algorithm to vary independently from the clients that use it. In a strict OOP language, this usually results in an explosion of boilerplate: an Interface (the Strategy), several Concrete Implementations (the specific algorithms), and a Context (the class using the strategy).

But Python is different. In Python, functions are first-class objects. They are not second-class citizens that must hide inside a class method. They can be created at runtime, assigned to variables, stored in data structures, and — most importantly — passed as arguments to other functions.

When you fully embrace functions as first-class objects, the heavy machinery of the Strategy Pattern evaporates. What used to take a dozen files and an abstract base class can often be achieved in three lines of code.

---

### The Core Concept: Verbs as Objects

To understand why Python simplifies this pattern so drastically, we must look at the CPython internals.

In Python, everything is an object. This isn’t just a mantra; it’s a technical reality. A function defined with `def` is an instance of the function class. Like any other object (integers, strings, lists), a function object resides in the heap memory. It has attributes (like `__doc__` for docstrings or `__name__` for its name) and methods.

The magic lies in the `__call__` method. When you write `my_func()`, Python is essentially looking up the object `my_func` and invoking its `__call__` operator.

Because functions are just objects, we don’t need a wrapper class to transport logic. If the Strategy Pattern is about “interchangeable logic,” and a function is logic encapsulated in an object, then a function is a pre-packaged Strategy.

---

### The “Old School” Boilerplate

Let’s imagine we are building a logistics system for a shipping company, Hermes Logistics. We need to calculate shipping costs based on different tiers: Standard Ground, Air Express, and Owl Post (for magical deliveries).

In a strict OOP approach, we might write this:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Parcel:
    weight: float
    volume: float

# The Abstract Strategy
class ShippingStrategy(ABC):
    @abstractmethod
    def calculate(self, parcel: Parcel) -> float:
        pass

# Concrete Strategy 1
class StandardGround(ShippingStrategy):
    def calculate(self, parcel: Parcel) -> float:
        return parcel.weight * 1.5 + 10.0

# Concrete Strategy 2
class AirExpress(ShippingStrategy):
    def calculate(self, parcel: Parcel) -> float:
        return parcel.weight * 3.0 + (parcel.volume * 2.0)

# The Context
class ShippingCalculator:
    def __init__(self, strategy: ShippingStrategy):
        self.strategy = strategy

    def compute_cost(self, parcel: Parcel) -> float:
        return self.strategy.calculate(parcel)

# Usage
pkg = Parcel(weight=10, volume=5)
calculator = ShippingCalculator(AirExpress())
cost = calculator.compute_cost(pkg)
```

This is robust, strictly typed, and… incredibly verbose. We created three classes just to wrap simple mathematical formulas. We are treating the action of calculating as a noun (`AirExpress`), rather than a verb.

---

### Code Demonstration: The Pythonic Refactor

Let’s dismantle this structure using Python’s first-class functions. We don’t need the `ShippingStrategy` abstract base class, nor do we need the concrete classes.

We require:
1.  **The Context:** A function or class that consumes the logic.
2.  **The Strategies:** Plain functions.

Here is the modern Python 3.10+ implementation using `typing.Callable` (or `TypeAlias`) to ensure we maintain the same level of type safety as the OOP version.

```python
import logging
from dataclasses import dataclass
from typing import Callable, TypeAlias

# Configure logging for demonstration
logging.basicConfig(level=logging.INFO)

@dataclass(frozen=True)
class Parcel:
    """Immutable data structure for shipment details."""
    sku: str
    weight_kg: float
    volume_m3: float
    price: float

# 1. Define the Interface using TypeAlias (Python 3.10+)
# This effectively replaces the Abstract Base Class.
# It says: A ShippingStrategy is any callable that takes a Parcel and returns a float.
ShippingStrategy: TypeAlias = Callable[[Parcel], float]

# 2. Define the Strategies as plain functions
def standard_ground(p: Parcel) -> float:
    """Base rate + weight cost."""
    return 10.0 + (p.weight_kg * 1.5)

def air_express(p: Parcel) -> float:
    """High speed implies weight and volumetric calculations."""
    volumetric_weight = p.volume_m3 * 167  # IATA standard
    chargeable_weight = max(p.weight_kg, volumetric_weight)
    return chargeable_weight * 4.5

def owl_post(p: Parcel) -> float:
    """Flat rate for magical delivery, free for high value items."""
    if p.price > 1000:
        return 0.0
    return 25.0

# 3. The Context
class OrderProcessor:
    def __init__(self, strategy: ShippingStrategy):
        self.strategy = strategy

    def process_order(self, parcel: Parcel) -> None:
        cost = self.strategy(parcel)  # Direct invocation!
        logging.info(f"Shipping {parcel.sku} via {self.strategy.__name__}: ${cost:.2f}")

# --- Execution ---

item_1 = Parcel("NIMBUS-2000", weight_kg=15.0, volume_m3=0.2, price=2000.0)
item_2 = Parcel("TEXTBOOK-101", weight_kg=2.0, volume_m3=0.05, price=50.0)

# Strategy 1: Air Express
processor_air = OrderProcessor(air_express)
processor_air.process_order(item_1)

# Strategy 2: Owl Post
processor_owl = OrderProcessor(owl_post)
processor_owl.process_order(item_1)
```

---

### Deconstructing the Mechanics

1.  **The Type Alias:** `ShippingStrategy: TypeAlias = Callable[[Parcel], float]` replaces the entire Abstract Base Class. It tells type checkers (like Mypy) and IDEs exactly what signature is expected.
2.  **Direct Invocation:** Inside `OrderProcessor`, we call `self.strategy(parcel)`. We don’t need `self.strategy.calculate(parcel)`. The function is the object; we just call it.
3.  **Introspection:** Notice `self.strategy.__name__` in the logging. Because the strategy is a standard function object, we get metadata for free.

---

### Best Practice Implementation: The Dispatch Map

While passing functions manually is powerful, a common requirement in production systems is selecting a strategy based on user input (e.g., a string from a JSON payload or a database configuration).

Instead of a massive `if/elif/else` block, we can use a dictionary. This is often called a Dispatch Table. Because functions are hashable and can be stored in data structures, this pattern is incredibly efficient (O(1) lookup time).

Here is how to implement a robust, data-driven strategy selector:

```python
from typing import Final

# ... (Previous Parcel and function definitions assumed) ...

# A Registry mapping strategy codes to actual function objects
# Using Final to prevent accidental overwrites
SHIPPING_STRATEGIES: Final[dict[str, ShippingStrategy]] = {
    "ground": standard_ground,
    "air": air_express,
    "owl": owl_post,
}

def get_shipping_cost(parcel: Parcel, method_code: str) -> float:
    """
    Calculates cost dynamically based on a string code.
    
    Args:
        parcel: The item to ship.
        method_code: 'ground', 'air', or 'owl'.
    
    Returns:
        The calculated float cost.
        
    Raises:
        ValueError: If the method_code is unknown.
    """
    # 1. Fetch the function object from the dict
    strategy_func = SHIPPING_STRATEGIES.get(method_code)
    
    if not strategy_func:
        valid_keys = ", ".join(SHIPPING_STRATEGIES.keys())
        raise ValueError(f"Unknown shipping method: '{method_code}'. Valid: {valid_keys}")
    
    # 2. Execute the function
    return strategy_func(parcel)

# --- Real World Usage ---

# Imagine this data comes from an API request
incoming_request = {
    "sku": "POTION-KIT", 
    "weight": 5.0, 
    "volume": 0.1, 
    "price": 45.0, 
    "method": "ground"
}

pkg = Parcel(
    incoming_request["sku"], 
    incoming_request["weight"], 
    incoming_request["volume"], 
    incoming_request["price"]
)

try:
    cost = get_shipping_cost(pkg, incoming_request["method"])
    print(f"Calculated Cost: ${cost:.2f}")
except ValueError as e:
    print(f"Error: {e}")
```

**Why this is Production-Grade**

*   **Extensibility:** Adding a new shipping method requires zero changes to the `OrderProcessor` or `get_shipping_cost` logic. You simply write the new function and add one entry to the `SHIPPING_STRATEGIES` dictionary. This adheres strictly to the Open/Closed Principle.
*   **Safety:** The dictionary lookup provides a centralized place to handle “unknown strategy” errors.
*   **Testability:** You can easily unit test `standard_ground` in isolation without instantiating a complex context object.

---

### Advanced Twist: Parameterization with functools.partial

Sometimes a strategy needs initialization data. In OOP, you would pass this to the `__init__` of the concrete class. In functional Python, we use `functools.partial`.

Suppose the `standard_ground` rate changes dynamically based on the season.

```python
from functools import partial

def variable_ground_shipping(season_surcharge: float, p: Parcel) -> float:
    base = 10.0 + season_surcharge
    return base + (p.weight_kg * 1.5)

# Create a specialized version of the function with the surcharge "frozen"
christmas_shipping = partial(variable_ground_shipping, 5.0)  # $5 surcharge
summer_shipping = partial(variable_ground_shipping, 0.0)     # $0 surcharge

# These partials are still callables accepting a Parcel!
# They fit perfectly into our existing ShippingStrategy type alias.
assert isinstance(christmas_shipping(item_1), float)
```

`functools.partial` creates a new callable object that wraps your original function and the fixed arguments. It allows you to configure your strategies at startup time and pass them around as if they were simple one-argument functions.

---

### Conclusion

The Strategy Pattern is not dead; it has simply evolved. In Python, we do not need the scaffolding of Interfaces and Concrete Classes to achieve polymorphism. By recognizing that functions are first-class objects — entities that can be passed, stored, and manipulated — we can strip away the boilerplate and focus on the algorithms themselves.

When you treat functions as data, your code becomes flatter, easier to test, and significantly more readable. You aren’t just writing “scripts”; you are leveraging the full power of the Python Data Model. So, the next time you find yourself writing a class with a single method called `execute` or `run`, stop. You probably just need a function.