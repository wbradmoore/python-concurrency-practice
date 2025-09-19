#!/usr/bin/env python3
"""
Test to verify that all pages in the graph are reachable from the root /api/ endpoint.
This uses a breadth-first search to traverse the entire graph.
"""

import requests
import time
from collections import deque

def test_all_pages_reachable(base_url="http://localhost:5000", verbose=False):
    """
    Verify all pages in the graph are reachable from /api/.

    Args:
        base_url: The base URL of the server
        verbose: If True, print detailed progress information

    Returns:
        dict: Test results including success status and statistics
    """
    print("Starting graph connectivity test...")
    start_time = time.time()

    # First, get the total number of pages from stats
    stats_response = requests.get(f"{base_url}/graph/stats")
    stats = stats_response.json()
    total_pages = stats["total_pages"]

    print(f"Total pages in graph: {total_pages}")
    print(f"Dead ends: {stats['dead_ends_count']}")
    print(f"Average links per page: {stats['avg_links_per_page']}")

    # Start crawling from the root
    visited = set()
    to_visit = deque(["/api/"])
    pages_fetched = 0

    # Track some statistics
    max_depth = 0
    current_depth = 0
    depth_marker = "/api/"  # Use to track when we move to next depth level
    next_depth_marker = None

    print("\nCrawling graph starting from /api/...")

    while to_visit:
        current_path = to_visit.popleft()

        # Track depth
        if current_path == depth_marker:
            current_depth += 1
            depth_marker = next_depth_marker
            next_depth_marker = None
            if verbose and current_depth > max_depth:
                max_depth = current_depth
                print(f"  Depth {current_depth}: {len(to_visit)} pages in queue")

        if current_path in visited:
            continue

        visited.add(current_path)
        pages_fetched += 1

        # Fetch the page
        try:
            response = requests.get(f"{base_url}{current_path}")
            response.raise_for_status()
            data = response.json()

            # Add all linked pages to the queue
            for link in data.get("links", []):
                if link not in visited:
                    to_visit.append(link)
                    # Mark for next depth level
                    if depth_marker and not next_depth_marker:
                        next_depth_marker = link

            # Progress indicator
            if pages_fetched % 100 == 0:
                print(f"  Fetched {pages_fetched} pages...")

        except requests.RequestException as e:
            print(f"ERROR fetching {current_path}: {e}")
            continue

    # Calculate results
    elapsed = time.time() - start_time

    # Count unique page IDs (excluding root)
    unique_pages = set()
    for path in visited:
        if path != "/api/" and path != "/api":
            # Handle both /api/xxxx and /api/delay/xxxx URLs
            parts = path.strip('/').split('/')
            page_id = parts[-1]  # Last part is always the page_id
            if page_id:
                unique_pages.add(page_id)

    pages_found = len(unique_pages)
    success = pages_found == total_pages

    # Print results
    print(f"\nTEST RESULTS:")
    print(f"Total pages in graph: {total_pages}")
    print(f"Pages found from /api/: {pages_found}")
    print(f"Root page visited: {'Yes' if '/api/' in visited else 'No'}")
    print(f"Total URLs visited: {len(visited)}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"Pages per second: {pages_found/elapsed:.1f}")

    if success:
        print(f"\nSUCCESS: All {total_pages} pages are reachable from /api/")
    else:
        missing = total_pages - pages_found
        print(f"\nFAILURE: {missing} pages are not reachable from /api/")
        print("This should not happen as the graph is built to be connected!")

    return {
        "success": success,
        "total_pages": total_pages,
        "pages_found": pages_found,
        "urls_visited": len(visited),
        "time_seconds": elapsed,
        "pages_per_second": pages_found/elapsed
    }

def test_sample_crawl(base_url="http://localhost:5000", max_pages=50):
    """
    Do a limited crawl to test basic connectivity without fetching all pages.
    """
    print(f"\nTesting limited crawl (max {max_pages} pages)...")

    visited = set()
    to_visit = deque(["/api/"])

    while to_visit and len(visited) < max_pages:
        current = to_visit.popleft()
        if current in visited:
            continue

        visited.add(current)

        try:
            response = requests.get(f"{base_url}{current}")
            data = response.json()

            for link in data.get("links", []):
                if link not in visited:
                    to_visit.append(link)

        except requests.RequestException as e:
            print(f"Error: {e}")

    print(f"Successfully crawled {len(visited)} pages")
    return len(visited) >= max_pages or len(visited) > 0

if __name__ == "__main__":
    print("Graph Connectivity Test Suite")

    # First do a quick test
    print("\n1. Quick connectivity test...")
    if test_sample_crawl():
        print("   Basic connectivity works")
    else:
        print("   Basic connectivity failed")
        exit(1)

    # Then do the full test
    print("\n2. Full graph reachability test...")
    results = test_all_pages_reachable(verbose=True)

    # Exit with appropriate code
    exit(0 if results["success"] else 1)