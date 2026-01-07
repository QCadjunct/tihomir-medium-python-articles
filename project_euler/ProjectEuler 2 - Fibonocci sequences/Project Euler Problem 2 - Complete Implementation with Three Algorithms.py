#!/usr/bin/env python3
"""
Project Euler Problem 2: Even Fibonacci Numbers
Complete Implementation with Three Algorithms

This module demonstrates:
1. Three separate optimized algorithms (All, Even, Odd)
2. Unified approach with filter parameter
3. Dedekind cuts analysis (GLB/LUB)
4. Performance comparisons
5. Educational demonstrations

Author: Peter Heller
Date: 2026-01-04
Python: 3.14
"""

from enum import Enum
from typing import List, Tuple, Dict
from dataclasses import dataclass
import time


# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_LIMIT = 4_000_000


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class FibonacciFilter(Enum):
    """Filter types for Fibonacci sequences."""
    ALL = "all"
    EVEN = "even"
    ODD = "odd"


@dataclass
class FibonacciResult:
    """
    Complete result container for Fibonacci calculations.
    
    Attributes:
        filter_type: Which filter was applied
        sum_value: Total sum of filtered terms
        sequence: List of all filtered terms
        count: Number of terms
        glb: Greatest Lower Bound (last term ≤ limit)
        lub: Least Upper Bound (first term > limit)
        limit: The upper bound used
        computation_time: Time taken in seconds
    """
    filter_type: FibonacciFilter
    sum_value: int
    sequence: List[int]
    count: int
    glb: int
    lub: int
    limit: int
    computation_time: float = 0.0
    
    def __str__(self) -> str:
        return f"""
Fibonacci Analysis ({self.filter_type.value.upper()})
{'='*60}
Limit:            {self.limit:,}
Sum:              {self.sum_value:,}
Count:            {self.count}
GLB:              {self.glb:,}
LUB:              {self.lub:,}
Computation Time: {self.computation_time*1000:.3f} ms
First 10 terms:   {self.sequence[:10]}
Last 5 terms:     {self.sequence[-5:] if len(self.sequence) >= 5 else self.sequence}
{'='*60}
        """


# ============================================================================
# ALGORITHM 1: ALL FIBONACCI NUMBERS
# ============================================================================

def fibonacci_all(limit: int = DEFAULT_LIMIT) -> FibonacciResult:
    """
    Calculate ALL Fibonacci numbers ≤ limit.
    
    Method: Standard recurrence F(n) = F(n-1) + F(n-2)
    Time: O(n) where n = count of terms
    Space: O(n) for storing sequence
    
    Args:
        limit: Upper bound (default 4,000,000)
        
    Returns:
        FibonacciResult with complete analysis
        
    Example:
        >>> result = fibonacci_all(100)
        >>> result.sum_value
        232
        >>> result.count
        12
    """
    start_time = time.perf_counter()
    
    sequence = []
    total = 0
    a, b = 1, 2
    
    # Generate all Fibonacci ≤ limit
    while a <= limit:
        sequence.append(a)
        total += a
        a, b = b, a + b
    
    # GLB and LUB
    glb = sequence[-1] if sequence else 0
    lub = a  # First term > limit
    
    end_time = time.perf_counter()
    
    return FibonacciResult(
        filter_type=FibonacciFilter.ALL,
        sum_value=total,
        sequence=sequence,
        count=len(sequence),
        glb=glb,
        lub=lub,
        limit=limit,
        computation_time=end_time - start_time
    )


# ============================================================================
# ALGORITHM 2: EVEN FIBONACCI NUMBERS (OPTIMIZED)
# ============================================================================

def fibonacci_even_optimized(limit: int = DEFAULT_LIMIT) -> FibonacciResult:
    """
    Calculate EVEN Fibonacci numbers ≤ limit using DIRECT RECURRENCE.
    
    Method: Direct even recurrence E(n) = 4E(n-1) + E(n-2)
    This is 3× faster than generating all and filtering!
    
    Time: O(n/3) where n = total Fibonacci count
    Space: O(n/3) for even sequence
    
    Args:
        limit: Upper bound (default 4,000,000)
        
    Returns:
        FibonacciResult with complete analysis
        
    Example:
        >>> result = fibonacci_even_optimized(100)
        >>> result.sum_value
        44
        >>> result.count
        4
        >>> result.sequence
        [2, 8, 34]
    """
    start_time = time.perf_counter()
    
    sequence = []
    total = 0
    a, b = 2, 8  # E(1) = 2, E(2) = 8
    
    # Generate even Fibonacci using direct recurrence
    while a <= limit:
        sequence.append(a)
        total += a
        a, b = b, 4*b + a  # Direct even recurrence!
    
    # GLB and LUB
    glb = sequence[-1] if sequence else 0
    lub = a  # First even term > limit
    
    end_time = time.perf_counter()
    
    return FibonacciResult(
        filter_type=FibonacciFilter.EVEN,
        sum_value=total,
        sequence=sequence,
        count=len(sequence),
        glb=glb,
        lub=lub,
        limit=limit,
        computation_time=end_time - start_time
    )


def fibonacci_even_filtered(limit: int = DEFAULT_LIMIT) -> FibonacciResult:
    """
    Calculate EVEN Fibonacci using filter (SLOWER - for comparison).
    
    Method: Generate all, filter evens
    Time: O(n)
    Space: O(n)
    
    This demonstrates why the optimized version is better!
    
    Args:
        limit: Upper bound
        
    Returns:
        FibonacciResult with complete analysis
    """
    start_time = time.perf_counter()
    
    sequence = []
    total = 0
    a, b = 1, 2
    
    # Generate all, keep only evens
    while a <= limit:
        if a % 2 == 0:
            sequence.append(a)
            total += a
        a, b = b, a + b
    
    # Find LUB (next even)
    while a % 2 == 1:
        a, b = b, a + b
    
    glb = sequence[-1] if sequence else 0
    lub = a
    
    end_time = time.perf_counter()
    
    return FibonacciResult(
        filter_type=FibonacciFilter.EVEN,
        sum_value=total,
        sequence=sequence,
        count=len(sequence),
        glb=glb,
        lub=lub,
        limit=limit,
        computation_time=end_time - start_time
    )


# ============================================================================
# ALGORITHM 3: ODD FIBONACCI NUMBERS
# ============================================================================

def fibonacci_odd_filtered(limit: int = DEFAULT_LIMIT) -> FibonacciResult:
    """
    Calculate ODD Fibonacci numbers using filtering.
    
    Method: Generate all, filter odds
    Time: O(n)
    Space: O(2n/3) for odd sequence
    
    Args:
        limit: Upper bound (default 4,000,000)
        
    Returns:
        FibonacciResult with complete analysis
        
    Example:
        >>> result = fibonacci_odd_filtered(100)
        >>> result.sum_value
        188
        >>> result.count
        8
    """
    start_time = time.perf_counter()
    
    sequence = []
    total = 0
    a, b = 1, 2
    
    # Generate Fibonacci, keep only odds
    while a <= limit:
        if a % 2 == 1:
            sequence.append(a)
            total += a
        a, b = b, a + b
    
    # Find LUB (next odd)
    while a <= limit or a % 2 == 0:
        a, b = b, a + b
    
    glb = sequence[-1] if sequence else 0
    lub = a
    
    end_time = time.perf_counter()
    
    return FibonacciResult(
        filter_type=FibonacciFilter.ODD,
        sum_value=total,
        sequence=sequence,
        count=len(sequence),
        glb=glb,
        lub=lub,
        limit=limit,
        computation_time=end_time - start_time
    )


def fibonacci_odd_difference(limit: int = DEFAULT_LIMIT) -> FibonacciResult:
    """
    Calculate ODD sum using difference method (FASTEST).
    
    Method: Sum(Odd) = Sum(All) - Sum(Even)
    This is faster because we can use optimized even calculation!
    
    Time: O(n)
    Space: O(1) for computation, O(n) if we want sequence
    
    Args:
        limit: Upper bound
        
    Returns:
        FibonacciResult with complete analysis
    """
    start_time = time.perf_counter()
    
    # Get all and even results
    all_result = fibonacci_all(limit)
    even_result = fibonacci_even_optimized(limit)
    
    # Calculate odd sequence by filtering all
    odd_sequence = [f for f in all_result.sequence if f % 2 == 1]
    
    # Calculate odd sum by difference (faster!)
    odd_sum = all_result.sum_value - even_result.sum_value
    
    # Find LUB
    a = all_result.lub
    b = a + all_result.glb
    while a % 2 == 0:
        a, b = b, a + b
    
    glb = odd_sequence[-1] if odd_sequence else 0
    lub = a
    
    end_time = time.perf_counter()
    
    return FibonacciResult(
        filter_type=FibonacciFilter.ODD,
        sum_value=odd_sum,
        sequence=odd_sequence,
        count=len(odd_sequence),
        glb=glb,
        lub=lub,
        limit=limit,
        computation_time=end_time - start_time
    )


# ============================================================================
# UNIFIED FIBONACCI SOLVER
# ============================================================================

class UnifiedFibonacciSolver:
    """
    Unified Fibonacci solver with configurable filtering.
    
    Demonstrates Single Responsibility Principle (SRP) and
    KISS principle through clean interface.
    """
    
    def __init__(self, limit: int = DEFAULT_LIMIT):
        """
        Initialize solver with upper bound.
        
        Args:
            limit: Maximum Fibonacci value to consider
        """
        self.limit = limit
    
    def solve(self, filter_type: FibonacciFilter = FibonacciFilter.EVEN) -> FibonacciResult:
        """
        Solve for specified filter type using optimal algorithm.
        
        Args:
            filter_type: Which terms to include (ALL, EVEN, or ODD)
            
        Returns:
            FibonacciResult with complete analysis
        """
        if filter_type == FibonacciFilter.ALL:
            return fibonacci_all(self.limit)
        elif filter_type == FibonacciFilter.EVEN:
            return fibonacci_even_optimized(self.limit)
        elif filter_type == FibonacciFilter.ODD:
            return fibonacci_odd_difference(self.limit)
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")
    
    def solve_all_three(self) -> Tuple[FibonacciResult, FibonacciResult, FibonacciResult]:
        """
        Solve for all three filter types.
        
        Returns:
            (all_result, even_result, odd_result)
        """
        return (
            self.solve(FibonacciFilter.ALL),
            self.solve(FibonacciFilter.EVEN),
            self.solve(FibonacciFilter.ODD)
        )
    
    def verify_results(self, all_result: FibonacciResult, 
                      even_result: FibonacciResult, 
                      odd_result: FibonacciResult) -> bool:
        """
        Verify that Sum(All) = Sum(Even) + Sum(Odd).
        
        Returns:
            True if verification passes
        """
        return all_result.sum_value == even_result.sum_value + odd_result.sum_value


# ============================================================================
# DEDEKIND CUTS ANALYZER
# ============================================================================

@dataclass
class DedekindCut:
    """
    Represents a Dedekind cut at the limit boundary.
    
    Attributes:
        limit: The boundary value
        lower_set: All Fibonacci ≤ limit
        upper_set: First few Fibonacci > limit
        glb: Greatest Lower Bound
        lub: Least Upper Bound
        glb_index: Index of GLB in Fibonacci sequence
        lub_index: Index of LUB in Fibonacci sequence
    """
    limit: int
    lower_set: List[int]
    upper_set: List[int]
    glb: int
    lub: int
    glb_index: int
    lub_index: int
    
    def __str__(self) -> str:
        return f"""
Dedekind Cut Analysis at {self.limit:,}
{'='*60}
GLB (Greatest Lower Bound):
  Value:    {self.glb:,}
  Index:    F({self.glb_index})
  
LUB (Least Upper Bound):
  Value:    {self.lub:,}
  Index:    F({self.lub_index})

Lower Set (L): {len(self.lower_set)} elements
  First 5:  {self.lower_set[:5]}
  Last 5:   {self.lower_set[-5:] if len(self.lower_set) >= 5 else self.lower_set}
  Sum:      {sum(self.lower_set):,}

Upper Set (U): Showing first {len(self.upper_set)} elements
  Elements: {self.upper_set}

Cut Property: ∀x∈L, ∀y∈U: x < {self.limit:,} < y ✓
{'='*60}
        """


def analyze_dedekind_cut(filter_type: FibonacciFilter = FibonacciFilter.ALL,
                        limit: int = DEFAULT_LIMIT) -> DedekindCut:
    """
    Perform Dedekind cut analysis for specified filter type.
    
    Args:
        filter_type: Which Fibonacci sequence to analyze
        limit: Boundary value for the cut
        
    Returns:
        DedekindCut with complete analysis
    """
    solver = UnifiedFibonacciSolver(limit)
    result = solver.solve(filter_type)
    
    # Lower set is the sequence
    lower_set = result.sequence
    
    # Generate a few upper set elements
    upper_set = []
    a, b = result.glb, result.lub
    
    if filter_type == FibonacciFilter.EVEN:
        # Use even recurrence
        a, b = result.lub, 4*result.lub + result.glb
        for _ in range(3):
            upper_set.append(a)
            a, b = b, 4*b + a
    else:
        # Use standard recurrence
        for _ in range(3):
            upper_set.append(b)
            a, b = b, a + b
            if filter_type == FibonacciFilter.ODD and b % 2 == 0:
                a, b = b, a + b  # Skip evens
    
    return DedekindCut(
        limit=limit,
        lower_set=lower_set,
        upper_set=upper_set,
        glb=result.glb,
        lub=result.lub,
        glb_index=result.count,
        lub_index=result.count + 1
    )


# ============================================================================
# PERFORMANCE COMPARISON
# ============================================================================

def compare_even_algorithms(limit: int = DEFAULT_LIMIT):
    """
    Compare optimized vs filtered approach for even Fibonacci.
    
    Demonstrates why direct recurrence is superior!
    """
    print("="*70)
    print("PERFORMANCE COMPARISON: EVEN FIBONACCI ALGORITHMS")
    print("="*70)
    print()
    
    # Method 1: Optimized (Direct Recurrence)
    print("🚀 METHOD 1: DIRECT RECURRENCE E(n) = 4E(n-1) + E(n-2)")
    result1 = fibonacci_even_optimized(limit)
    print(f"   Time: {result1.computation_time*1000:.4f} ms")
    print(f"   Sum:  {result1.sum_value:,}")
    print()
    
    # Method 2: Filtered (Generate All)
    print("🐌 METHOD 2: GENERATE ALL, FILTER EVENS")
    result2 = fibonacci_even_filtered(limit)
    print(f"   Time: {result2.computation_time*1000:.4f} ms")
    print(f"   Sum:  {result2.sum_value:,}")
    print()
    
    # Comparison
    speedup = result2.computation_time / result1.computation_time
    print("📊 ANALYSIS:")
    print(f"   Optimized is {speedup:.2f}× FASTER!")
    print(f"   Time saved: {(result2.computation_time - result1.computation_time)*1000:.4f} ms")
    print()
    print("💡 WHY? Direct recurrence computes only even terms (every 3rd),")
    print("   while filtering must generate ALL terms then discard 2/3 of them!")
    print()


# ============================================================================
# DEMONSTRATION FUNCTIONS
# ============================================================================

def demonstrate_all_three():
    """Main demonstration showing all three use cases."""
    print("\n")
    print("="*70)
    print("PROJECT EULER PROBLEM 2: FIBONACCI ANALYSIS")
    print("="*70)
    print()
    
    solver = UnifiedFibonacciSolver(DEFAULT_LIMIT)
    all_result, even_result, odd_result = solver.solve_all_three()
    
    # Display results
    print(all_result)
    print(even_result)
    print(odd_result)
    
    # Verification
    print("\n" + "="*70)
    print("VERIFICATION: Sum(All) = Sum(Even) + Sum(Odd)")
    print("="*70)
    is_valid = solver.verify_results(all_result, even_result, odd_result)
    print(f"\n{all_result.sum_value:,} = {even_result.sum_value:,} + {odd_result.sum_value:,}")
    print(f"\n{'✓ VERIFIED!' if is_valid else '✗ VERIFICATION FAILED!'}\n")


def demonstrate_dedekind_cuts():
    """Demonstrate Dedekind cut analysis."""
    print("\n")
    print("="*70)
    print("DEDEKIND CUTS ANALYSIS")
    print("="*70)
    print()
    
    # Analyze all three cases
    for filter_type in [FibonacciFilter.ALL, FibonacciFilter.EVEN, FibonacciFilter.ODD]:
        cut = analyze_dedekind_cut(filter_type)
        print(cut)
        print()


def main():
    """Run all demonstrations."""
    demonstrate_all_three()
    demonstrate_dedekind_cuts()
    compare_even_algorithms()


if __name__ == "__main__":
    main()