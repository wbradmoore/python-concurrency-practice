#!/usr/bin/env python3
"""
Quick test for CPU/core hashseed logic with fewer iterations.
"""

import requests
import hashlib
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERVER_PORT

BASE_URL = f"http://localhost:{SERVER_PORT}"

# Use smaller iteration counts for quick testing
TEST_CPU_ITERATIONS = 1000
TEST_CORE_ITERATIONS = 250

def quick_hash_cpu_seed(seed):
    """Hash a CPU seed with fewer iterations for testing"""
    result = seed
    for i in range(TEST_CPU_ITERATIONS):
        result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
    return result[:4]

def decode_cpu_seed(seed):
    """Decode the target from the CPU seed format"""
    # Seed format: "cpu_<reversed_target>_<salt>"
    parts = seed.split('_')
    if len(parts) >= 3 and parts[0] == 'cpu':
        encoded = parts[1]
        # Reverse to get original target
        target = ''.join(reversed(encoded))
        return target
    return None

def test_cpu_seed_encoding():
    """Test CPU seed encoding/decoding logic"""
    print("Testing CPU seed encoding...")

    # Get a CPU page
    response = requests.get(f"{BASE_URL}/test/cpu")
    cpu_page_id = response.url.split('/')[-1]

    # Fetch the page
    response = requests.get(f"{BASE_URL}/api/{cpu_page_id}")
    data = response.json()

    seed = data["hashseed"]
    print(f"  CPU page {cpu_page_id}")
    print(f"  Hashseed: {seed}")

    # Decode the target from the seed
    decoded_target = decode_cpu_seed(seed)
    print(f"  Decoded target: {decoded_target}")

    # Check if decoded target is valid
    if decoded_target:
        response = requests.get(f"{BASE_URL}/api/{decoded_target}")
        if response.status_code in [200, 500]:
            print(f"  ✓ Decoded target {decoded_target} is a valid page")
            return True
        else:
            print(f"  ✗ Decoded target {decoded_target} not found (status {response.status_code})")
            # Show what pages do exist for debugging
            response = requests.get(f"{BASE_URL}/")
            root_data = response.json()
            print(f"    Total pages in graph: {root_data.get('total_pages', 'unknown')}")
            return False
    else:
        print(f"  ✗ Could not decode target from seed")
        return False

def test_core_seed_encoding():
    """Test core seed encoding logic"""
    print("Testing core seed encoding...")

    # Get a core page
    response = requests.get(f"{BASE_URL}/test/core")
    core_page_id = response.url.split('/')[-1]

    # Fetch the page
    response = requests.get(f"{BASE_URL}/api/{core_page_id}")
    data = response.json()

    hashseeds = data["hashseed"]
    print(f"  Core page {core_page_id}")

    # Decode each seed
    decoded_chars = []
    for pos in ["1", "2", "3", "4"]:
        seed = hashseeds[pos]
        # Seed format: "core_<char>_<index>_<salt>"
        parts = seed.split('_')
        if len(parts) >= 4 and parts[0] == 'core':
            char = parts[1]
            decoded_chars.append(char)
            print(f"    Position {pos}: {seed} -> '{char}'")

    decoded_target = ''.join(decoded_chars)
    print(f"  Decoded target: {decoded_target}")

    # Check if decoded target is valid
    response = requests.get(f"{BASE_URL}/api/{decoded_target}")
    if response.status_code in [200, 500]:
        print(f"  ✓ Decoded target {decoded_target} is a valid page")
        return True
    else:
        print(f"  ✗ Decoded target {decoded_target} not found (status {response.status_code})")
        return False

def main():
    print("Quick Hashseed Test")
    print("=" * 50)

    # Check server
    try:
        requests.get(f"{BASE_URL}/", timeout=1)
    except:
        print("Server not running! Start with: cd server && ./newserver.sh")
        exit(1)

    # Run tests
    print()
    cpu_passed = test_cpu_seed_encoding()
    print()
    core_passed = test_core_seed_encoding()

    print()
    print("=" * 50)
    if cpu_passed and core_passed:
        print("✓ Quick tests passed!")
        print("\nNote: The actual implementation requires proper hashing.")
        print("The seeds encode the target, but clients must do the CPU work.")
    else:
        print("✗ Tests failed - check seed generation logic")

if __name__ == "__main__":
    main()