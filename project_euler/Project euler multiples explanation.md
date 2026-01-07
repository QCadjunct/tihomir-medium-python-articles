# Project Euler:Project Euler multiples explanation

## Problem Statement

Find the sum of all multiples of 3 or 5 below N+.

**Example:**
- For N = 10: multiples are 3, 5, 6, 9 → sum = 23
- For N = 100: sum = 2318

## Mathematical Solution (O(1) Complexity)

Instead of iterating through all numbers, we use the **arithmetic series formula** and the **inclusion-exclusion principle**.

### Arithmetic Series Formula

The sum of first k natural numbers is:
```
1 + 2 + 3 + ... + k = k × (k + 1) / 2
```

### Sum of Multiples of a Number

To find the sum of all multiples of `m` below `N`:

1. **Count of multiples**: `k = (N - 1) // m`
   - We use `N - 1` because we want numbers *below* N (not including N)

2. **Multiples are**: m, 2m, 3m, ..., km = m × (1 + 2 + 3 + ... + k)

3. **Sum formula**: 
   ```
   Sum = m × k × (k + 1) / 2
   ```

### Example: Multiples of 3 below 10

- k₃ = (10 - 1) // 3 = 9 // 3 = 3
- Multiples: 3, 6, 9 (which is 3×1, 3×2, 3×3)
- Sum = 3 × 3 × 4 / 2 = 3 × 6 = 18

### Example: Multiples of 5 below 10

- k₅ = (10 - 1) // 5 = 9 // 5 = 1
- Multiples: 5 (which is 5×1)
- Sum = 5 × 1 × 2 / 2 = 5

### Inclusion-Exclusion Principle

**Problem**: If we simply add multiples of 3 and multiples of 5, we count numbers divisible by **both** 3 and 5 twice.

Numbers divisible by both 3 and 5 are multiples of **LCM(3, 5) = 15**.

**Solution**:
```
Sum = (Sum of multiples of 3) + (Sum of multiples of 5) - (Sum of multiples of 15)
```

### Complete Example: N = 10

1. **Multiples of 3**: k₃ = 3, Sum₃ = 3 × 3 × 4 / 2 = 18
2. **Multiples of 5**: k₅ = 1, Sum₅ = 5 × 1 × 2 / 2 = 5
3. **Multiples of 15**: k₁₅ = 0, Sum₁₅ = 0
4. **Final Sum**: 18 + 5 - 0 = **23** ✓

### Complete Example: N = 100

1. **Multiples of 3**: k₃ = 33, Sum₃ = 3 × 33 × 34 / 2 = 1683
2. **Multiples of 5**: k₅ = 19, Sum₅ = 5 × 19 × 20 / 2 = 950
3. **Multiples of 15**: k₁₅ = 6, Sum₁₅ = 15 × 6 × 7 / 2 = 315
4. **Final Sum**: 1683 + 950 - 315 = **2318** ✓

## Optimization Strategy

Given T test cases (potentially with duplicate N values):

1. **Extract unique N values** from all test cases
2. **Sort unique values** (optional, for incremental caching if needed)
3. **Calculate sum for each unique N** using O(1) formula
4. **Map results** back to original test case order
5. **Parallel processing**: Use multiprocessing for large T values

### Why This Works

- **Time Complexity**: O(1) per unique N value (no iteration needed)
- **Space Complexity**: O(U) where U = number of unique N values
- **Handles duplicates**: Calculate once, reuse result
- **Scalable**: Works for N up to 10⁹ instantly

## Algorithm Pseudocode

```python
def sum_multiples_below(N, m):
    """Calculate sum of multiples of m below N"""
    k = (N - 1) // m
    return m * k * (k + 1) // 2

def solve(N):
    """Calculate sum of multiples of 3 or 5 below N"""
    sum_3 = sum_multiples_below(N, 3)
    sum_5 = sum_multiples_below(N, 5)
    sum_15 = sum_multiples_below(N, 15)
    return sum_3 + sum_5 - sum_15

# For multiple test cases:
# 1. Collect all N values
# 2. Find unique N values
# 3. Calculate solve(N) for each unique N
# 4. Map results back to original order
```

## Verification

Let's verify with the examples:

**N = 10:**
- Actual multiples: 3, 5, 6, 9
- Expected sum: 23
- Calculated: 18 + 5 - 0 = 23 ✓

**N = 100:**
- Expected sum: 2318
- Calculated: 1683 + 950 - 315 = 2318 ✓

## Key Insights

1. **No iteration required** - Pure mathematics
2. **Constant time** per calculation regardless of N size
3. **Inclusion-exclusion** prevents double-counting
4. **Cache-friendly** for duplicate queries
5. **Parallelizable** across independent test cases