#!/usr/bin/env python3
"""
Test that CPU and core page hashseeds deterministically produce valid page IDs.
"""

import requests
import hashlib
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERVER_PORT, CPU_PAGE_ITERATIONS, CORE_PAGE_ITERATIONS_PER_CHAR

BASE_URL = f"http://localhost:{SERVER_PORT}"

def hash_cpu_seed(seed):
    """Hash a CPU seed the required number of times to get target page ID"""
    result = seed
    for _ in range(CPU_PAGE_ITERATIONS):
        result = hashlib.md5(result.encode()).hexdigest()
    return result[:6]  # First 6 chars are the target page ID

def hash_core_seed(seed):
    """Hash a core seed to get one character of the target"""
    result = seed
    for _ in range(CORE_PAGE_ITERATIONS_PER_CHAR):
        result = hashlib.md5(result.encode()).hexdigest()
    return result[0]  # First char is the target character

def test_cpu_hashseed():
    """Test that CPU hashseed produces a valid page ID"""
    print("Testing CPU hashseed validation...")

    # Get a CPU page
    response = requests.get(f"{BASE_URL}/api/test/cpu")
    cpu_page_id = response.url.split('/')[-1]

    # Fetch the page to get its hashseed
    response = requests.get(f"{BASE_URL}/api/{cpu_page_id}")
    data = response.json()

    assert "hashseeds" in data, "CPU page should have hashseeds field"
    assert isinstance(data["hashseeds"], list), "CPU hashseeds should be a list"

    if not data["hashseeds"]:
        print("  ⚠ No hashseeds found")
        return True

    seed = data["hashseeds"][0]
    print(f"  CPU page {cpu_page_id} has hashseed: {seed}")

    # Hash the seed to get the target page ID
    print(f"  Hashing {CPU_PAGE_ITERATIONS:,} times...")
    computed_target = hash_cpu_seed(seed)
    print(f"  Computed target page ID: {computed_target}")

    # Verify the target page exists
    response = requests.get(f"{BASE_URL}/api/{computed_target}")
    if response.status_code == 200:
        print(f"  ✓ Target page {computed_target} exists!")
        target_data = response.json()
        print(f"    Target is a {target_data['page_type']} page")
        return True
    elif response.status_code == 500:
        print(f"  ✓ Target page {computed_target} exists (failure page that returned 500)")
        return True
    else:
        print(f"  ✗ Target page {computed_target} returned status {response.status_code}")
        return False

def test_core_hashseed():
    """Test that core hashseeds produce a valid page ID"""
    print("Testing core hashseed validation...")

    # Get a core page
    response = requests.get(f"{BASE_URL}/api/test/core")
    core_page_id = response.url.split('/')[-1]

    # Fetch the page to get its hashseed dict
    response = requests.get(f"{BASE_URL}/api/{core_page_id}")
    data = response.json()

    assert "quadseeds" in data, "Core page should have quadseeds field"
    assert isinstance(data["quadseeds"], list), "Core quadseeds should be a list"

    if not data["quadseeds"]:
        print("  ⚠ No quadseeds found")
        return True

    hexseed = data["quadseeds"][0]
    assert isinstance(hexseed, list) and len(hexseed) == 6, "Each hexseed should be list of 6"

    hashseeds = {str(i+1): seed for i, seed in enumerate(hexseed)}
    print(f"  Core page {core_page_id} has hashseed dict with {len(hashseeds)} seeds")

    # Hash each seed in parallel to get the 6 characters
    print(f"  Hashing each seed {CORE_PAGE_ITERATIONS_PER_CHAR:,} times...")

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        for pos in ["1", "2", "3", "4", "5", "6"]:
            seed = hashseeds[pos]
            futures.append(executor.submit(hash_core_seed, seed))

        chars = []
        for i, future in enumerate(futures):
            char = future.result()
            chars.append(char)
            print(f"    Position {i+1}: {hashseeds[str(i+1)]} -> '{char}'")

    computed_target = "".join(chars)
    print(f"  Computed target page ID: {computed_target}")

    # Verify the target page exists
    response = requests.get(f"{BASE_URL}/api/{computed_target}")
    if response.status_code == 200:
        print(f"  ✓ Target page {computed_target} exists!")
        target_data = response.json()
        print(f"    Target is a {target_data['page_type']} page")
        return True
    elif response.status_code == 500:
        print(f"  ✓ Target page {computed_target} exists (failure page that returned 500)")
        return True
    else:
        print(f"  ✗ Target page {computed_target} returned status {response.status_code}")
        return False

def test_determinism():
    """Test that hashseeds are deterministic"""
    print("Testing hashseed determinism...")

    # Get the same CPU page multiple times
    response = requests.get(f"{BASE_URL}/api/test/cpu")
    cpu_page_id = response.url.split('/')[-1]

    seeds = []
    for i in range(3):
        response = requests.get(f"{BASE_URL}/api/{cpu_page_id}")
        data = response.json()
        if data.get("hashseeds"):
            seeds.append(data["hashseeds"][0] if data["hashseeds"] else None)

    if len(set(seeds)) == 1:
        print(f"  ✓ CPU page {cpu_page_id} returns same hashseed every time: {seeds[0]}")
    else:
        print(f"  ✗ CPU page {cpu_page_id} returns different hashseeds: {seeds}")
        return False

    # Test core page determinism
    response = requests.get(f"{BASE_URL}/api/test/core")
    core_page_id = response.url.split('/')[-1]

    seed_sets = []
    for i in range(3):
        response = requests.get(f"{BASE_URL}/api/{core_page_id}")
        data = response.json()
        if data.get("quadseeds"):
            seed_sets.append(str(data["quadseeds"][0] if data["quadseeds"] else None))

    if len(set(seed_sets)) == 1:
        print(f"  ✓ Core page {core_page_id} returns same hashseed dict every time")
    else:
        print(f"  ✗ Core page {core_page_id} returns different hashseed dicts")
        return False

    return True

def main():
    print("Hashseed Validation Tests")
    print("=" * 50)

    # Check server is running
    try:
        requests.get(f"{BASE_URL}/", timeout=1)
    except:
        print("Server not running! Start with: cd server && ./newserver.sh")
        exit(1)

    # Run tests
    tests = [
        test_cpu_hashseed,
        test_core_hashseed,
        test_determinism
    ]

    all_passed = True
    for test in tests:
        print()
        try:
            if not test():
                all_passed = False
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            all_passed = False
            print(f"✗ {test.__name__} failed with error: {e}")

    print()
    print("=" * 50)
    if all_passed:
        print("✓ All hashseed tests passed!")
        exit(0)
    else:
        print("✗ Some tests failed")
        exit(1)

if __name__ == "__main__":
    main()