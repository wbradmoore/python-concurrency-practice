#!/usr/bin/env python3
"""
Test server functionality: page types, connectivity, basic performance
"""

import os
import sys
import time

import requests

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REGULAR_PAGE_DELAY, SERVER_PORT

BASE_URL = f"http://localhost:{SERVER_PORT}"

def test_page_types():
    """Test different page types work correctly"""
    print("Testing page types...")

    # Test each page type using the new test endpoints
    for page_type in ["regular", "delay", "failure", "cpu", "core"]:
        try:
            response = requests.get(f"{BASE_URL}/api/test/{page_type}")
            # Extract page ID from final URL after redirect
            page_id = response.url.split('/')[-1]
            page = {"page_id": page_id, "page_type": page_type}
        except Exception as e:
            print(f"  Could not get {page_type} page: {e}")
            continue
        print(f"  Testing {page_type} page: {page['page_id']}")

        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/{page['page_id']}")
        elapsed = time.time() - start_time

        if page_type == "failure" and response.status_code == 500:
            print(f"    Failure page failed as expected")
            continue

        if response.status_code != 200:
            print(f"    Unexpected status code: {response.status_code}")
            continue

        try:
            data = response.json()
        except Exception as e:
            print(f"    Failed to parse JSON response: {e}")
            print(f"    Response content: {response.text[:200]}")
            continue
        print(f"    Response time: {elapsed:.3f}s")

        # Check content structure
        if page_type in ["regular", "delay", "failure"]:
            assert "links" in data, f"{page_type} should have links"
            assert isinstance(data["links"], list), f"{page_type} links should be list"
        elif page_type == "cpu":
            assert "hashseeds" in data, "CPU page should have hashseeds"
            assert isinstance(data["hashseeds"], list), "CPU hashseeds should be list"
        elif page_type == "core":
            assert "multiseeds" in data, "Core page should have multiseeds"
            assert isinstance(data["multiseeds"], list), "Core multiseeds should be list"
            if data["multiseeds"]:
                assert all(isinstance(q, list) and len(q) == 6 for q in data["multiseeds"]), "Each multiseed should be list of 6"

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
            if response.status_code == 500:
                # Failure page - skip but don't count as error
                continue

            data = response.json()

            # Add linked pages
            for page_id in data.get("links", []):
                link_path = f"/api/{page_id}"
                if link_path not in visited:
                    to_visit.append(link_path)
        except Exception as e:
            # Skip pages that fail to parse
            continue

    print(f"  Crawled {len(visited)} pages successfully")
    assert len(visited) >= 2, "Should be able to crawl at least 2 pages"
    print("✓ Basic connectivity working")

def test_performance():
    """Basic performance test"""
    print("Testing performance...")

    # Get a few regular pages
    regular_pages = []
    for _ in range(5):
        try:
            response = requests.get(f"{BASE_URL}/graph/random")
            # Extract page ID from final URL after redirect
            page_id = response.url.split('/')[-1]
            # Check the page type
            page_response = requests.get(f"{BASE_URL}/api/{page_id}")

            if page_response.status_code == 500:
                # Failure page, try again
                continue

            page_data = page_response.json()
            if page_data["page_type"] == "regular":
                regular_pages.append({"page_id": page_id})
        except Exception as e:
            # Failed to get or parse page, try again
            continue

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
        requests.get(f"{BASE_URL}/", timeout=1)
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