#!/usr/bin/env python3
"""
Project Euler: Sum of Multiples of 3 or 5 Below N

O(1) solution using arithmetic series formula and inclusion-exclusion principle.
No iteration, no parallelization needed - pure mathematics.

Author: Peter Heller
Date: 2026-01-04
Python: 3.14
"""

import sys
from typing import List, Dict


def sum_multiples_below(n: int, m: int) -> int:
    """
    Calculate sum of all multiples of m below n using arithmetic series formula.
    
    Formula: m × k × (k + 1) / 2, where k = (n - 1) // m
    
    Time Complexity: O(1)
    
    Args:
        n: Upper bound (exclusive)
        m: Multiple to sum (e.g., 3 or 5)
        
    Returns:
        Sum of all multiples of m below n
        
    Example:
        >>> sum_multiples_below(10, 3)  # 3 + 6 + 9
        18
    """
    if n <= m:
        return 0
    
    k = (n - 1) // m
    return m * k * (k + 1) // 2


def calculate_sum_3_or_5(n: int) -> int:
    """
    Calculate sum of all multiples of 3 or 5 below n.
    
    Uses inclusion-exclusion principle:
    Sum = (multiples of 3) + (multiples of 5) - (multiples of 15)
    
    Time Complexity: O(1)
    
    Args:
        n: Upper bound (exclusive)
        
    Returns:
        Sum of all multiples of 3 or 5 below n
        
    Example:
        >>> calculate_sum_3_or_5(10)
        23
        >>> calculate_sum_3_or_5(100)
        2318
    """
    sum_3 = sum_multiples_below(n, 3)
    sum_5 = sum_multiples_below(n, 5)
    sum_15 = sum_multiples_below(n, 15)
    
    return sum_3 + sum_5 - sum_15


def solve_test_cases(test_cases: List[int]) -> List[int]:
    """
    Solve multiple test cases efficiently using deduplication.
    
    Strategy:
    1. Find unique N values from all test cases
    2. Calculate sum once for each unique N (O(1) per unique value)
    3. Map results back to original test case order
    
    Time Complexity: O(U) where U = number of unique values
    Space Complexity: O(U) for the cache
    
    Args:
        test_cases: List of N values (may contain duplicates)
        
    Returns:
        List of sums corresponding to each test case
        
    Example:
        >>> solve_test_cases([10, 100, 10])
        [23, 2318, 23]
    """
    # Calculate sum once per unique N value
    unique_sums = {n: calculate_sum_3_or_5(n) for n in set(test_cases)}
    
    # Map results back to original order
    return [unique_sums[n] for n in test_cases]


def main():
    """
    Main entry point for reading input and processing test cases.
    
    Input Format:
        First line: T (number of test cases)
        Next T lines: Each containing an integer N
        
    Constraints:
        1 ≤ T ≤ 10⁵
        1 ≤ N ≤ 10⁹
        
    Output Format:
        T lines, each containing the sum for corresponding test case
    """
    # Read number of test cases
    t = int(input().strip())
    
    # Read all test cases
    test_cases = [int(input().strip()) for _ in range(t)]
    
    # Solve all test cases with deduplication
    results = solve_test_cases(test_cases)
    
    # Output results
    for result in results:
        print(result)


if __name__ == "__main__":
    main()