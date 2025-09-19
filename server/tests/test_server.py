#!/usr/bin/env python3
"""
Test server functionality: page types, connectivity, basic performance
"""

import requests
import time
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERVER_PORT, REGULAR_PAGE_DELAY, DELAY_PAGE_DELAY, FAILURE_PAGE_ERROR_RATE

BASE_URL = f"http://localhost:{SERVER_PORT}"

def test_page_types():
    """Test different page types work correctly"""
    print("Testing page types...")

    # Get sample pages
    response = requests.get(f"{BASE_URL}/graph/sample")
    sample = response.json()

    # Test each page type
    for page_type in ["regular", "delay", "failure", "cpu", "core"]:
        pages = [p for p in sample["pages"] if p["page_type"] == page_type]
        if not pages:
            continue

        page = pages[0]
        print(f"  Testing {page_type} page: {page['page_id']}")

        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/{page['page_id']}")
        elapsed = time.time() - start_time

        if page_type == "failure" and response.status_code == 500:
            print(f"    Failure page failed as expected")
            continue

        data = response.json()
        print(f"    Response time: {elapsed:.3f}s")

        # Check content structure
        if page_type in ["regular", "delay", "failure"]:
            assert "links" in data, f"{page_type} should have links"
            assert isinstance(data["links"], list), f"{page_type} links should be list"
        elif page_type == "cpu":
            assert "hashseed" in data, "CPU page should have hashseed"
            assert isinstance(data["hashseed"], str), "CPU hashseed should be string"
        elif page_type == "core":
            assert "hashseed" in data, "Core page should have hashseed"
            assert isinstance(data["hashseed"], dict), "Core hashseed should be dict"
            assert set(data["hashseed"].keys()) == {"1", "2", "3", "4"}, "Core should have keys 1-4"

        print(f"    ✓ {page_type} page structure correct")

    print("✓ All page types working")

def test_connectivity():
    """Test basic graph connectivity"""
    print("Testing connectivity...")

    visited = set()
    to_visit = ["/api/"]

    # Crawl up to 50 pages
    while to_visit and len(visited) < 50:
        current = to_visit.pop(0)
        if current in visited:
            continue

        visited.add(current)

        try:
            response = requests.get(f"{BASE_URL}{current}")
            data = response.json()

            # Add linked pages
            for page_id in data.get("links", []):
                link_path = f"/api/{page_id}"
                if link_path not in visited:
                    to_visit.append(link_path)
        except:
            continue

    print(f"  Crawled {len(visited)} pages successfully")
    assert len(visited) >= 10, "Should be able to crawl at least 10 pages"
    print("✓ Basic connectivity working")

def test_performance():
    """Basic performance test"""
    print("Testing performance...")

    # Get a few regular pages
    response = requests.get(f"{BASE_URL}/graph/sample")
    sample = response.json()
    regular_pages = [p for p in sample["pages"] if p["page_type"] == "regular"][:5]

    if regular_pages:
        # Sequential timing
        start_time = time.time()
        for page in regular_pages:
            requests.get(f"{BASE_URL}/api/{page['page_id']}")
        sequential_time = time.time() - start_time

        print(f"  Sequential: {len(regular_pages)} pages in {sequential_time:.2f}s")
        print(f"  Average: {sequential_time/len(regular_pages):.3f}s per page")

        # Should be roughly 500ms per page
        expected_time = len(regular_pages) * REGULAR_PAGE_DELAY
        assert abs(sequential_time - expected_time) < 1.0, f"Timing off: expected ~{expected_time}s, got {sequential_time:.2f}s"

        print("✓ Performance timing correct")

def main():
    print("Server Test Suite")

    # Check server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=1)
    except:
        print("Server not running! Start with: docker compose up")
        exit(1)

    tests = [test_page_types, test_connectivity, test_performance]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            exit(1)

    print("\n✓ All server tests passed!")

if __name__ == "__main__":
    main()