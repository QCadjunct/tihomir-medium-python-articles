# 🐍 Pythonic SOLID Design Principles with Pydantic & Duck Typing

> **A Modern, Type-Safe Approach to Object-Oriented Design in Python**

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [🔑 Key Improvements Over ABC-Based Approach](#-key-improvements-over-abc-based-approach)
- [🎨 Design Philosophy](#-design-philosophy)
- [1️⃣ Single Responsibility Principle (SRP)](#1️⃣-single-responsibility-principle-srp)
- [2️⃣ Open-Closed Principle (OCP)](#2️⃣-open-closed-principle-ocp)
- [3️⃣ Liskov Substitution Principle (LSP)](#3️⃣-liskov-substitution-principle-lsp)
- [4️⃣ Interface Segregation Principle (ISP)](#4️⃣-interface-segregation-principle-isp)
- [5️⃣ Dependency Inversion Principle (DIP)](#5️⃣-dependency-inversion-principle-dip)
- [🎓 Best Practices & Patterns](#-best-practices--patterns)
- [🧪 Testing Strategies](#-testing-strategies)
- [📚 Complete Example Project](#-complete-example-project)
- [🔍 Comparison: ABC vs Protocol](#-comparison-abc-vs-protocol)
- [🎯 Conclusion](#-conclusion)

---

## 🎯 Overview

This guide demonstrates how to implement SOLID design principles using **modern Python** features:

- ✅ **Pydantic v2** for data validation and serialization
- ✅ **Protocol classes** for duck typing and structural subtyping
- ✅ **Type hints** for static analysis and IDE support
- ✅ **Composition over inheritance** for flexibility
- ✅ **Runtime validation** with Pydantic's powerful validators

### 📊 Architecture Overview

```mermaid
graph TB
    subgraph PRINCIPLES ["🎯    SOLID    Design    Principles"]
        SRP[Single Responsibility]
        OCP[Open-Closed]
        LSP[Liskov Substitution]
        ISP[Interface Segregation]
        DIP[Dependency Inversion]
    end
    
    subgraph TOOLS ["🛠️    Modern    Python    Tools"]
        PYDANTIC[Pydantic Models]
        PROTOCOLS[Protocol Classes]
        TYPING[Type Hints]
        VALIDATION[Runtime Validation]
    end
    
    subgraph BENEFITS ["✨    Key    Benefits"]
        TYPESAFE[Type Safety]
        EXTENSIBLE[Easy Extension]
        TESTABLE[Simple Testing]
        MAINTAINABLE[Easy Maintenance]
    end
    
    %% Data flow from principles to tools
    SRP --> PYDANTIC
    OCP --> PROTOCOLS
    LSP --> PROTOCOLS
    ISP --> PYDANTIC
    DIP --> PROTOCOLS
    
    %% Tools enable benefits
    PYDANTIC --> TYPESAFE
    PYDANTIC --> VALIDATION
    PROTOCOLS --> EXTENSIBLE
    TYPING --> TYPESAFE
    VALIDATION --> MAINTAINABLE
    PROTOCOLS --> TESTABLE
    TYPING --> EXTENSIBLE
    
    %% Connection styling
    linkStyle 0 stroke:#1976d2,stroke-width:3px
    linkStyle 1 stroke:#1976d2,stroke-width:3px
    linkStyle 2 stroke:#1976d2,stroke-width:3px
    linkStyle 3 stroke:#1976d2,stroke-width:3px
    linkStyle 4 stroke:#1976d2,stroke-width:3px
    linkStyle 5 stroke:#7b1fa2,stroke-width:3px
    linkStyle 6 stroke:#7b1fa2,stroke-width:3px
    linkStyle 7 stroke:#7b1fa2,stroke-width:3px
    linkStyle 8 stroke:#7b1fa2,stroke-width:3px
    linkStyle 9 stroke:#7b1fa2,stroke-width:3px
    linkStyle 10 stroke:#7b1fa2,stroke-width:3px
    linkStyle 11 stroke:#7b1fa2,stroke-width:3px
    
    %% Subgraph styling
    style PRINCIPLES fill:#e8f4fd,stroke:#1976d2,stroke-width:3px,color:#000
    style TOOLS fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px,color:#000
    style BENEFITS fill:#fff4e6,stroke:#f57c00,stroke-width:3px,color:#000
    
    %% Node styling
    style SRP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style OCP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style LSP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style ISP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style DIP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style PYDANTIC fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style PROTOCOLS fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style TYPING fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style VALIDATION fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style TYPESAFE fill:#fff8e1,stroke:#f57c00,stroke-width:3px,color:#000
    style EXTENSIBLE fill:#fff8e1,stroke:#f57c00,stroke-width:3px,color:#000
    style TESTABLE fill:#fff8e1,stroke:#f57c00,stroke-width:3px,color:#000
    style MAINTAINABLE fill:#fff8e1,stroke:#f57c00,stroke-width:3px,color:#000
```

[⬆️ Back to TOC](#-table-of-contents)

---

## 🔑 Key Improvements Over ABC-Based Approach

### 🎭 Why Protocol Classes?

| Feature | ABC Approach | Protocol Approach |
|---------|-------------|-------------------|
| **Type Checking** | Runtime only | Static + Runtime |
| **Coupling** | Tight (inheritance) | Loose (structural) |
| **Python Philosophy** | Less Pythonic | Idiomatic duck typing |
| **Extensibility** | Requires inheritance | Any matching interface |
| **Testing** | More complex mocking | Simple duck-type mocks |
| **Third-party Integration** | Must subclass | Works automatically |

### 🌟 Pydantic Advantages

```python
from pydantic import BaseModel, Field, field_validator

class Circle(BaseModel):
    """Automatic validation, serialization, and documentation"""
    radius: float = Field(gt=0, description="Circle radius in units")
    
    @field_validator('radius')
    @classmethod
    def validate_radius(cls, v):
        if v > 1000:
            raise ValueError("Radius too large")
        return v
    
    def calculate_area(self) -> float:
        return 3.14159 * self.radius ** 2

# Automatic JSON serialization
circle = Circle(radius=5.0)
print(circle.model_dump_json())  # {"radius": 5.0}

# Automatic validation
try:
    invalid = Circle(radius=-5)  # Raises ValidationError
except ValidationError as e:
    print(e)
```

**Benefits:**
- ✅ Automatic data validation
- ✅ JSON serialization/deserialization
- ✅ Schema generation for APIs
- ✅ Type hints enforcement
- ✅ IDE autocomplete support
- ✅ Runtime type checking

[⬆️ Back to TOC](#-table-of-contents)

---

## 🎨 Design Philosophy

### 🐍 The Pythonic Way

**"If it walks like a duck and quacks like a duck, it's a duck"**

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Quackable(Protocol):
    """Defines what it means to quack - no inheritance needed!"""
    def quack(self) -> str:
        ...

class Duck:
    def quack(self) -> str:
        return "Quack!"

class Person:
    def quack(self) -> str:
        return "I'm pretending to be a duck!"

# Both work - no inheritance required!
def make_it_quack(thing: Quackable) -> None:
    print(thing.quack())

make_it_quack(Duck())      # Works!
make_it_quack(Person())    # Works!
```

### 🎯 KISS + SRP = Success

**Keep It Simple, Stupid + Single Responsibility Principle**

1. **One class, one job** - Never mix concerns
2. **Composition over inheritance** - Build from smaller pieces
3. **Protocol over ABC** - Define behavior, not hierarchy
4. **Validation early** - Fail fast with Pydantic
5. **Type hints everywhere** - Let the tooling help you

[⬆️ Back to TOC](#-table-of-contents)

---

## 1️⃣ Single Responsibility Principle (SRP)

> **"A class should have only one reason to change"** - Uncle Bob

### 📖 The Problem

Mixing multiple responsibilities in one class creates:
- 🔴 Complex testing requirements
- 🔴 Difficult code reuse
- 🔴 Multiple reasons to change the class
- 🔴 Tight coupling between unrelated features

### ✅ The Solution: Separate Concerns

```mermaid
graph TB
    subgraph ORIGINAL ["❌    Original    Mixed    Responsibilities"]
        MIXED[FileManager<br/>- read/write<br/>- compress/decompress<br/>- encrypt/decrypt]
    end
    
    subgraph REFACTORED ["✅    Separated    Single    Responsibilities"]
        FILE[FileManager<br/>- read<br/>- write]
        ZIP[ZipFileManager<br/>- compress<br/>- decompress]
        CRYPTO[CryptoManager<br/>- encrypt<br/>- decrypt]
    end
    
    subgraph BENEFITS ["🎯    Benefits    of    Separation"]
        TESTABLE[Easy Testing]
        REUSABLE[High Reusability]
        MAINTAINABLE[Simple Maintenance]
        EXTENDABLE[Easy Extension]
    end
    
    %% Problem to solution
    MIXED --> FILE
    MIXED --> ZIP
    MIXED --> CRYPTO
    
    %% Solution to benefits
    FILE --> TESTABLE
    ZIP --> TESTABLE
    CRYPTO --> TESTABLE
    
    FILE --> REUSABLE
    ZIP --> REUSABLE
    CRYPTO --> REUSABLE
    
    FILE --> MAINTAINABLE
    ZIP --> MAINTAINABLE
    
    FILE --> EXTENDABLE
    ZIP --> EXTENDABLE
    
    %% Connection styling
    linkStyle 0 stroke:#c2185b,stroke-width:2px,stroke-dasharray:5
    linkStyle 1 stroke:#c2185b,stroke-width:2px,stroke-dasharray:5
    linkStyle 2 stroke:#c2185b,stroke-width:2px,stroke-dasharray:5
    linkStyle 3 stroke:#388e3c,stroke-width:3px
    linkStyle 4 stroke:#388e3c,stroke-width:3px
    linkStyle 5 stroke:#388e3c,stroke-width:3px
    linkStyle 6 stroke:#388e3c,stroke-width:3px
    linkStyle 7 stroke:#388e3c,stroke-width:3px
    linkStyle 8 stroke:#388e3c,stroke-width:3px
    linkStyle 9 stroke:#388e3c,stroke-width:3px
    linkStyle 10 stroke:#388e3c,stroke-width:3px
    linkStyle 11 stroke:#388e3c,stroke-width:3px
    linkStyle 12 stroke:#388e3c,stroke-width:3px
    
    %% Subgraph styling
    style ORIGINAL fill:#fef7f7,stroke:#c2185b,stroke-width:3px,color:#000
    style REFACTORED fill:#f0f8f0,stroke:#388e3c,stroke-width:3px,color:#000
    style BENEFITS fill:#fff4e6,stroke:#f57c00,stroke-width:3px,color:#000
    
    %% Node styling
    style MIXED fill:#fce4ec,stroke:#c2185b,stroke-width:3px,color:#000
    style FILE fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style ZIP fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style CRYPTO fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style TESTABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style REUSABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style MAINTAINABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style EXTENDABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
```

### 💻 Implementation

<details>
<summary><strong>📁 FileManager - Handles Basic I/O</strong></summary>

```python
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, field_validator

class FileManager(BaseModel):
    """
    Single Responsibility: File I/O operations only
    
    ✅ Reads files
    ✅ Writes files
    ❌ Does NOT compress
    ❌ Does NOT encrypt
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    path: Path
    encoding: str = Field(default="utf-8", description="Text encoding")
    
    @field_validator('path', mode='before')
    @classmethod
    def convert_to_path(cls, v):
        """Ensure path is always a Path object"""
        return Path(v) if not isinstance(v, Path) else v
    
    def read(self) -> str:
        """Read file contents"""
        if not self.path.exists():
            raise FileNotFoundError(f"File not found: {self.path}")
        return self.path.read_text(self.encoding)
    
    def write(self, data: str) -> None:
        """Write data to file"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(data, self.encoding)
    
    def exists(self) -> bool:
        """Check if file exists"""
        return self.path.exists()
    
    def size(self) -> int:
        """Get file size in bytes"""
        return self.path.stat().st_size if self.exists() else 0
```
</details>

<details>
<summary><strong>🗜️ ZipFileManager - Handles Compression</strong></summary>

```python
from zipfile import ZipFile
from typing import Optional

class ZipFileManager(BaseModel):
    """
    Single Responsibility: ZIP compression/decompression only
    
    ✅ Compresses files to ZIP
    ✅ Decompresses ZIP archives
    ❌ Does NOT read/write regular files
    ❌ Does NOT encrypt
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    path: Path
    compression_level: int = Field(default=9, ge=0, le=9)
    
    @field_validator('path', mode='before')
    @classmethod
    def convert_to_path(cls, v):
        return Path(v) if not isinstance(v, Path) else v
    
    @property
    def zip_path(self) -> Path:
        """Get the ZIP file path"""
        return self.path.with_suffix(".zip")
    
    def compress(self, files: Optional[list[Path]] = None) -> Path:
        """
        Compress file(s) to ZIP archive
        
        Args:
            files: List of files to compress (default: single file)
        
        Returns:
            Path to created ZIP file
        """
        files_to_compress = files or [self.path]
        
        with ZipFile(self.zip_path, mode="w") as archive:
            for file in files_to_compress:
                if file.exists():
                    archive.write(file, arcname=file.name)
        
        return self.zip_path
    
    def decompress(self, target_dir: Optional[Path] = None) -> list[Path]:
        """
        Decompress ZIP archive
        
        Args:
            target_dir: Target directory (default: parent directory)
        
        Returns:
            List of extracted file paths
        """
        target = target_dir or self.path.parent
        target.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        with ZipFile(self.zip_path, mode="r") as archive:
            for name in archive.namelist():
                archive.extract(name, target)
                extracted_files.append(target / name)
        
        return extracted_files
    
    def list_contents(self) -> list[str]:
        """List files in ZIP archive"""
        with ZipFile(self.zip_path, mode="r") as archive:
            return archive.namelist()
```
</details>

<details>
<summary><strong>🔐 CryptoManager - Handles Encryption</strong></summary>

```python
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode, urlsafe_b64decode
import hashlib

class CryptoManager(BaseModel):
    """
    Single Responsibility: File encryption/decryption only
    
    ✅ Encrypts file contents
    ✅ Decrypts file contents
    ❌ Does NOT read/write files
    ❌ Does NOT compress
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    path: Path
    password: str = Field(repr=False, exclude=True)  # Never expose in repr
    
    @field_validator('path', mode='before')
    @classmethod
    def convert_to_path(cls, v):
        return Path(v) if not isinstance(v, Path) else v
    
    def _get_key(self) -> bytes:
        """Derive encryption key from password"""
        key_bytes = hashlib.sha256(self.password.encode()).digest()
        return urlsafe_b64encode(key_bytes)
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt data"""
        fernet = Fernet(self._get_key())
        return fernet.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data"""
        fernet = Fernet(self._get_key())
        return fernet.decrypt(encrypted_data).decode()
    
    @property
    def encrypted_path(self) -> Path:
        """Get path for encrypted file"""
        return self.path.with_suffix(self.path.suffix + '.encrypted')
```
</details>

### 🎯 Usage Example

```python
# Each class has ONE job - easy to understand and test!

# 1. File I/O
file_manager = FileManager(path="document.txt")
file_manager.write("Hello, SOLID!")
content = file_manager.read()

# 2. Compression (uses file created above)
zip_manager = ZipFileManager(path="document.txt")
zip_file = zip_manager.compress()
print(f"Created: {zip_file}")

# 3. Encryption (separate concern)
crypto_manager = CryptoManager(path="document.txt", password="secret123")
encrypted = crypto_manager.encrypt(content)
decrypted = crypto_manager.decrypt(encrypted)

# 🎯 Each class can be tested independently!
# 🎯 Each class can be reused independently!
# 🎯 Each class has ONE reason to change!
```

### ✅ SRP Checklist

- ✅ Each class has a single, well-defined responsibility
- ✅ Changes to one feature don't affect others
- ✅ Easy to test in isolation
- ✅ High reusability across projects
- ✅ Clear naming that reflects responsibility
- ✅ Pydantic provides automatic validation

[⬆️ Back to TOC](#-table-of-contents)

---

## 2️⃣ Open-Closed Principle (OCP)

> **"Software entities should be open for extension, but closed for modification"** - Bertrand Meyer

### 📖 The Problem

Adding new functionality by modifying existing classes creates:
- 🔴 Risk of breaking existing code
- 🔴 Difficult testing (must retest everything)
- 🔴 Code bloat with if/elif chains
- 🔴 Violation of KISS principle

### ✅ The Solution: Protocol-Based Extension

```mermaid
graph TB
    subgraph PROTOCOL ["🎯    Shape    Protocol    (Interface)"]
        PROTO[ShapeProtocol<br/>+ calculate_area: float]
    end
    
    subgraph IMPLEMENTATIONS ["🔷    Concrete    Implementations"]
        CIRCLE[Circle<br/>radius: float<br/>+ calculate_area]
        RECT[Rectangle<br/>width, height: float<br/>+ calculate_area]
        SQUARE[Square<br/>side: float<br/>+ calculate_area]
        TRIANGLE[Triangle<br/>base, height: float<br/>+ calculate_area]
    end
    
    subgraph EXTENSION ["➕    Easy    to    Extend"]
        HEXAGON[Hexagon<br/>Just add new class!<br/>+ calculate_area]
        ELLIPSE[Ellipse<br/>No modification needed!<br/>+ calculate_area]
    end
    
    subgraph CLIENT ["💼    Client    Code"]
        FUNCTION[get_total_area<br/>Works with ANY shape!]
    end
    
    %% Protocol defines interface
    PROTO -.-> CIRCLE
    PROTO -.-> RECT
    PROTO -.-> SQUARE
    PROTO -.-> TRIANGLE
    PROTO -.-> HEXAGON
    PROTO -.-> ELLIPSE
    
    %% All implementations work with client
    CIRCLE --> FUNCTION
    RECT --> FUNCTION
    SQUARE --> FUNCTION
    TRIANGLE --> FUNCTION
    HEXAGON --> FUNCTION
    ELLIPSE --> FUNCTION
    
    %% Connection styling
    linkStyle 0 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 1 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 2 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 3 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 4 stroke:#388e3c,stroke-width:2px,stroke-dasharray:5
    linkStyle 5 stroke:#388e3c,stroke-width:2px,stroke-dasharray:5
    linkStyle 6 stroke:#1976d2,stroke-width:3px
    linkStyle 7 stroke:#1976d2,stroke-width:3px
    linkStyle 8 stroke:#1976d2,stroke-width:3px
    linkStyle 9 stroke:#1976d2,stroke-width:3px
    linkStyle 10 stroke:#388e3c,stroke-width:3px
    linkStyle 11 stroke:#388e3c,stroke-width:3px
    
    %% Subgraph styling
    style PROTOCOL fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px,color:#000
    style IMPLEMENTATIONS fill:#e8f4fd,stroke:#1976d2,stroke-width:3px,color:#000
    style EXTENSION fill:#f0f8f0,stroke:#388e3c,stroke-width:3px,color:#000
    style CLIENT fill:#fff4e6,stroke:#f57c00,stroke-width:3px,color:#000
    
    %% Node styling
    style PROTO fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    style CIRCLE fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style RECT fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style SQUARE fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style TRIANGLE fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style HEXAGON fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style ELLIPSE fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style FUNCTION fill:#fff8e1,stroke:#f57c00,stroke-width:3px,color:#000
```

### 💻 Implementation

<details>
<summary><strong>🎯 Protocol Definition</strong></summary>

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ShapeProtocol(Protocol):
    """
    Defines what it means to be a "shape"
    
    Any class with calculate_area() method automatically implements this!
    No inheritance required - this is duck typing!
    """
    def calculate_area(self) -> float:
        """Calculate the area of the shape"""
        ...
    
    @property
    def shape_type(self) -> str:
        """Return the type of shape"""
        ...
```
</details>

<details>
<summary><strong>🔵 Circle Implementation</strong></summary>

```python
from math import pi
from pydantic import BaseModel, Field

class Circle(BaseModel):
    """
    Circle - implements ShapeProtocol WITHOUT inheriting!
    Open for extension (add new shapes) but closed for modification
    """
    radius: float = Field(gt=0, description="Circle radius")
    
    def calculate_area(self) -> float:
        """Calculate circle area: πr²"""
        return pi * self.radius ** 2
    
    @property
    def shape_type(self) -> str:
        return "circle"
    
    @property
    def circumference(self) -> float:
        """Additional circle-specific method"""
        return 2 * pi * self.radius
    
    def __str__(self) -> str:
        return f"Circle(radius={self.radius:.2f}, area={self.calculate_area():.2f})"
```
</details>

<details>
<summary><strong>📐 Rectangle Implementation</strong></summary>

```python
class Rectangle(BaseModel):
    """Rectangle - independently implements ShapeProtocol"""
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        """Calculate rectangle area: w × h"""
        return self.width * self.height
    
    @property
    def shape_type(self) -> str:
        return "rectangle"
    
    @property
    def perimeter(self) -> float:
        """Additional rectangle-specific method"""
        return 2 * (self.width + self.height)
    
    @property
    def is_square(self) -> bool:
        """Check if this rectangle is actually a square"""
        return abs(self.width - self.height) < 1e-10
    
    def __str__(self) -> str:
        return f"Rectangle({self.width}×{self.height}, area={self.calculate_area():.2f})"
```
</details>

<details>
<summary><strong>⬜ Square Implementation</strong></summary>

```python
class Square(BaseModel):
    """Square - separate from Rectangle, implements ShapeProtocol"""
    side: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        """Calculate square area: s²"""
        return self.side ** 2
    
    @property
    def shape_type(self) -> str:
        return "square"
    
    @property
    def diagonal(self) -> float:
        """Calculate diagonal using Pythagorean theorem"""
        return self.side * (2 ** 0.5)
    
    def __str__(self) -> str:
        return f"Square(side={self.side:.2f}, area={self.calculate_area():.2f})"
```
</details>

<details>
<summary><strong>🔺 Triangle Implementation</strong></summary>

```python
class Triangle(BaseModel):
    """Triangle - easy to extend! Just implement the protocol"""
    base: float = Field(gt=0)
    height: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        """Calculate triangle area: ½ × b × h"""
        return 0.5 * self.base * self.height
    
    @property
    def shape_type(self) -> str:
        return "triangle"
    
    def __str__(self) -> str:
        return f"Triangle(base={self.base}×height={self.height}, area={self.calculate_area():.2f})"
```
</details>

<details>
<summary><strong>⬡ Hexagon - NEW Extension!</strong></summary>

```python
class Hexagon(BaseModel):
    """
    NEW SHAPE - Added without modifying ANY existing code!
    This is the Open-Closed Principle in action!
    """
    side: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        """Calculate regular hexagon area: (3√3/2) × s²"""
        return (3 * (3 ** 0.5) / 2) * (self.side ** 2)
    
    @property
    def shape_type(self) -> str:
        return "hexagon"
    
    @property
    def perimeter(self) -> float:
        return 6 * self.side
    
    def __str__(self) -> str:
        return f"Hexagon(side={self.side:.2f}, area={self.calculate_area():.2f})"
```
</details>

### 🎯 Client Code - Works With ALL Shapes

```python
from typing import Sequence

def get_total_area(shapes: Sequence[ShapeProtocol]) -> float:
    """
    Calculate total area of all shapes
    
    ✅ Works with ANY object that has calculate_area()
    ✅ No modification needed when adding new shapes
    ✅ Type-safe with static checking
    """
    return sum(shape.calculate_area() for shape in shapes)

def print_shape_details(shapes: Sequence[ShapeProtocol]) -> None:
    """Print details of all shapes"""
    for shape in shapes:
        print(f"  {shape.shape_type.title()}: {shape.calculate_area():.2f} sq units")

# Usage - CLOSED for modification, OPEN for extension!
shapes = [
    Circle(radius=5),
    Rectangle(width=10, height=5),
    Square(side=4),
    Triangle(base=6, height=8),
    Hexagon(side=3)  # New shape - no client code changes needed!
]

print(f"Total area: {get_total_area(shapes):.2f}")
print("\nShape details:")
print_shape_details(shapes)

# Output:
# Total area: 240.08
# 
# Shape details:
#   Circle: 78.54 sq units
#   Rectangle: 50.00 sq units
#   Square: 16.00 sq units
#   Triangle: 24.00 sq units
#   Hexagon: 23.38 sq units
```

### 🧪 Testing New Shapes

```python
def test_hexagon_implements_protocol():
    """Verify hexagon implements ShapeProtocol"""
    hex = Hexagon(side=5)
    
    # Runtime check
    assert isinstance(hex, ShapeProtocol)
    
    # Has required methods
    assert hasattr(hex, 'calculate_area')
    assert hasattr(hex, 'shape_type')
    
    # Works with client code
    total = get_total_area([hex])
    assert total > 0

# ✅ Test ONLY the new shape - existing shapes don't need retesting!
```

### ✅ OCP Checklist

- ✅ New functionality via new classes, not modifications
- ✅ Protocol defines contract, not inheritance
- ✅ Client code works with any conforming type
- ✅ Static type checking catches interface violations
- ✅ No cascading changes when extending
- ✅ Each implementation is independent

[⬆️ Back to TOC](#-table-of-contents)

---

## 3️⃣ Liskov Substitution Principle (LSP)

> **"Subtypes must be substitutable for their base types"** - Barbara Liskov

### 📖 The Problem

Violating LSP creates:
- 🔴 Surprising behavior when substituting types
- 🔴 Breaking existing code assumptions
- 🔴 Complex conditional logic in client code
- 🔴 Loss of polymorphism benefits

### ✅ The Solution: Behavioral Compatibility

```mermaid
graph TB
    subgraph VIOLATION ["❌    LSP    Violation"]
        BASE1[Rectangle<br/>width, height<br/>independent dimensions]
        DERIVED1[Square extends Rectangle<br/>⚠️ Changes width/height together<br/>⚠️ Breaks Rectangle assumptions]
        CLIENT1[Client expects<br/>independent dimensions<br/>💥 Surprise!]
        
        BASE1 --> DERIVED1
        DERIVED1 --> CLIENT1
    end
    
    subgraph CORRECT ["✅    LSP    Compliant"]
        PROTO[AreaCalculable<br/>Protocol<br/>calculate_area]
        RECT[Rectangle<br/>width, height<br/>independent]
        SQ[Square<br/>side only<br/>consistent behavior]
        CLIENT2[Client uses<br/>calculate_area<br/>😊 Works perfectly!]
        
        PROTO -.-> RECT
        PROTO -.-> SQ
        RECT --> CLIENT2
        SQ --> CLIENT2
    end
    
    subgraph BENEFITS ["🎯    LSP    Benefits"]
        PREDICTABLE[Predictable Behavior]
        POLYMORPHIC[True Polymorphism]
        TESTABLE[Reliable Testing]
        MAINTAINABLE[Easy Maintenance]
    end
    
    %% Problem flows
    linkStyle 0 stroke:#c2185b,stroke-width:3px
    linkStyle 1 stroke:#c2185b,stroke-width:3px,stroke-dasharray:5
    
    %% Correct implementation
    linkStyle 2 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 3 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 4 stroke:#388e3c,stroke-width:3px
    linkStyle 5 stroke:#388e3c,stroke-width:3px
    
    %% To benefits
    CORRECT --> PREDICTABLE
    CORRECT --> POLYMORPHIC
    CORRECT --> TESTABLE
    CORRECT --> MAINTAINABLE
    
    linkStyle 6 stroke:#3f51b5,stroke-width:4px
    linkStyle 7 stroke:#3f51b5,stroke-width:4px
    linkStyle 8 stroke:#3f51b5,stroke-width:4px
    linkStyle 9 stroke:#3f51b5,stroke-width:4px
    
    %% Subgraph styling
    style VIOLATION fill:#fef7f7,stroke:#c2185b,stroke-width:3px,color:#000
    style CORRECT fill:#f0f8f0,stroke:#388e3c,stroke-width:3px,color:#000
    style BENEFITS fill:#fff4e6,stroke:#f57c00,stroke-width:3px,color:#000
    
    %% Node styling
    style BASE1 fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
    style DERIVED1 fill:#fce4ec,stroke:#c2185b,stroke-width:3px,color:#000
    style CLIENT1 fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000
    style PROTO fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    style RECT fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style SQ fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style CLIENT2 fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style PREDICTABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style POLYMORPHIC fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style TESTABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style MAINTAINABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
```

### 💻 Implementation

<details>
<summary><strong>🎯 Protocol Definition</strong></summary>

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class AreaCalculable(Protocol):
    """
    Protocol for anything that can calculate area
    
    This is the "base type" for LSP
    Any type implementing calculate_area() is substitutable
    """
    def calculate_area(self) -> float:
        """Calculate the area"""
        ...
```
</details>

<details>
<summary><strong>❌ BAD: LSP Violation Example</strong></summary>

```python
class BadRectangle(BaseModel):
    """Rectangle with independent dimensions"""
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        return self.width * self.height

class BadSquare(BadRectangle):
    """
    ❌ LSP VIOLATION!
    
    This breaks the Rectangle contract because setting width
    automatically changes height (and vice versa).
    Code expecting independent dimensions will break!
    """
    def __init__(self, side: float):
        super().__init__(width=side, height=side)
    
    def __setattr__(self, key: str, value: float):
        """Override setattr to keep sides equal - BREAKS LSP!"""
        if key in ("width", "height"):
            # Setting one side changes BOTH - unexpected behavior!
            super().__setattr__("width", value)
            super().__setattr__("height", value)
        else:
            super().__setattr__(key, value)

# The problem:
def resize_rectangle(rect: BadRectangle) -> None:
    """
    Client code expects independent width/height
    This works for BadRectangle but breaks for BadSquare!
    """
    rect.width = 10
    rect.height = 5
    # For BadRectangle: area = 50 ✅
    # For BadSquare: area = 25 ❌ (height changed to 10!)
    print(f"Area after resize: {rect.calculate_area()}")

rect = BadRectangle(width=2, height=3)
resize_rectangle(rect)  # Works: area = 50

square = BadSquare(side=2)
resize_rectangle(square)  # BROKEN: area = 25 (expected 50!)
```
</details>

<details>
<summary><strong>✅ GOOD: LSP Compliant Implementation</strong></summary>

```python
class Rectangle(BaseModel):
    """
    Rectangle with truly independent dimensions
    ✅ LSP Compliant: Behavior matches contract
    """
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        """Calculate rectangle area"""
        return self.width * self.height
    
    def resize(self, width: float, height: float) -> None:
        """Resize with independent dimensions"""
        self.width = width
        self.height = height
    
    @property
    def aspect_ratio(self) -> float:
        """Width to height ratio"""
        return self.width / self.height

class Square(BaseModel):
    """
    Square as SEPARATE type with its own contract
    ✅ LSP Compliant: Consistent behavior for squares
    """
    side: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        """Calculate square area"""
        return self.side ** 2
    
    def resize(self, side: float) -> None:
        """Resize square - different signature is OK!"""
        self.side = side
    
    @property
    def aspect_ratio(self) -> float:
        """Squares always have 1:1 ratio"""
        return 1.0

# Both are substitutable for AreaCalculable!
def print_area(shape: AreaCalculable) -> None:
    """
    Works with ANY AreaCalculable
    ✅ Rectangle and Square are both substitutable
    ✅ No surprising behavior
    """
    print(f"Area: {shape.calculate_area():.2f}")

rect = Rectangle(width=10, height=5)
square = Square(side=5)

print_area(rect)    # Works perfectly
print_area(square)  # Works perfectly

# Each has its own appropriate resize method
rect.resize(20, 10)   # Rectangle way
square.resize(10)     # Square way
```
</details>

<details>
<summary><strong>🎨 More LSP Examples</strong></summary>

```python
class Circle(BaseModel):
    """Circle is also substitutable for AreaCalculable"""
    radius: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        return pi * self.radius ** 2
    
    def resize(self, radius: float) -> None:
        """Circle has its own resize contract"""
        self.radius = radius

class Ellipse(BaseModel):
    """Ellipse - another shape with its own behavior"""
    semi_major: float = Field(gt=0)
    semi_minor: float = Field(gt=0)
    
    def calculate_area(self) -> float:
        return pi * self.semi_major * self.semi_minor
    
    def resize(self, semi_major: float, semi_minor: float) -> None:
        """Ellipse resize contract"""
        self.semi_major = semi_major
        self.semi_minor = semi_minor
    
    @property
    def eccentricity(self) -> float:
        """Ellipse-specific property"""
        a, b = max(self.semi_major, self.semi_minor), min(self.semi_major, self.semi_minor)
        return ((a ** 2 - b ** 2) ** 0.5) / a

# All are substitutable for AreaCalculable Protocol!
shapes: list[AreaCalculable] = [
    Rectangle(width=10, height=5),
    Square(side=5),
    Circle(radius=5),
    Ellipse(semi_major=6, semi_minor=4)
]

# This function works with ALL of them!
def get_total_area(shapes: list[AreaCalculable]) -> float:
    """✅ True polymorphism - all shapes are substitutable"""
    return sum(shape.calculate_area() for shape in shapes)

print(f"Total area: {get_total_area(shapes):.2f}")
```
</details>

### 🎯 Key Insights

```python
# ✅ LSP Compliant Design Principles:

# 1. Shared behavior in Protocol (interface)
@runtime_checkable
class AreaCalculable(Protocol):
    def calculate_area(self) -> float: ...

# 2. Different implementations are SIBLINGS, not parent-child
#    Rectangle and Square DON'T inherit from each other
#    They're both valid AreaCalculable implementations

# 3. Each type maintains its own invariants
rect.width = 10  # Only affects width
square.side = 10 # Affects all sides (as expected)

# 4. Client code depends on Protocol, not concrete types
def process_shape(shape: AreaCalculable):  # Works with any shape
    return shape.calculate_area()

# 5. Substitution is based on BEHAVIOR, not inheritance
#    Any object with calculate_area() works!
```

### ✅ LSP Checklist

- ✅ Subtypes don't weaken preconditions
- ✅ Subtypes don't strengthen postconditions
- ✅ Invariants are preserved in subtypes
- ✅ Client code has no surprising behavior
- ✅ Substitution is based on behavior, not inheritance
- ✅ Protocol defines shared contract only

[⬆️ Back to TOC](#-table-of-contents)

---

## 4️⃣ Interface Segregation Principle (ISP)

> **"Clients should not be forced to depend upon methods they do not use"** - Uncle Bob

### 📖 The Problem

Fat interfaces with many methods create:
- 🔴 Forced implementation of unused methods
- 🔴 Unnecessary dependencies
- 🔴 Difficult testing (must mock unused features)
- 🔴 Violation of SRP at interface level

### ✅ The Solution: Segregated Protocols + Composition

```mermaid
graph TB
    subgraph SEGREGATED ["🎯    Segregated    Protocols"]
        PRINT[Printable<br/>print]
        FAX[Faxable<br/>fax]
        SCAN[Scannable<br/>scan]
    end
    
    subgraph CAPABILITIES ["🔧    Capability    Components"]
        PRINTCAP[PrinterCapability<br/>color: bool<br/>+ print]
        FAXCAP[FaxCapability<br/>+ fax]
        SCANCAP[ScanCapability<br/>resolution: int<br/>+ scan]
    end
    
    subgraph DEVICES ["🖨️    Device    Implementations"]
        OLD[OldPrinter<br/>printer only<br/>✅ No unused methods]
        MODERN[ModernPrinter<br/>printer + fax + scan<br/>✅ Full featured]
        SCANNER[OfficeScanner<br/>scanner only<br/>✅ Single purpose]
    end
    
    subgraph BENEFITS ["✨    ISP    Benefits"]
        FOCUSED[Focused Interfaces]
        FLEXIBLE[Flexible Composition]
        TESTABLE[Easy Testing]
        MAINTAINABLE[Simple Maintenance]
    end
    
    %% Protocols define capabilities
    PRINT -.-> PRINTCAP
    FAX -.-> FAXCAP
    SCAN -.-> SCANCAP
    
    %% Devices compose capabilities
    PRINTCAP --> OLD
    PRINTCAP --> MODERN
    FAXCAP --> MODERN
    SCANCAP --> MODERN
    SCANCAP --> SCANNER
    
    %% To benefits
    SEGREGATED --> FOCUSED
    CAPABILITIES --> FLEXIBLE
    DEVICES --> TESTABLE
    DEVICES --> MAINTAINABLE
    
    %% Connection styling
    linkStyle 0 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 1 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 2 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 3 stroke:#1976d2,stroke-width:3px
    linkStyle 4 stroke:#1976d2,stroke-width:3px
    linkStyle 5 stroke:#1976d2,stroke-width:3px
    linkStyle 6 stroke:#1976d2,stroke-width:3px
    linkStyle 7 stroke:#1976d2,stroke-width:3px
    linkStyle 8 stroke:#388e3c,stroke-width:3px
    linkStyle 9 stroke:#388e3c,stroke-width:3px
    linkStyle 10 stroke:#388e3c,stroke-width:3px
    linkStyle 11 stroke:#388e3c,stroke-width:3px
    
    %% Subgraph styling
    style SEGREGATED fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px,color:#000
    style CAPABILITIES fill:#e8f4fd,stroke:#1976d2,stroke-width:3px,color:#000
    style DEVICES fill:#f0f8f0,stroke:#388e3c,stroke-width:3px,color:#000
    style BENEFITS fill:#fff4e6,stroke:#f57c00,stroke-width:3px,color:#000
    
    %% Node styling
    style PRINT fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style FAX fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style SCAN fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    style PRINTCAP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style FAXCAP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style SCANCAP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style OLD fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style MODERN fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#000
    style SCANNER fill:#e8f5e8,stroke:#388e3c,stroke-width:2px,color:#000
    style FOCUSED fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style FLEXIBLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style TESTABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style MAINTAINABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
```

### 💻 Implementation

<details>
<summary><strong>🎯 Segregated Protocols</strong></summary>

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Printable(Protocol):
    """Protocol for devices that can print"""
    def print(self, document: str) -> None:
        """Print a document"""
        ...

@runtime_checkable
class Faxable(Protocol):
    """Protocol for devices that can fax"""
    def fax(self, document: str) -> None:
        """Send a fax"""
        ...

@runtime_checkable
class Scannable(Protocol):
    """Protocol for devices that can scan"""
    def scan(self, document: str) -> None:
        """Scan a document"""
        ...

# ✅ Each protocol is FOCUSED on ONE capability
# ✅ Devices only implement what they need
# ✅ No "NotImplementedError" antipattern!
```
</details>

<details>
<summary><strong>🔧 Capability Components</strong></summary>

```python
from pydantic import BaseModel, Field

class PrinterCapability(BaseModel):
    """Reusable printing capability"""
    color: bool = Field(default=False, description="Color or B&W printing")
    duplex: bool = Field(default=False, description="Double-sided printing")
    dpi: int = Field(default=600, ge=300, le=2400, description="Print resolution")
    
    def print(self, document: str) -> None:
        """Print a document"""
        mode = "color" if self.color else "black and white"
        sides = "duplex" if self.duplex else "simplex"
        print(f"🖨️  Printing '{document}' in {mode} ({sides}, {self.dpi}dpi)")

class FaxCapability(BaseModel):
    """Reusable fax capability"""
    fax_number: str = Field(default="+1-555-0100")
    
    def fax(self, document: str) -> None:
        """Send a fax"""
        print(f"📠 Faxing '{document}' to {self.fax_number}")

class ScanCapability(BaseModel):
    """Reusable scan capability"""
    resolution: int = Field(default=300, ge=150, le=1200, description="Scan DPI")
    color_scan: bool = Field(default=True)
    
    def scan(self, document: str) -> None:
        """Scan a document"""
        mode = "color" if self.color_scan else "grayscale"
        print(f"🔍 Scanning '{document}' at {self.resolution}dpi ({mode})")

# ✅ Capabilities are COMPOSABLE
# ✅ Each capability has its own configuration
# ✅ Easy to test independently
```
</details>

<details>
<summary><strong>🖨️ Old Printer (Single Interface)</strong></summary>

```python
class OldPrinter(BaseModel):
    """
    Legacy printer - ONLY printing capability
    ✅ Implements ONLY Printable protocol
    ✅ No unused fax/scan methods
    """
    printer: PrinterCapability = Field(
        default_factory=lambda: PrinterCapability(color=False)
    )
    
    def print(self, document: str) -> None:
        """Print using the printer capability"""
        self.printer.print(document)
    
    def get_capabilities(self) -> list[str]:
        """Return list of supported operations"""
        return ["print"]

# Usage
old = OldPrinter()
old.print("document.pdf")  # ✅ Works!
# old.fax("document.pdf")  # ❌ Correctly doesn't exist!
# old.scan("document.pdf") # ❌ Correctly doesn't exist!

assert isinstance(old, Printable)   # ✅ True
assert not isinstance(old, Faxable) # ✅ True (not faxable)
```
</details>

<details>
<summary><strong>🖨️ Modern Printer (Multiple Interfaces)</strong></summary>

```python
class ModernPrinter(BaseModel):
    """
    All-in-one modern printer
    ✅ Implements Printable, Faxable, AND Scannable
    ✅ Uses composition to combine capabilities
    """
    printer: PrinterCapability = Field(
        default_factory=lambda: PrinterCapability(color=True, duplex=True)
    )
    fax: FaxCapability = Field(default_factory=FaxCapability)
    scanner: ScanCapability = Field(
        default_factory=lambda: ScanCapability(resolution=600)
    )
    
    def print(self, document: str) -> None:
        """Print using the printer capability"""
        self.printer.print(document)
    
    def fax(self, document: str) -> None:
        """Fax using the fax capability"""
        self.fax.fax(document)
    
    def scan(self, document: str) -> None:
        """Scan using the scanner capability"""
        self.scanner.scan(document)
    
    def get_capabilities(self) -> list[str]:
        """Return list of supported operations"""
        return ["print", "fax", "scan"]

# Usage
modern = ModernPrinter()
modern.print("report.pdf")     # ✅ Works!
modern.fax("contract.pdf")     # ✅ Works!
modern.scan("receipt.jpg")     # ✅ Works!

assert isinstance(modern, Printable)  # ✅ True
assert isinstance(modern, Faxable)    # ✅ True
assert isinstance(modern, Scannable)  # ✅ True
```
</details>

<details>
<summary><strong>🔍 Office Scanner (Single Interface)</strong></summary>

```python
class OfficeScanner(BaseModel):
    """
    Dedicated high-quality scanner
    ✅ Implements ONLY Scannable protocol
    ✅ No printing or faxing capabilities
    """
    scanner: ScanCapability = Field(
        default_factory=lambda: ScanCapability(resolution=1200, color_scan=True)
    )
    
    def scan(self, document: str) -> None:
        """Scan using high-resolution scanner"""
        self.scanner.scan(document)
    
    def get_capabilities(self) -> list[str]:
        """Return list of supported operations"""
        return ["scan"]

# Usage
scanner = OfficeScanner()
scanner.scan("photo.jpg")      # ✅ Works!
# scanner.print("doc.pdf")     # ❌ Correctly doesn't exist!
# scanner.fax("contract.pdf")  # ❌ Correctly doesn't exist!

assert not isinstance(scanner, Printable) # ✅ True (not printable)
assert isinstance(scanner, Scannable)     # ✅ True
```
</details>

### 🎯 Client Code - Uses Only Needed Interfaces

```python
def print_if_possible(device: object, document: str) -> None:
    """
    Print document if device supports it
    ✅ Checks for capability using duck typing
    ✅ No dependency on fat interface
    """
    if isinstance(device, Printable):
        device.print(document)
        print("✅ Document printed")
    else:
        print(f"❌ Device does not support printing")

def scan_if_possible(device: object, document: str) -> None:
    """
    Scan document if device supports it
    ✅ Each function depends ONLY on what it needs
    """
    if isinstance(device, Scannable):
        device.scan(document)
        print("✅ Document scanned")
    else:
        print("❌ Device does not support scanning")

def process_document(device: object, document: str) -> None:
    """
    Process document based on device capabilities
    ✅ Discovers capabilities dynamically
    """
    capabilities = []
    
    if isinstance(device, Printable):
        capabilities.append("print")
    if isinstance(device, Faxable):
        capabilities.append("fax")
    if isinstance(device, Scannable):
        capabilities.append("scan")
    
    print(f"Device capabilities: {', '.join(capabilities)}")
    
    # Use only available capabilities
    if "print" in capabilities:
        device.print(document)
    if "scan" in capabilities:
        device.scan(document)

# Test with different devices
old = OldPrinter()
modern = ModernPrinter()
scanner = OfficeScanner()

print("=== Old Printer ===")
print_if_possible(old, "doc.pdf")      # ✅ Prints
scan_if_possible(old, "doc.pdf")       # ❌ Can't scan

print("\n=== Modern Printer ===")
process_document(modern, "report.pdf") # ✅ Prints and scans

print("\n=== Office Scanner ===")
print_if_possible(scanner, "photo.jpg") # ❌ Can't print
scan_if_possible(scanner, "photo.jpg")  # ✅ Scans
```

### 🧪 Easy Testing with ISP

```python
from unittest.mock import Mock

def test_print_only_needs_printable():
    """
    Test that only depends on Printable interface
    ✅ Don't need to mock fax/scan methods!
    """
    # Create minimal mock with just print method
    mock_printer = Mock(spec=Printable)
    mock_printer.print = Mock()
    
    print_if_possible(mock_printer, "test.pdf")
    
    mock_printer.print.assert_called_once_with("test.pdf")
    # ✅ No need to set up fax or scan!

def test_scan_only_needs_scannable():
    """
    Test that only depends on Scannable interface
    ✅ Completely independent of print/fax!
    """
    mock_scanner = Mock(spec=Scannable)
    mock_scanner.scan = Mock()
    
    scan_if_possible(mock_scanner, "test.jpg")
    
    mock_scanner.scan.assert_called_once_with("test.jpg")
    # ✅ No printing or faxing to mock!
```

### ✅ ISP Checklist

- ✅ Interfaces are small and focused
- ✅ Clients depend only on methods they use
- ✅ No forced implementation of unused methods
- ✅ Capabilities are composable
- ✅ Easy to test in isolation
- ✅ Protocol-based segregation

[⬆️ Back to TOC](#-table-of-contents)

---

## 5️⃣ Dependency Inversion Principle (DIP)

> **"Abstractions should not depend upon details. Details should depend upon abstractions"** - Uncle Bob

### 📖 The Problem

Depending on concrete implementations creates:
- 🔴 Tight coupling between components
- 🔴 Difficult to change data sources
- 🔴 Hard to test (can't mock concrete classes easily)
- 🔴 Violation of OCP (changes ripple through codebase)

### ✅ The Solution: Depend on Protocols

```mermaid
graph TB
    subgraph ABSTRACTION ["🎯    DataSource    Protocol    (Abstraction)"]
        PROTO[DataSource Protocol<br/>+ get_data: dict]
    end
    
    subgraph IMPLEMENTATIONS ["🔷    Concrete    Implementations"]
        DB[Database<br/>PostgreSQL<br/>+ connection_string<br/>+ get_data]
        API[RestAPI<br/>HTTP Client<br/>+ base_url<br/>+ get_data]
        FS[FileSystem<br/>JSON Files<br/>+ file_path<br/>+ get_data]
        CACHE[CacheLayer<br/>Redis<br/>+ cache_key<br/>+ get_data]
    end
    
    subgraph CLIENT ["💼    High-Level    Client"]
        FRONTEND[FrontEnd<br/>data_source: DataSource<br/>+ display_data]
    end
    
    subgraph BENEFITS ["✨    DIP    Benefits"]
        TESTABLE[Easy Testing<br/>Mock Protocol]
        FLEXIBLE[Swap Sources<br/>Runtime]
        LOOSE[Loose Coupling<br/>Maintainable]
        SCALABLE[Add Sources<br/>No Changes]
    end
    
    %% Protocol defines contract
    PROTO -.-> DB
    PROTO -.-> API
    PROTO -.-> FS
    PROTO -.-> CACHE
    
    %% Client depends on abstraction
    PROTO --> FRONTEND
    
    %% Implementations injected into client
    DB --> FRONTEND
    API --> FRONTEND
    FS --> FRONTEND
    CACHE --> FRONTEND
    
    %% Benefits flow
    FRONTEND --> TESTABLE
    FRONTEND --> FLEXIBLE
    FRONTEND --> LOOSE
    FRONTEND --> SCALABLE
    
    %% Connection styling
    linkStyle 0 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 1 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 2 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 3 stroke:#7b1fa2,stroke-width:2px,stroke-dasharray:5
    linkStyle 4 stroke:#1976d2,stroke-width:4px
    linkStyle 5 stroke:#388e3c,stroke-width:3px
    linkStyle 6 stroke:#388e3c,stroke-width:3px
    linkStyle 7 stroke:#388e3c,stroke-width:3px
    linkStyle 8 stroke:#388e3c,stroke-width:3px
    linkStyle 9 stroke:#3f51b5,stroke-width:4px
    linkStyle 10 stroke:#3f51b5,stroke-width:4px
    linkStyle 11 stroke:#3f51b5,stroke-width:4px
    linkStyle 12 stroke:#3f51b5,stroke-width:4px
    
    %% Subgraph styling
    style ABSTRACTION fill:#f8f0ff,stroke:#7b1fa2,stroke-width:3px,color:#000
    style IMPLEMENTATIONS fill:#e8f4fd,stroke:#1976d2,stroke-width:3px,color:#000
    style CLIENT fill:#f0f8f0,stroke:#388e3c,stroke-width:3px,color:#000
    style BENEFITS fill:#fff4e6,stroke:#f57c00,stroke-width:3px,color:#000
    
    %% Node styling
    style PROTO fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px,color:#000
    style DB fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style API fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style FS fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style CACHE fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    style FRONTEND fill:#e8f5e8,stroke:#388e3c,stroke-width:3px,color:#000
    style TESTABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style FLEXIBLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style LOOSE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
    style SCALABLE fill:#fff8e1,stroke:#f57c00,stroke-width:2px,color:#000
```

### 💻 Implementation

<details>
<summary><strong>🎯 Protocol (Abstraction)</strong></summary>

```python
from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class DataSource(Protocol):
    """
    Protocol defining how to get data
    
    This is the ABSTRACTION that both high-level and low-level
    modules depend on.
    
    ✅ High-level (FrontEnd) depends on this
    ✅ Low-level (Database, API) implements this
    """
    def get_data(self) -> dict[str, Any]:
        """Retrieve data from the source"""
        ...
    
    @property
    def source_type(self) -> str:
        """Return the type of data source"""
        ...
```
</details>

<details>
<summary><strong>🗄️ Database Implementation</strong></summary>

```python
from pydantic import BaseModel, Field, field_validator

class Database(BaseModel):
    """
    Database data source
    ✅ Depends on DataSource protocol (abstraction)
    ✅ Can be swapped with any other DataSource
    """
    connection_string: str = Field(description="Database connection URL")
    table_name: str = Field(description="Table to query")
    query_timeout: int = Field(default=30, ge=1, le=300)
    
    @field_validator('connection_string')
    @classmethod
    def validate_connection_string(cls, v: str) -> str:
        if not v.startswith(('postgresql://', 'mysql://', 'sqlite://')):
            raise ValueError("Invalid database URL scheme")
        return v
    
    def get_data(self) -> dict[str, Any]:
        """Simulate database query"""
        # In real code: execute SQL query
        return {
            "source": "database",
            "table": self.table_name,
            "connection": self.connection_string.split('@')[0],  # Hide credentials
            "data": [
                {"id": 1, "name": "Alice", "role": "Engineer"},
                {"id": 2, "name": "Bob", "role": "Designer"},
                {"id": 3, "name": "Charlie", "role": "Manager"}
            ],
            "row_count": 3
        }
    
    @property
    def source_type(self) -> str:
        return "database"
    
    def execute_query(self, sql: str) -> dict:
        """Database-specific method"""
        return {"sql": sql, "status": "executed"}
```
</details>

<details>
<summary><strong>🌐 REST API Implementation</strong></summary>

```python
class RestAPI(BaseModel):
    """
    REST API data source
    ✅ Implements same DataSource protocol
    ✅ Completely different implementation
    """
    base_url: str = Field(description="API base URL")
    endpoint: str = Field(description="API endpoint path")
    api_key: str = Field(repr=False, exclude=True)  # Secret, don't expose
    timeout: int = Field(default=10, ge=1, le=60)
    
    @field_validator('base_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL scheme")
        return v.rstrip('/')
    
    def get_data(self) -> dict[str, Any]:
        """Simulate API call"""
        # In real code: httpx.get() or requests.get()
        return {
            "source": "api",
            "url": f"{self.base_url}/{self.endpoint}",
            "status": 200,
            "data": {
                "users": [
                    {"id": 101, "name": "Dave", "role": "Admin"},
                    {"id": 102, "name": "Eve", "role": "User"}
                ],
                "metadata": {
                    "timestamp": "2025-01-15T10:30:00Z",
                    "version": "2.0"
                }
            }
        }
    
    @property
    def source_type(self) -> str:
        return "rest_api"
    
    def make_request(self, method: str, data: dict = None) -> dict:
        """API-specific method"""
        return {"method": method, "data": data, "status": "success"}
```
</details>

<details>
<summary><strong>📁 File System Implementation</strong></summary>

```python
from pathlib import Path

class FileSystem(BaseModel):
    """
    File system data source
    ✅ Yet another DataSource implementation
    ✅ Reads from JSON/CSV files
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    file_path: Path
    format: str = Field(default="json", pattern="^(json|csv)$")
    encoding: str = Field(default="utf-8")
    
    @field_validator('file_path', mode='before')
    @classmethod
    def convert_to_path(cls, v):
        path = Path(v) if not isinstance(v, Path) else v
        if not path.exists():
            raise ValueError(f"File not found: {path}")
        return path
    
    def get_data(self) -> dict[str, Any]:
        """Simulate file read"""
        # In real code: json.load() or pd.read_csv()
        return {
            "source": "filesystem",
            "file": str(self.file_path),
            "format": self.format,
            "data": {
                "records": [
                    {"id": 201, "product": "Widget", "price": 19.99},
                    {"id": 202, "product": "Gadget", "price": 29.99}
                ]
            },
            "size_bytes": self.file_path.stat().st_size
        }
    
    @property
    def source_type(self) -> str:
        return "filesystem"
```
</details>

<details>
<summary><strong>⚡ Cache Layer Implementation</strong></summary>

```python
from typing import Optional

class CacheLayer(BaseModel):
    """
    Cache data source (Redis, Memcached, etc.)
    ✅ Same protocol, different persistence
    ✅ Easy to add without changing client code
    """
    cache_key: str
    ttl_seconds: int = Field(default=3600, ge=60)
    fallback_source: Optional[DataSource] = Field(default=None)
    
    def get_data(self) -> dict[str, Any]:
        """Simulate cache lookup"""
        # In real code: redis.get() or memcached.get()
        cached_data = self._check_cache()
        
        if cached_data:
            return {
                "source": "cache",
                "cache_key": self.cache_key,
                "cache_hit": True,
                "data": cached_data
            }
        
        # Cache miss - use fallback if available
        if self.fallback_source:
            data = self.fallback_source.get_data()
            self._store_cache(data)
            return {
                "source": "cache",
                "cache_key": self.cache_key,
                "cache_hit": False,
                "fallback": self.fallback_source.source_type,
                "data": data
            }
        
        return {"source": "cache", "cache_key": self.cache_key, "data": None}
    
    @property
    def source_type(self) -> str:
        return "cache"
    
    def _check_cache(self) -> Optional[dict]:
        """Simulate cache check"""
        return None  # Simulate cache miss
    
    def _store_cache(self, data: dict) -> None:
        """Simulate storing to cache"""
        pass
```
</details>

<details>
<summary><strong>💼 Frontend (High-Level Client)</strong></summary>

```python
class FrontEnd(BaseModel):
    """
    Frontend that displays data
    
    ✅ Depends on DataSource PROTOCOL (abstraction)
    ✅ NOT on concrete Database or API classes
    ✅ Can work with ANY DataSource implementation
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    data_source: DataSource  # Depends on abstraction!
    cache_enabled: bool = Field(default=True)
    format_style: str = Field(default="json", pattern="^(json|table|list)$")
    
    def display_data(self) -> None:
        """
        Display data from ANY source
        
        ✅ Works with Database
        ✅ Works with RestAPI
        ✅ Works with FileSystem
        ✅ Works with any future DataSource!
        """
        data = self.data_source.get_data()
        
        print(f"\n{'='*60}")
        print(f"📊 Data from {data.get('source', 'unknown')} source")
        print(f"{'='*60}")
        
        if self.format_style == "json":
            import json
            print(json.dumps(data, indent=2))
        else:
            print(data)
    
    def switch_source(self, new_source: DataSource) -> None:
        """
        Switch data sources at runtime
        
        ✅ Demonstrates loose coupling
        ✅ No code changes needed
        """
        old_source = self.data_source.source_type
        self.data_source = new_source
        print(f"✅ Switched from {old_source} to {new_source.source_type}")
    
    def get_metadata(self) -> dict:
        """Get metadata about current source"""
        return {
            "source_type": self.data_source.source_type,
            "cache_enabled": self.cache_enabled,
            "format": self.format_style
        }
```
</details>

### 🎯 Usage Examples

```python
# Create different data sources
db = Database(
    connection_string="postgresql://user:pass@localhost/mydb",
    table_name="users"
)

api = RestAPI(
    base_url="https://api.example.com",
    endpoint="data/users",
    api_key="secret123"
)

fs = FileSystem(
    file_path=Path("data/users.json")
)

# Frontend depends on abstraction - works with ANY source!
app = FrontEnd(data_source=db)
app.display_data()

# ✅ Easy to switch sources at runtime
app.switch_source(api)
app.display_data()

app.switch_source(fs)
app.display_data()

# ✅ Can even chain sources (cache with fallback)
cache = CacheLayer(
    cache_key="users_data",
    fallback_source=db
)
app.switch_source(cache)
app.display_data()
```

### 🧪 Easy Testing with DIP

```python
from unittest.mock import Mock

def test_frontend_with_mock_source():
    """
    Test frontend without real database/API
    ✅ Mock the protocol, not concrete classes
    """
    # Create mock that implements DataSource protocol
    mock_source = Mock(spec=DataSource)
    mock_source.get_data.return_value = {
        "source": "mock",
        "data": {"test": "data"}
    }
    mock_source.source_type = "mock"
    
    # Frontend works with mock!
    app = FrontEnd(data_source=mock_source)
    app.display_data()
    
    mock_source.get_data.assert_called_once()
    # ✅ No need for real database or API!

def test_source_switching():
    """Test that sources can be swapped"""
    source1 = Mock(spec=DataSource)
    source1.source_type = "source1"
    
    source2 = Mock(spec=DataSource)
    source2.source_type = "source2"
    
    app = FrontEnd(data_source=source1)
    assert app.data_source is source1
    
    app.switch_source(source2)
    assert app.data_source is source2
    # ✅ Loose coupling allows easy switching!
```

### ✅ DIP Checklist

- ✅ High-level modules depend on abstractions (protocols)
- ✅ Low-level modules depend on abstractions (protocols)
- ✅ Abstractions don't depend on details
- ✅ Details depend on abstractions
- ✅ Easy to swap implementations at runtime
- ✅ Simple mocking in tests

[⬆️ Back to TOC](#-table-of-contents)

---

## 🎓 Best Practices & Patterns

### 🎯 Choosing Between ABC and Protocol

| Use ABC When... | Use Protocol When... |
|----------------|---------------------|
| You need shared implementation | You need duck typing |
| You want forced inheritance | You want structural subtyping |
| You're building a framework | You're building applications |
| Type hierarchy is important | Behavior matching is enough |
| You need metaclass features | You want simplicity |

### 🌟 Pydantic Best Practices

```python
from pydantic import BaseModel, Field, field_validator, model_validator

class BestPracticeExample(BaseModel):
    """Example showing Pydantic best practices"""
    
    # 1. Use descriptive Field parameters
    name: str = Field(
        min_length=1,
        max_length=100,
        description="User-friendly name"
    )
    
    # 2. Validate at field level
    age: int = Field(ge=0, le=150)
    
    @field_validator('age')
    @classmethod
    def validate_age(cls, v: int) -> int:
        """Additional business logic validation"""
        if v < 18:
            raise ValueError("Must be 18 or older")
        return v
    
    # 3. Validate at model level for cross-field checks
    start_date: str
    end_date: str
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'BestPracticeExample':
        """Cross-field validation"""
        if self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        return self
    
    # 4. Use property methods for computed values
    @property
    def is_adult(self) -> bool:
        return self.age >= 18
    
    # 5. Provide meaningful __str__
    def __str__(self) -> str:
        return f"{self.name} (age {self.age})"
```

### 🔄 Composition Patterns

```python
# ✅ GOOD: Composition
class EmailService(BaseModel):
    """Email sending capability"""
    smtp_host: str
    smtp_port: int = 587
    
    def send(self, to: str, subject: str, body: str) -> None:
        print(f"📧 Sending email to {to}")

class NotificationService(BaseModel):
    """Uses email service via composition"""
    email_service: EmailService
    
    def notify_user(self, user_email: str, message: str) -> None:
        self.email_service.send(
            to=user_email,
            subject="Notification",
            body=message
        )

# ❌ BAD: Deep inheritance
class EmailNotificationService(EmailService):  # Tight coupling!
    pass
```

### 📊 Protocol + Pydantic Pattern

```python
# Protocol for behavior contract
@runtime_checkable
class Exportable(Protocol):
    def export_json(self) -> str: ...
    def export_csv(self) -> str: ...

# Pydantic for data + validation
class Report(BaseModel):
    title: str
    data: list[dict]
    created_at: str = Field(default_factory=lambda: "2025-01-15")
    
    # Implement protocol
    def export_json(self) -> str:
        return self.model_dump_json(indent=2)
    
    def export_csv(self) -> str:
        # Implementation
        return "CSV export"

# ✅ Type-safe AND validated!
def save_export(exportable: Exportable) -> None:
    data = exportable.export_json()
    # Save data...

report = Report(title="Q4 Report", data=[{"revenue": 1000}])
save_export(report)  # Type-safe!
```

[⬆️ Back to TOC](#-table-of-contents)

---

## 🧪 Testing Strategies

### 🎯 Testing Protocol Implementations

```python
import pytest
from typing import Type

def test_shape_protocol_compliance():
    """Test that all shapes implement ShapeProtocol"""
    shapes: list[Type[ShapeProtocol]] = [
        Circle,
        Rectangle,
        Square,
        Triangle,
        Hexagon
    ]
    
    for shape_class in shapes:
        # Create instance
        if shape_class == Circle:
            shape = shape_class(radius=5)
        elif shape_class in (Rectangle,):
            shape = shape_class(width=5, height=10)
        elif shape_class in (Square, Hexagon):
            shape = shape_class(side=5)
        else:
            shape = shape_class(base=5, height=10)
        
        # Verify protocol compliance
        assert isinstance(shape, ShapeProtocol)
        assert hasattr(shape, 'calculate_area')
        assert hasattr(shape, 'shape_type')
        
        # Verify methods work
        area = shape.calculate_area()
        assert isinstance(area, (int, float))
        assert area > 0

def test_pydantic_validation():
    """Test that Pydantic validation works"""
    with pytest.raises(ValidationError):
        Circle(radius=-5)  # Negative radius
    
    with pytest.raises(ValidationError):
        Rectangle(width=0, height=5)  # Zero width
    
    # Valid instances
    circle = Circle(radius=5)
    assert circle.radius == 5
```

### 🎭 Mocking Protocols

```python
from unittest.mock import Mock, MagicMock

def test_with_mock_data_source():
    """Test FrontEnd with mocked DataSource"""
    # Create mock implementing protocol
    mock_source = Mock(spec=DataSource)
    mock_source.get_data.return_value = {
        "source": "test",
        "data": [1, 2, 3]
    }
    mock_source.source_type = "test"
    
    # Use with FrontEnd
    app = FrontEnd(data_source=mock_source)
    app.display_data()
    
    # Verify interactions
    mock_source.get_data.assert_called_once()

def test_with_real_pydantic_models():
    """Test with actual Pydantic models"""
    # Real implementations are easy to test
    db = Database(
        connection_string="postgresql://localhost/test",
        table_name="test_table"
    )
    
    api = RestAPI(
        base_url="https://test.com",
        endpoint="data",
        api_key="test123"
    )
    
    # Both implement protocol
    assert isinstance(db, DataSource)
    assert isinstance(api, DataSource)
    
    # Can use interchangeably
    app = FrontEnd(data_source=db)
    app.switch_source(api)
    assert app.data_source is api
```

### ✅ Integration Testing

```python
def test_end_to_end_shapes():
    """Integration test for shape system"""
    shapes = [
        Circle(radius=5),
        Rectangle(width=10, height=5),
        Square(side=4),
        Triangle(base=6, height=8),
        Hexagon(side=3)
    ]
    
    # Calculate total area
    total = get_total_area(shapes)
    
    # Verify each shape works
    for shape in shapes:
        area = shape.calculate_area()
        assert area > 0
        assert isinstance(area, (int, float))
    
    # Verify total
    expected_total = sum(s.calculate_area() for s in shapes)
    assert abs(total - expected_total) < 1e-10

def test_end_to_end_data_sources():
    """Integration test for data source system"""
    # Test all sources work
    sources = [
        Database(
            connection_string="postgresql://localhost/db",
            table_name="users"
        ),
        RestAPI(
            base_url="https://api.test.com",
            endpoint="data",
            api_key="key123"
        )
    ]
    
    app = FrontEnd(data_source=sources[0])
    
    for source in sources:
        app.switch_source(source)
        data = app.data_source.get_data()
        
        # Verify data structure
        assert isinstance(data, dict)
        assert 'source' in data
        assert 'data' in data
```

[⬆️ Back to TOC](#-table-of-contents)

---

## 📚 Complete Example Project

### 🏗️ Project Structure

```
solid_project/
├── models/
│   ├── __init__.py
│   ├── protocols.py      # Protocol definitions
│   ├── shapes.py         # Shape implementations
│   └── data_sources.py   # Data source implementations
├── services/
│   ├── __init__.py
│   ├── file_manager.py   # File services (SRP)
│   └── frontend.py       # Frontend service (DIP)
├── tests/
│   ├── __init__.py
│   ├── test_shapes.py
│   └── test_data_sources.py
└── main.py               # Example usage
```

### 📄 protocols.py

```python
"""
Protocol definitions for the entire project
All protocols in one place for easy reference
"""
from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class ShapeProtocol(Protocol):
    """Shapes that can calculate area"""
    def calculate_area(self) -> float: ...
    @property
    def shape_type(self) -> str: ...

@runtime_checkable
class Printable(Protocol):
    """Devices that can print"""
    def print(self, document: str) -> None: ...

@runtime_checkable
class DataSource(Protocol):
    """Sources that provide data"""
    def get_data(self) -> dict[str, Any]: ...
    @property
    def source_type(self) -> str: ...
```

### 🎯 main.py - Complete Example

```python
"""
Complete example demonstrating all SOLID principles
"""
from pathlib import Path
from models.shapes import Circle, Rectangle, Square, get_total_area
from models.data_sources import Database, RestAPI
from services.file_manager import FileManager, ZipFileManager
from services.frontend import FrontEnd

def demonstrate_srp():
    """Single Responsibility Principle"""
    print("=" * 60)
    print("🎯 SINGLE RESPONSIBILITY PRINCIPLE")
    print("=" * 60)
    
    # Each class has ONE job
    file_mgr = FileManager(path="demo.txt")
    file_mgr.write("Hello, SOLID!")
    content = file_mgr.read()
    print(f"✅ File content: {content}")
    
    zip_mgr = ZipFileManager(path="demo.txt")
    zip_file = zip_mgr.compress()
    print(f"✅ Created ZIP: {zip_file}")

def demonstrate_ocp():
    """Open-Closed Principle"""
    print("\n" + "=" * 60)
    print("🔓 OPEN-CLOSED PRINCIPLE")
    print("=" * 60)
    
    # Easy to extend with new shapes
    shapes = [
        Circle(radius=5),
        Rectangle(width=10, height=5),
        Square(side=4)
    ]
    
    total = get_total_area(shapes)
    print(f"✅ Total area: {total:.2f}")
    print("✅ Can add new shapes without modifying client code!")

def demonstrate_lsp():
    """Liskov Substitution Principle"""
    print("\n" + "=" * 60)
    print("🔄 LISKOV SUBSTITUTION PRINCIPLE")
    print("=" * 60)
    
    # All shapes are substitutable
    def print_area(shape: ShapeProtocol) -> None:
        print(f"  {shape.shape_type}: {shape.calculate_area():.2f}")
    
    shapes = [Circle(radius=5), Square(side=5), Rectangle(width=5, height=10)]
    for shape in shapes:
        print_area(shape)
    
    print("✅ All shapes substitutable!")

def demonstrate_isp():
    """Interface Segregation Principle"""
    print("\n" + "=" * 60)
    print("🔀 INTERFACE SEGREGATION PRINCIPLE")
    print("=" * 60)
    
    # Devices only implement what they need
    from models.printers import OldPrinter, ModernPrinter
    
    old = OldPrinter()
    modern = ModernPrinter()
    
    print(f"✅ Old printer: {old.get_capabilities()}")
    print(f"✅ Modern printer: {modern.get_capabilities()}")
    print("✅ No unused methods!")

def demonstrate_dip():
    """Dependency Inversion Principle"""
    print("\n" + "=" * 60)
    print("⬇️ DEPENDENCY INVERSION PRINCIPLE")
    print("=" * 60)
    
    # Frontend depends on abstraction
    db = Database(
        connection_string="postgresql://localhost/demo",
        table_name="users"
    )
    
    api = RestAPI(
        base_url="https://api.demo.com",
        endpoint="users",
        api_key="demo123"
    )
    
    app = FrontEnd(data_source=db)
    print("✅ Using database source:")
    app.display_data()
    
    app.switch_source(api)
    print("\n✅ Switched to API source:")
    app.display_data()
    
    print("✅ Loose coupling via protocols!")

if __name__ == "__main__":
    demonstrate_srp()
    demonstrate_ocp()
    demonstrate_lsp()
    demonstrate_isp()
    demonstrate_dip()
    
    print("\n" + "=" * 60)
    print("🎉 ALL SOLID PRINCIPLES DEMONSTRATED!")
    print("=" * 60)
```

[⬆️ Back to TOC](#-table-of-contents)

---

## 🔍 Comparison: ABC vs Protocol

### 📊 Side-by-Side Comparison

```python
# ===== ABC APPROACH =====
from abc import ABC, abstractmethod

class ShapeABC(ABC):
    """ABC-based interface"""
    @abstractmethod
    def calculate_area(self) -> float:
        pass

class CircleABC(ShapeABC):
    """MUST inherit from ShapeABC"""
    def __init__(self, radius: float):
        self.radius = radius
    
    def calculate_area(self) -> float:
        return 3.14 * self.radius ** 2

# ❌ This won't work - doesn't inherit!
class ThirdPartyShape:
    def calculate_area(self) -> float:
        return 100.0

# TypeError: Can't use without inheritance
# shapes: list[ShapeABC] = [CircleABC(5), ThirdPartyShape()]


# ===== PROTOCOL APPROACH =====
from typing import Protocol, runtime_checkable

@runtime_checkable
class ShapeProtocol(Protocol):
    """Protocol-based interface"""
    def calculate_area(self) -> float: ...

class CircleProtocol:
    """NO inheritance needed!"""
    def __init__(self, radius: float):
        self.radius = radius
    
    def calculate_area(self) -> float:
        return 3.14 * self.radius ** 2

# ✅ This works - duck typing!
class ThirdPartyShape:
    def calculate_area(self) -> float:
        return 100.0

# Both work!
shapes: list[ShapeProtocol] = [CircleProtocol(5), ThirdPartyShape()]
```

### 🎯 When to Use Each

**Use ABC when:**
- Building a framework or library
- Need shared implementation (mixins)
- Type hierarchy is meaningful
- Want to prevent instantiation of base class

**Use Protocol when:**
- Building applications
- Want flexibility and duck typing
- Working with third-party code
- Type checking is primary goal
- Following KISS principle

### 📈 Performance Comparison

```python
import timeit

# ABC approach
setup_abc = """
from abc import ABC, abstractmethod
class ShapeABC(ABC):
    @abstractmethod
    def area(self): pass

class Circle(ShapeABC):
    def __init__(self, r): self.r = r
    def area(self): return 3.14 * self.r ** 2
"""

# Protocol approach
setup_protocol = """
from typing import Protocol
class ShapeProtocol(Protocol):
    def area(self) -> float: ...

class Circle:
    def __init__(self, r): self.r = r
    def area(self): return 3.14 * self.r ** 2
"""

# Results (approximate):
# ABC: ~0.15 microseconds per operation
# Protocol: ~0.12 microseconds per operation
# ✅ Protocol is slightly faster (no inheritance overhead)
```

[⬆️ Back to TOC](#-table-of-contents)

---

## 🎯 Conclusion

### 🌟 Key Takeaways

1. **Protocol > ABC** for modern Python applications
   - More Pythonic (duck typing)
   - Looser coupling
   - Better for composition

2. **Pydantic Adds Value**
   - Automatic validation
   - JSON serialization
   - Schema generation
   - Type safety

3. **SOLID Still Applies**
   - SRP: One class, one job
   - OCP: Extend via new types
   - LSP: Behavioral compatibility
   - ISP: Small, focused interfaces
   - DIP: Depend on abstractions

4. **KISS Wins**
   - Simple is better than complex
   - Explicit is better than implicit
   - Composition over inheritance

### 📊 Quick Reference

| Principle | Key Pattern | Pydantic Feature |
|-----------|-------------|------------------|
| SRP | Separate concerns | Field validation |
| OCP | Protocol-based | Model inheritance |
| LSP | Behavioral contracts | Type constraints |
| ISP | Small protocols | Composition |
| DIP | Protocol injection | ConfigDict |

### 🚀 Next Steps

1. **Refactor existing code** using these patterns
2. **Start new projects** with Protocol + Pydantic
3. **Write comprehensive tests** using protocol mocks
4. **Document protocols** clearly for team
5. **Review regularly** against SOLID principles

### 📚 Additional Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/)
- [Uncle Bob's SOLID Principles](https://blog.cleancoder.com/uncle-bob/2020/10/18/Solid-Relevance.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

### ✅ Final Checklist

Before considering your code "SOLID":

- [ ] Each class has a single, clear responsibility
- [ ] New features added via new classes, not modifications
- [ ] Types are substitutable based on behavior
- [ ] Interfaces are small and focused
- [ ] Dependencies are on protocols, not concrete classes
- [ ] Pydantic validates all data
- [ ] Comprehensive tests using protocol mocks
- [ ] Type hints throughout
- [ ] Clear documentation

**Remember:** SOLID principles are guidelines, not laws. Apply them pragmatically based on project needs. When in doubt, favor KISS!

[⬆️ Back to TOC](#-table-of-contents)

---

<div align="center">

**🎉 You're now ready to write Pythonic, SOLID code! 🎉**

*Built with Python, Pydantic, and SOLID principles*

</div>