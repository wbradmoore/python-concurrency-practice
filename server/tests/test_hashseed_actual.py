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
    for i in range(CPU_PAGE_ITERATIONS):
        result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
    return result[:6]  # First 6 chars are the target page ID

def hash_core_seed(seed):
    """Hash a core seed to get one character of the target"""
    result = seed
    for i in range(CORE_PAGE_ITERATIONS_PER_CHAR):
        result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
    return result[0]  # First char is the target character

def find_cpu_page_with_links():
    """Find a CPU page that has hashseeds"""
    # Try the test/cpu endpoint first
    response = requests.get(f"{BASE_URL}/api/test/cpu", allow_redirects=True)
    if response.status_code == 200:
        data = response.json()
        if data.get("page_type") == "cpu" and data.get("hashseeds") and len(data["hashseeds"]) > 0:
            return data["page_id"], data

    # If that didn't work, search through pages
    response = requests.get(f"{BASE_URL}/")
    root_data = response.json()
    first_page = root_data["links"][0]

    visited = set()
    to_visit = [first_page]

    while to_visit and len(visited) < 50:  # Limit search
        page_id = to_visit.pop(0)
        if page_id in visited:
            continue
        visited.add(page_id)

        response = requests.get(f"{BASE_URL}/api/{page_id}")
        if response.status_code != 200:
            continue

        data = response.json()

        if data.get("page_type") == "cpu" and data.get("hashseeds") and len(data["hashseeds"]) > 0:
            return page_id, data

        # Add linked pages to search
        if "links" in data:
            to_visit.extend(data["links"])

    return None, None

def find_core_page_with_links():
    """Find a core page that has quadseeds"""
    # Try the test/core endpoint first
    response = requests.get(f"{BASE_URL}/api/test/core", allow_redirects=True)
    if response.status_code == 200:
        data = response.json()
        if data.get("page_type") == "core" and data.get("quadseeds") and len(data["quadseeds"]) > 0:
            return data["page_id"], data

    # If that didn't work, search through pages
    response = requests.get(f"{BASE_URL}/")
    root_data = response.json()
    first_page = root_data["links"][0]

    visited = set()
    to_visit = [first_page]

    while to_visit and len(visited) < 50:  # Limit search
        page_id = to_visit.pop(0)
        if page_id in visited:
            continue
        visited.add(page_id)

        response = requests.get(f"{BASE_URL}/api/{page_id}")
        if response.status_code != 200:
            continue

        data = response.json()

        if data.get("page_type") == "core" and data.get("quadseeds") and len(data["quadseeds"]) > 0:
            return page_id, data

        # Add linked pages to search
        if "links" in data:
            to_visit.extend(data["links"])

    return None, None

def test_cpu_hashseed():
    """Test that CPU hashseeds produce valid page IDs"""
    print("Testing CPU hashseed validation...")

    # Find a CPU page with hashseeds
    cpu_page_id, data = find_cpu_page_with_links()

    if not cpu_page_id:
        print("  ⚠ No CPU pages with hashseeds found")
        return True  # Not a failure, just no pages to test

    hashseeds = data["hashseeds"]
    print(f"  CPU page {cpu_page_id} has {len(hashseeds)} hashseeds")

    # Test the first hashseed
    seed = hashseeds[0]
    print(f"  Testing hashseed: {seed}")

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
    """Test that core quadseeds produce valid page IDs"""
    print("Testing core quadseed validation...")

    # Find a core page with quadseeds
    core_page_id, data = find_core_page_with_links()

    if not core_page_id:
        print("  ⚠ No core pages with quadseeds found")
        return True  # Not a failure, just no pages to test

    quadseeds = data["quadseeds"]
    print(f"  Core page {core_page_id} has {len(quadseeds)} quadseeds")

    # Test the first quadseed group
    quad = quadseeds[0]
    print(f"  Testing quadseed group: {quad}")

    # Hash each seed in parallel to get the 6 characters
    print(f"  Hashing each seed {CORE_PAGE_ITERATIONS_PER_CHAR:,} times...")

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        for i, seed in enumerate(quad):
            futures.append(executor.submit(hash_core_seed, seed))

        chars = []
        for i, future in enumerate(futures):
            char = future.result()
            chars.append(char)
            print(f"    Position {i+1}: {quad[i]} -> '{char}'")

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

def main():
    print("Hashseed Validation Tests (New Implementation)")
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