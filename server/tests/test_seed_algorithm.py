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
    return result[:4]  # First 4 chars are the target page ID

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

    # Test some example seeds
    test_seeds = ["abcd1234", "test5678", "seed9012", "example123"]

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
    print("Testing if we can find a seed that produces a specific target...")

    # Try to find a seed that produces page ID "1234"
    target = "1234"
    found = False
    for i in range(1000):
        seed = f"test{i:04d}"
        result = hash_cpu_seed(seed)
        if result == target:
            print(f"Found seed '{seed}' that produces target '{target}'!")
            found = True
            break
        elif i < 10:  # Show first 10 attempts
            print(f"  {seed} -> {result}")

    if not found:
        print(f"No seed found that produces '{target}' in 1000 attempts")

    print()
    print("Testing if we can find a seed that produces character 'a'...")

    # Try to find a seed that produces character 'a'
    target_char = 'a'
    found = False
    for i in range(100):
        seed = f"char{i:04d}"
        result = hash_core_seed(seed)
        if result == target_char:
            print(f"Found seed '{seed}' that produces character '{target_char}'!")
            found = True
            break
        elif i < 10:
            print(f"  {seed} -> '{result}'")

    if not found:
        print(f"No seed found that produces '{target_char}' in 100 attempts")

if __name__ == "__main__":
    test_algorithm()