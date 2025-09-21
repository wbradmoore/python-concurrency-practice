#!/usr/bin/env python3
"""
Test the hashseed algorithm itself with known seeds.
"""

import hashlib
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CPU_PAGE_ITERATIONS, CORE_PAGE_ITERATIONS_PER_CHAR

def hash_cpu_seed(seed):
    """Hash a CPU seed the required number of times to get target page ID"""
    result = seed
    for i in range(CPU_PAGE_ITERATIONS):
        result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
    return result[:6]  # First 6 chars are the target page ID

def hash_core_seed(seed):
    """Hash a core seed to get one character of the target"""
    result = seed
    for i in range(CORE_PAGE_ITERATIONS_PER_CHAR):
        result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
    return result[0]  # First char is the target character

def test_algorithm():
    """Test the hashseed algorithm with example seeds"""
    print("Testing hashseed algorithm...")
    print(f"CPU iterations: {CPU_PAGE_ITERATIONS}")
    print(f"Core iterations per char: {CORE_PAGE_ITERATIONS_PER_CHAR}")
    print()

    # Test just a couple example seeds (reduced to avoid timeout)
    test_seeds = ["abcd1234", "test5678"]

    print("CPU seed testing:")
    for seed in test_seeds:
        result = hash_cpu_seed(seed)
        print(f"  {seed} -> {result}")

    print()
    print("Core seed testing:")
    for seed in test_seeds:
        result = hash_core_seed(seed)
        print(f"  {seed} -> '{result}'")

    print()
    print("Note: Skipping brute-force search tests (would take too long with 5M iterations)")

if __name__ == "__main__":
    test_algorithm()