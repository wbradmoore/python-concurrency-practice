#!/usr/bin/env python3
"""
Quick test for CPU/core hashseed computation.
"""

import requests
import hashlib
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERVER_PORT, CPU_PAGE_ITERATIONS, CORE_PAGE_ITERATIONS_PER_CHAR

BASE_URL = f"http://localhost:{SERVER_PORT}"

def test_cpu_seed_computation():
    """Test CPU seed computation"""
    print("Testing CPU seed computation...")

    # Get a CPU page
    response = requests.get(f"{BASE_URL}/api/test/cpu")
    cpu_page_id = response.url.split('/')[-1]

    # Fetch the page
    response = requests.get(f"{BASE_URL}/api/{cpu_page_id}")
    data = response.json()

    if "hashseeds" not in data or not data["hashseeds"]:
        print(f"  CPU page {cpu_page_id} has no hashseeds")
        return True  # Not an error, page might not have links

    seed = data["hashseeds"][0]
    print(f"  CPU page {cpu_page_id}")
    print(f"  Hashseed: {seed}")

    # Compute the target
    result = seed
    for i in range(CPU_PAGE_ITERATIONS):
        result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
    target = result[:4]
    print(f"  Computed target: {target}")

    # Verify the target exists
    response = requests.get(f"{BASE_URL}/api/{target}")
    if response.status_code in [200, 500]:
        print(f"  ✓ Target page {target} exists")
        return True
    else:
        print(f"  ✗ Target page {target} not found (status {response.status_code})")
        return False

def test_core_seed_computation():
    """Test core seed computation"""
    print("Testing core seed computation...")

    # Get a core page
    response = requests.get(f"{BASE_URL}/api/test/core")
    core_page_id = response.url.split('/')[-1]

    # Fetch the page
    response = requests.get(f"{BASE_URL}/api/{core_page_id}")
    data = response.json()

    if "quadseeds" not in data or not data["quadseeds"]:
        print(f"  Core page {core_page_id} has no quadseeds")
        return True  # Not an error, page might not have links

    quadseed = data["quadseeds"][0]
    print(f"  Core page {core_page_id}")

    # Compute the 4-character result
    target = ""
    for i, seed in enumerate(quadseed):
        result = seed
        for j in range(CORE_PAGE_ITERATIONS_PER_CHAR):
            result = hashlib.md5(f"{result}_{j}".encode()).hexdigest()
        target += result[0]
        print(f"    Position {i+1}: {seed} -> '{result[0]}'")

    print(f"  Computed target: {target}")

    # Verify the target exists
    response = requests.get(f"{BASE_URL}/api/{target}")
    if response.status_code in [200, 500]:
        print(f"  ✓ Target page {target} exists")
        return True
    else:
        print(f"  ✗ Target page {target} not found (status {response.status_code})")
        return False

def main():
    print("Quick Hashseed Test")
    print("=" * 50)

    # Check server is running
    try:
        requests.get(f"{BASE_URL}/", timeout=1)
    except:
        print("Server not running! Start with: docker compose up")
        exit(1)

    # Run tests
    cpu_passed = test_cpu_seed_computation()
    print()
    core_passed = test_core_seed_computation()

    print()
    print("=" * 50)
    if cpu_passed and core_passed:
        print("✓ All tests passed")
    else:
        print("✗ Tests failed")

if __name__ == "__main__":
    main()