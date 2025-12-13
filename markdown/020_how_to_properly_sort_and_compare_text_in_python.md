# How to Properly Sort and Compare Text in Python
#### Beyond ASCII: A Guide to Collation, Locales, and the Right Way to Sort Strings

**By Tihomir Manushev**  
*Nov 4, 2025 · 6 min read*

---

As developers, we live by a simple, comforting logic: A comes before B, 1 comes before 2. We trust our tools to get this right. So, let’s try a quick experiment. Imagine you’re building a new HR application and you need to sort a list of your new European team members.

```python
team_members = ['Zoë', 'aaron', 'Åsa', 'Zola', 'Ángel']

print("Default sorting:")
print(sorted(team_members))
```

You run it, and this is what you get:

```text
Default sorting:
['Ángel', 'Åsa', 'Zola', 'Zoë', 'aaron']
```

Wait, what? Zola comes before aaron? And where did those accented names end up? This isn’t just a minor quirk; this is fundamentally wrong for any human looking at the list. Your application, which was supposed to be simple and logical, has just failed its first and most basic test of user-friendliness.

Welcome to the subtle, often maddening world of Unicode sorting. The bad news is that Python’s default behavior is almost never what you want for human-readable text. The good news is that understanding why it fails is the key to fixing it correctly and building robust, global-ready applications.

---

### The Problem: Computers Sort Numbers, Not Letters

The core of the misunderstanding lies in a simple fact: computers don’t see characters. They see numbers. Every character on your screen — ‘A’, ‘Á’, ‘Å’, ‘α’, ‘😊’ — is represented by a unique number called a code point in the Unicode standard.

When you call `sorted()`, Python performs a simple, logical operation: it compares the code points of each character in each string, one by one.

Let’s look at the code points for the first letter of our names:

*   Á -> U+00C1 (Decimal 193)
*   Å -> U+00C5 (Decimal 197)
*   Z -> U+005A (Decimal 90)
*   a -> U+0061 (Decimal 97)

The default sort order is now obvious: Z (90) comes before a (97), and both come after Å (197). Python isn’t wrong; it’s just being ruthlessly literal. It’s sorting by numerical value, not by linguistic meaning.

Humans, on the other hand, use a set of complex rules called collation. Collation is the algorithm that defines the correct sorting order of strings in a specific language. For example, in many European languages:

*   Case is ignored (‘a’ is sorted with ‘A’).
*   Accents are secondary; ‘á’ should be sorted with ‘a’. If two words are identical except for an accent, the plain one usually comes first.
*   Some languages have unique rules. In Swedish, ‘Å’ is a distinct letter that comes after ‘Z’. In German, ‘ä’ is sorted as if it were ‘ae’.

To sort text correctly, we need to tell Python to stop sorting by raw code points and start using a proper collation algorithm.

---

### The Built-in Way: The locale Module

Python’s standard library offers a tool for this: the `locale` module. It allows you to tap into the host operating system’s language and formatting settings. The idea is simple: you set a global locale for your program, and then use the `locale.strxfrm` function as a key for sorting. This function transforms a string into a different representation that, when sorted byte-by-byte, produces a culturally correct order.

Let’s try to fix our list using a German locale, where ‘ä’ and ‘a’ are treated similarly.

```python
import locale

team_members = ['Zoë', 'aaron', 'Åsa', 'Zola', 'Ángel']

# Set the locale to German (assuming it's installed on the OS)
try:
    locale.setlocale(locale.LC_COLLATE, 'de_DE.UTF-8')
    print("Sorting with German locale:")
    
    # Use locale.strxfrm as the sort key
    sorted_members = sorted(team_members, key=locale.strxfrm)
    print(sorted_members)

except locale.Error:
    print("The locale 'de_DE.UTF-8' is not supported on this system.")
```

If the `de_DE.UTF-8` locale is installed on your system, you’ll get a much more sensible result:

```text
Sorting with German locale:
['aaron', 'Ángel', 'Åsa', 'Zola', 'Zoë']
```

This is a huge improvement! Case is handled correctly (‘aaron’ is first), and the accented names are in reasonable positions.

So, problem solved? Not quite. The `locale` module is a powerful tool, but it’s riddled with pitfalls for application developers:

1.  **It’s Global:** `locale.setlocale()` changes a setting for your entire program. This is a massive problem in libraries, web servers, or any multi-threaded application. One part of your code could change the locale and unknowingly break the sorting logic somewhere else entirely.
2.  **It’s Platform-Dependent:** The string `de_DE.UTF-8` only works on systems (like Linux) that use that naming convention. On Windows, you might need `German_Germany.1252`. Worse, the locale has to be pre-installed on the machine running the code. This makes your application’s deployment fragile and unpredictable.
3.  **It Can Be Unreliable:** Implementations can vary between operating systems, leading to inconsistent results.

For a simple script running on your own machine, `locale` might be fine. For building distributable applications, it’s a liability. We need a solution that is self-contained, predictable, and doesn’t rely on global state.

---

### A Modern Solution: The Unicode Collation Algorithm

The Unicode Consortium publishes the Unicode Collation Algorithm (UCA), a standard set of rules for sorting Unicode text that serves as a solid, language-agnostic baseline. Fortunately, you don’t need to implement it yourself. The excellent, pure-Python library **PyUCA** does it for you.

Because PyUCA is a self-contained Python package, it has no external dependencies and works identically on Windows, macOS, and Linux.

First, install it:

```bash
pip install pyuca
```

Now, let’s rewrite our sorting example. The process is clean and simple: you instantiate a Collator object and use its `sort_key` method.

```python
import pyuca

team_members = ['Zoë', 'aaron', 'Åsa', 'Zola', 'Ángel']

# Create a collator instance from PyUCA
collator = pyuca.Collator()

print("Sorting with PyUCA:")
sorted_members = sorted(team_members, key=collator.sort_key)
print(sorted_members)
```

The output is exactly what we wanted, with no fuss:

```text
Sorting with PyUCA:
['aaron', 'Ángel', 'Åsa', 'Zola', 'Zoë']
```

This code is clean, predictable, and portable. It doesn’t modify any global settings and doesn’t care what operating system it’s running on. For the vast majority of applications, PyUCA is the right starting point for Unicode sorting.

---

### For Maximum Power: PyICU and Locale-Specific Rules

PyUCA uses the default UCA table, which provides excellent general-purpose sorting. But what if you need to respect the specific rules of a particular language? Remember how Swedish sorts ‘Å’ after ‘Z’? The default UCA won’t do that.

For this level of control, you need the powerhouse of internationalization libraries: **PyICU**. This is a Python wrapper for the industry-standard C++ ICU (International Components for Unicode) libraries used by Google, Apple, and countless others.

PyICU is a binary dependency, so it can be more complex to install than PyUCA, but it gives you unparalleled control. With PyICU, you can request a collator for a specific locale without touching the program’s global state.

Let’s see how to sort our list according to Swedish rules:

```bash
pip install PyICU
```

```python
from icu import Collator, Locale

team_members = ['Zoë', 'aaron', 'Åsa', 'Zola', 'Ángel']

# Create a collator specifically for the Swedish locale
swedish_collator = Collator.createInstance(Locale('sv_SE'))

print("Sorting with PyICU (Swedish rules):")
sorted_members = sorted(team_members, key=swedish_collator.getSortKey)
print(sorted_members)
```

Now, the output reflects the specific rules of the Swedish language:

```text
Sorting with PyICU (Swedish rules):
['aaron', 'Ángel', 'Zola', 'Zoë', 'Åsa']
```

Look at that! Åsa is now correctly placed at the end of the list, just as a Swedish user would expect. This is the ultimate in collation correctness, and it’s essential for applications that need to present data to users in their native language conventions.

---

### Conclusion: Your Sorting Strategy

Sorting text in a global world is more than a one-line function call. It requires intention and an understanding of the tools at your disposal. Here’s a simple guide to making the right choice:

*   **For quick-and-dirty scripts on your own machine:** The `locale` module can work, but know its limits.
*   **For most applications (web apps, data processing, APIs):** Start with **PyUCA**. It is robust, simple, platform-independent, and provides sensible sorting for a wide range of languages.
*   **For applications requiring strict linguistic correctness for specific locales:** Use **PyICU**. It’s the most powerful and correct solution, but comes with the overhead of a binary dependency.

By moving beyond Python’s default behavior, you’re not just fixing a bug; you’re showing respect for your users and their languages. You’re building software that is truly, and correctly, global.