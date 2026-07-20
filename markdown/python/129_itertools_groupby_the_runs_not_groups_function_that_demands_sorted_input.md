# itertools.groupby: The Runs-Not-Groups Function That Demands Sorted Input

#### Why Python's groupby fragments your data into pieces when SQL's GROUP BY would have collected it — and the lazy trap that empties your groups

**By Tihomir Manushev**

*Jul 17, 2026 · 7 min read*

---

Someone reads the name `itertools.groupby`, remembers SQL's `GROUP BY`, and writes the obvious code: group these delivery records by zone, sum the packages in each. The result looks almost right — every zone is there — but the totals are wrong, and the same zone shows up three separate times. No exception, no warning. Just quietly incorrect numbers in a report nobody double-checks until a customer does.

The trap is a single word in the mental model. SQL's `GROUP BY` collects *all* rows with the same key, wherever they sit in the table. Python's `groupby` collects *consecutive* rows with the same key — it breaks the input into **runs**, not groups. Feed it data where equal keys aren't already adjacent, and it hands back a fragment every time the key changes, not one group per distinct value.

This article shows exactly where that goes wrong, the one-line fix, the cases where consecutive-grouping is the whole point, and a second, nastier trap: the group objects `groupby` yields are lazy views that empty themselves the moment you look away.

---

### Runs, Not Groups

Here is the code that looks correct and isn't. Delivery records, grouped by zone, collected into lists:

```python
from itertools import groupby
from operator import itemgetter

deliveries = [
    ("north", 3), ("south", 5), ("north", 2),
    ("east", 4), ("south", 1), ("north", 6),
]

for zone, group in groupby(deliveries, key=itemgetter(0)):
    packages = [count for _, count in group]
    print(f"{zone}: {packages}")
```

The `key=itemgetter(0)` tells `groupby` to compare records by their first element, the zone. You expect three lines — one per zone. You get six:

```
north: [3]
south: [5]
north: [2]
east: [4]
south: [1]
north: [6]
```

`groupby` walked the list in order and started a fresh group every time the key differed from the previous element. Because `north` never appears twice in a row, it produced three separate `north` runs. Aggregate these and you'd double- and triple-count zones, silently. The function did precisely what it promises — it just doesn't promise what `GROUP BY` promises.

---

### The Sort-Then-Group Fix

`groupby` only sees adjacency, so the fix is to make equal keys adjacent first. Sort by the same key you group on:

```python
ordered = sorted(deliveries, key=itemgetter(0))

for zone, group in groupby(ordered, key=itemgetter(0)):
    total = sum(count for _, count in group)
    print(f"{zone}: total={total}")
```

Now every zone's records sit together, so each becomes exactly one run:

```
east: total=4
north: total=11
south: total=6
```

The rule that keeps you out of trouble: **the sort key and the group key must be the same function**. Sort by zone and group by zone. If you sort by one attribute and group by another, you're back to fragmentation with no error to warn you. This is also the honest cost of the approach — sorting is **O(n log n)**, whereas a true one-pass grouping is **O(n)**. For already-sorted data (rows straight out of an `ORDER BY` query, timestamps from a log) you skip the sort entirely and `groupby` runs in a single linear pass. That is the scenario it was built for.

---

### When Consecutive Is the Point

It would be a mistake to conclude `groupby` is just a clumsy `GROUP BY` that needs a sort bolted on. Its consecutive semantics are a genuine feature — the right and only tool when position *is* the meaning. Detecting streaks, collapsing repeats, run-length encoding: all of these depend on grouping adjacent equal items and would be destroyed by sorting.

```python
from itertools import groupby

status_stream = "AAAABBBCCDAAA"
runs = [(state, len(list(run))) for state, run in groupby(status_stream)]
print(runs)
# [('A', 4), ('B', 3), ('C', 2), ('D', 1), ('A', 3)]
```

Called with no `key`, `groupby` groups by the element itself. The output captures that the stream held four `A`s, then three `B`s, and — crucially — a *separate* final run of three `A`s. That trailing `('A', 3)` is exactly what you want when encoding a time-ordered signal: the two `A` stretches are different events, separated in time. Sorting this input would fuse them into a meaningless `('A', 7)` and throw away the structure you were trying to measure. When your data is a sequence and the runs carry meaning, `groupby` is the function; a `GROUP BY`-style collector is the bug.

---

### The Gotcha That Breaks Everyone's First groupby

Now the trap that survives even after you've learned to sort. It feels natural to collect the `(key, group)` pairs first and process them later:

```python
ordered = sorted(deliveries, key=itemgetter(0))
saved = [(zone, group) for zone, group in groupby(ordered, key=itemgetter(0))]

for zone, group in saved:
    print(f"{zone}: {list(group)}")
```

Every group comes back empty:

```
east: []
north: []
south: []
```

The groups aren't lists — they're lazy sub-iterators that share **one underlying cursor** with the outer `groupby` iterator. When the list comprehension advanced to find the next `(key, group)` pair, it dragged that shared cursor past the previous group's elements, consuming them. By the time you loop over `saved`, every group's items have already been walked. Nothing is left.

You can watch a single step do it. Advancing the outer iterator by one guts the group you were just handed:

```python
grouper = groupby(ordered, key=itemgetter(0))
first_key, first_group = next(grouper)
second_key, second_group = next(grouper)   # this advance consumes first_group
print(f"{first_key} after advancing to {second_key}:", list(first_group))
# east after advancing to north: []
```

The fix is a discipline, not a workaround: **materialize each group before advancing to the next**. Turn the sub-iterator into a real list inside the loop body, and it survives:

```python
sales = sorted([("q2", 40), ("q1", 10), ("q2", 25), ("q1", 30)], key=itemgetter(0))
grouped = {quarter: [amt for _, amt in group]
           for quarter, group in groupby(sales, key=itemgetter(0))}
print(grouped)
# {'q1': [10, 30], 'q2': [40, 25]}
```

The dict comprehension consumes each `group` into a list *before* the next iteration pulls the shared cursor forward. This is why `[list(g) for _, g in groupby(...)]` works but saving the raw groupers doesn't: the difference is whether you drink from the sub-iterator now or intend to come back for it later. With `groupby`, there is no coming back.

---

### The Key Can Be Any Function

Nothing restricts the key to a column lookup. It is an ordinary function, so you can group by anything you can compute from an element — a length, a bucket, a sign, a truncated timestamp. Group short status codes into runs by their length, and the same sort-then-group discipline applies to the derived key:

```python
codes = ["ok", "io", "db", "fail", "warn", "retry"]
ordered = sorted(codes, key=len)
by_length = {n: list(group) for n, group in groupby(ordered, key=len)}
print(by_length)
# {2: ['ok', 'io', 'db'], 4: ['fail', 'warn'], 5: ['retry']}
```

The sort arranges elements so equal *derived* keys sit together, then `groupby` runs them into buckets. One efficiency detail worth knowing: `groupby` calls the key function exactly once per element and caches the result, so an expensive key — a regex, a parse, a database of lookups — isn't recomputed as it compares neighbors. That makes a computed key cheap to use even on large streams, provided the input is already ordered by that same key.

---

### When to Reach for defaultdict Instead

If you find yourself sorting solely to satisfy `groupby`, ask whether you wanted runs at all. When you genuinely want SQL-style grouping — every record with a given key collected regardless of position — a `defaultdict` does it in one linear pass with no sort and no adjacency requirement:

```python
from collections import defaultdict

buckets: dict[str, list[int]] = defaultdict(list)
for quarter, amount in [("q2", 40), ("q1", 10), ("q2", 25), ("q1", 30)]:
    buckets[quarter].append(amount)
print(dict(buckets))
# {'q2': [40, 25], 'q1': [10, 30]}
```

No sorting, no fragmentation risk, no lazy-view trap, and **O(n)** instead of **O(n log n)**. The trade-off is that a `defaultdict` builds the whole mapping in memory, so it needs the full dataset at once; `groupby` streams, touching one group at a time, which matters when the input is enormous or infinite. Choose by intent: reach for `groupby` when your data is ordered and the runs mean something — or when it's already sorted and you want to stream. Reach for `defaultdict` when you want true grouping over unordered data and the result fits in memory.

---

### Conclusion

`itertools.groupby` is not a broken `GROUP BY`; it is a precise tool with a different job. It splits an ordered sequence into consecutive runs, which makes it perfect for streaks, run-length encoding, and already-sorted streams — and wrong for collecting scattered keys unless you sort on the same key first. Match the sort key to the group key, and match the tool to the intent — sort-then-`groupby` when you want runs or streaming, a `defaultdict` when you want scattered keys collected in one pass.

Keep the lazy trap in mind above all: the group objects share a cursor with the parent iterator and evaporate the instant you advance past them. Consume each group into a real container inside the loop, never save the raw groupers for later, and the runs-not-groups model stops producing mysterious empty lists and silently wrong totals.
