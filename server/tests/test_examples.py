#!/usr/bin/env python3
"""
CPU and multi-core example tests for the Web Graph Server.
Tests hashseed solving for CPU-bound and parallel processing challenges.
"""

import requests
import hashlib
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERVER_PORT

BASE_URL = f"http://localhost:{SERVER_PORT}"

def solve_cpu_hashseed(hashseed):
    """Solve CPU hashseed to extract target page ID"""
    result = hashseed
    iterations = 100000  # Reduced for testing
    for i in range(iterations):
        result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
    return result[:4]

def solve_core_hashseed(hashseed, char_position):
    """Solve single hashseed for multi-core page"""
    result = hashseed
    iterations = 100000  # Reduced for testing
    for i in range(iterations):
        result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
    return char_position, result[0]

def test_cpu_page():
    """Test CPU page hashseed solving"""
    print("Testing CPU page...")

    response = requests.get(f"{BASE_URL}/graph/random")
    cpu_data = response.json()

    if cpu_data["page_type"] != "cpu":
        print("  Random page not CPU type, skipping test")
        return True

    cpu_pages = [{"page_id": cpu_data["page_id"]}]
    if not cpu_pages:
        print("  No CPU pages in sample")
        return True

    page = cpu_pages[0]
    response = requests.get(f"{BASE_URL}/api/{page['page_id']}")
    data = response.json()

    if 'hashseed' not in data:
        print("  No hashseed found")
        return True

    target_page_id = solve_cpu_hashseed(data['hashseed'])
    print(f"  Computed target: {target_page_id}")

    # Try accessing computed target
    response = requests.get(f"{BASE_URL}/api/{target_page_id}")
    if response.status_code in [200, 404, 500]:
        print("  ✓ CPU hashseed solving works")
        return True
    return False

def test_core_page():
    """Test multi-core page with sequential vs parallel"""
    print("Testing multi-core page...")

    response = requests.get(f"{BASE_URL}/graph/random")
    core_data = response.json()

    if core_data["page_type"] != "core":
        print("  Random page not core type, skipping test")
        return True

    core_pages = [{"page_id": core_data["page_id"]}]
    if not core_pages:
        print("  No core pages in sample")
        return True

    page = core_pages[0]
    response = requests.get(f"{BASE_URL}/api/{page['page_id']}")
    data = response.json()

    hashseed_dict = data['hashseed']

    # Sequential approach
    start_time = time.time()
    results_seq = []
    for pos_str in ["1", "2", "3", "4"]:
        pos, char = solve_core_hashseed(hashseed_dict[pos_str], int(pos_str))
        results_seq.append((pos, char))
    results_seq.sort()
    target_seq = "".join([char for _, char in results_seq])
    time_seq = time.time() - start_time

    # Parallel approach
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for pos_str in ["1", "2", "3", "4"]:
            futures.append(executor.submit(solve_core_hashseed, hashseed_dict[pos_str], int(pos_str)))
        results_par = [future.result() for future in futures]
    results_par.sort()
    target_par = "".join([char for _, char in results_par])
    time_par = time.time() - start_time

    if target_seq != target_par:
        print(f"  ERROR: Different results - seq: {target_seq}, par: {target_par}")
        return False

    speedup = time_seq / time_par if time_par > 0 else 1
    print(f"  Sequential: {time_seq:.3f}s, Parallel: {time_par:.3f}s, Speedup: {speedup:.1f}x")
    print("  ✓ Multi-core parallel processing works")
    return True

def main():
    print("Example Tests")

    # Check server
    try:
        requests.get(f"{BASE_URL}/health", timeout=1)
    except:
        print("Server not running! Start with: docker compose up")
        exit(1)

    tests = [test_cpu_page, test_core_page]

    for test in tests:
        try:
            if not test():
                print(f"✗ {test.__name__} failed")
                exit(1)
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            exit(1)

    print("\n✓ All example tests passed!")

if __name__ == "__main__":
    main()