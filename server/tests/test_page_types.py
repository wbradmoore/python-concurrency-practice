#!/usr/bin/env python3
"""
Test to verify that the different page types work correctly:
- Regular pages with 500ms delay at /api/[id]
- Delay pages with 5000ms delay at /api/delay/[id]
"""

import requests
import time
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DELAY_PAGE_PROBABILITY, REGULAR_PAGE_DELAY, DELAY_PAGE_DELAY,
    SERVER_PORT
)

BASE_URL = f"http://localhost:{SERVER_PORT}"

def test_page_type_distribution():
    """Test that page types are distributed correctly"""
    print("Testing page type distribution...")

    # Get stats
    response = requests.get(f"{BASE_URL}/graph/stats")
    stats = response.json()

    # Check distribution
    regular_count = stats["page_types"]["regular"]["count"]
    delay_count = stats["page_types"]["delay"]["count"]
    total = regular_count + delay_count

    regular_pct = (regular_count / total) * 100
    delay_pct = (delay_count / total) * 100

    print(f"  Regular pages: {regular_count} ({regular_pct:.1f}%)")
    print(f"  Delay pages: {delay_count} ({delay_pct:.1f}%)")

    # Should match configured probabilities (with some tolerance)
    expected_regular = (1 - DELAY_PAGE_PROBABILITY) * 100
    expected_delay = DELAY_PAGE_PROBABILITY * 100
    tolerance = 5  # 5% tolerance

    assert expected_regular - tolerance <= regular_pct <= expected_regular + tolerance, \
        f"Regular pages should be ~{expected_regular}%, got {regular_pct:.1f}%"
    assert expected_delay - tolerance <= delay_pct <= expected_delay + tolerance, \
        f"Delay pages should be ~{expected_delay}%, got {delay_pct:.1f}%"

    print("  Distribution looks correct")
    return True

def test_regular_page_timing():
    """Test that regular pages have ~500ms delay"""
    print("\nTesting regular page timing...")

    # Get a sample to find regular pages
    response = requests.get(f"{BASE_URL}/graph/sample")
    sample = response.json()

    regular_pages = [p for p in sample["pages"] if p["page_type"] == "regular"]
    if not regular_pages:
        print("  No regular pages in sample, skipping timing test")
        return True

    page = regular_pages[0]
    print(f"  Testing page: {page['url']}")

    # Time the request
    start_time = time.time()
    response = requests.get(f"{BASE_URL}{page['url']}")
    elapsed = time.time() - start_time

    data = response.json()
    print(f"  Actual delay: {elapsed:.3f}s")
    print(f"  Reported delay: {data['delay_ms']}ms")

    # Should match configured delay
    expected_delay = REGULAR_PAGE_DELAY
    tolerance = 0.1  # 100ms tolerance

    assert expected_delay - tolerance <= elapsed <= expected_delay + tolerance, \
        f"Regular page should take ~{expected_delay}s, took {elapsed:.3f}s"
    assert data["delay_ms"] == int(expected_delay * 1000), \
        f"Should report {int(expected_delay * 1000)}ms delay, got {data['delay_ms']}ms"

    print("  Regular page timing correct")
    return True

def test_delay_page_timing():
    """Test that delay pages have ~5000ms delay"""
    print("\nTesting delay page timing...")

    # Get samples until we find a delay page
    delay_page = None
    for _ in range(5):  # Try 5 samples
        response = requests.get(f"{BASE_URL}/graph/sample")
        sample = response.json()
        delay_pages = [p for p in sample["pages"] if p["page_type"] == "delay"]
        if delay_pages:
            delay_page = delay_pages[0]
            break

    if not delay_page:
        print("  No delay pages found in samples, skipping timing test")
        return True

    print(f"  Testing delay page: {delay_page['url']}")

    # Time the request
    start_time = time.time()
    response = requests.get(f"{BASE_URL}{delay_page['url']}")
    elapsed = time.time() - start_time

    data = response.json()
    print(f"  Actual delay: {elapsed:.3f}s")
    print(f"  Reported delay: {data['delay_ms']}ms")

    # Should match configured delay
    expected_delay = DELAY_PAGE_DELAY
    tolerance = 0.5  # 500ms tolerance

    assert expected_delay - tolerance <= elapsed <= expected_delay + tolerance, \
        f"Delay page should take ~{expected_delay}s, took {elapsed:.3f}s"
    assert data["delay_ms"] == int(expected_delay * 1000), \
        f"Should report {int(expected_delay * 1000)}ms delay, got {data['delay_ms']}ms"

    print("  Delay page timing correct")
    return True


def test_route_validation():
    """Test that wrong page types return 404"""
    print("\nTesting route validation...")

    # Get a regular page ID
    response = requests.get(f"{BASE_URL}/graph/sample")
    sample = response.json()
    regular_pages = [p for p in sample["pages"] if p["page_type"] == "regular"]

    if regular_pages:
        page_id = regular_pages[0]["page_id"]

        # Try to access regular page via delay route - should fail
        response = requests.get(f"{BASE_URL}/api/delay/{page_id}")
        assert response.status_code == 404, "Regular page should not be accessible via delay route"
        print("  Regular page correctly rejected via delay route")

    return True

def main():
    print("Page Types Test Suite")

    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=1)
    except:
        print("Server is not running! Start it with: docker compose up")
        exit(1)

    tests = [
        test_page_type_distribution,
        test_regular_page_timing,
        test_delay_page_timing,
        test_route_validation
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  Test failed: {e}")

    print(f"\nResults: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("All page type tests passed!")
        exit(0)
    else:
        print("Some tests failed")
        exit(1)

if __name__ == "__main__":
    main()