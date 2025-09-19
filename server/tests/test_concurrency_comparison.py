#!/usr/bin/env python3
"""
Quick test to demonstrate the massive performance difference between
sequential and concurrent approaches due to the 500ms delay per page.
"""

import requests
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_TEST_PAGES, DEFAULT_THREAD_WORKERS, MAX_CONCURRENT_REQUESTS, SERVER_PORT

BASE_URL = f"http://localhost:{SERVER_PORT}"
TEST_PAGES = DEFAULT_TEST_PAGES

def test_sequential(num_pages=TEST_PAGES):
    """Sequential approach - very slow with 500ms delay per page"""
    print(f"\n1. Sequential approach (fetching {num_pages} pages)...")

    start_time = time.time()
    visited = set()
    to_visit = ["/api/"]

    while to_visit and len(visited) < num_pages:
        current = to_visit.pop(0)
        if current in visited:
            continue

        visited.add(current)

        response = requests.get(f"{BASE_URL}{current}")
        data = response.json()

        for link in data.get("links", []):
            if link not in visited:
                to_visit.append(link)

    elapsed = time.time() - start_time
    print(f"   Sequential: {len(visited)} pages in {elapsed:.2f} seconds")
    print(f"   Speed: {len(visited)/elapsed:.1f} pages/second")
    print(f"   Estimated time for 1000 pages: {1000 * elapsed / len(visited):.0f} seconds")
    return elapsed

def test_threading(num_pages=TEST_PAGES):
    """Threading approach - much faster for I/O-bound tasks"""
    print(f"\n2. Threading approach (fetching {num_pages} pages)...")

    start_time = time.time()
    visited = set()
    to_visit = ["/api/"]

    def fetch_page(path):
        try:
            response = requests.get(f"{BASE_URL}{path}")
            return path, response.json()
        except:
            return path, None

    with ThreadPoolExecutor(max_workers=DEFAULT_THREAD_WORKERS) as executor:
        while to_visit and len(visited) < num_pages:
            # Submit batch of requests
            batch = []
            for _ in range(min(DEFAULT_THREAD_WORKERS, num_pages - len(visited))):
                if to_visit:
                    path = to_visit.pop(0)
                    if path not in visited:
                        visited.add(path)
                        batch.append(path)

            if batch:
                futures = [executor.submit(fetch_page, path) for path in batch]
                for future in futures:
                    path, data = future.result()
                    if data:
                        for link in data.get("links", []):
                            if link not in visited and len(visited) < num_pages:
                                to_visit.append(link)

    elapsed = time.time() - start_time
    print(f"   Threading: {len(visited)} pages in {elapsed:.2f} seconds")
    print(f"   Speed: {len(visited)/elapsed:.1f} pages/second")
    print(f"   Speedup: {test_sequential.last_time/elapsed:.1f}x faster!")
    return elapsed

async def test_asyncio(num_pages=TEST_PAGES):
    """Async approach - excellent for many concurrent I/O operations"""
    print(f"\n3. Asyncio approach (fetching {num_pages} pages)...")

    start_time = time.time()
    visited = set()
    to_visit = ["/api/"]

    async with aiohttp.ClientSession() as session:
        while to_visit and len(visited) < num_pages:
            # Process batch concurrently
            batch = []
            for _ in range(min(DEFAULT_THREAD_WORKERS, num_pages - len(visited))):
                if to_visit:
                    path = to_visit.pop(0)
                    if path not in visited:
                        visited.add(path)
                        batch.append(path)

            if batch:
                tasks = []
                for path in batch:
                    async def fetch(p):
                        try:
                            async with session.get(f"{BASE_URL}{p}") as response:
                                return p, await response.json()
                        except:
                            return p, None
                    tasks.append(fetch(path))

                results = await asyncio.gather(*tasks)
                for path, data in results:
                    if data:
                        for link in data.get("links", []):
                            if link not in visited and len(visited) < num_pages:
                                to_visit.append(link)

    elapsed = time.time() - start_time
    print(f"   Asyncio: {len(visited)} pages in {elapsed:.2f} seconds")
    print(f"   Speed: {len(visited)/elapsed:.1f} pages/second")
    print(f"   Speedup: {test_sequential.last_time/elapsed:.1f}x faster!")
    return elapsed

def main():
    print("CONCURRENCY PERFORMANCE COMPARISON")
    print("Testing with mixed page types:")
    print("- Regular pages: 500ms delay (~90%)")
    print("- Delay pages: 5000ms delay (~10%)")

    # Run sequential first to get baseline
    seq_time = test_sequential()
    test_sequential.last_time = seq_time

    # Run concurrent approaches
    thread_time = test_threading()

    # Run async
    async_time = asyncio.run(test_asyncio())

    # Summary
    print("\nSUMMARY")
    print(f"Sequential: {seq_time:.2f}s (baseline)")
    print(f"Threading:  {thread_time:.2f}s ({seq_time/thread_time:.1f}x speedup)")
    print(f"Asyncio:    {async_time:.2f}s ({seq_time/async_time:.1f}x speedup)")

    print("\nKey Insight:")
    print(f"With {TEST_PAGES} pages at 500ms each:")
    print(f"  - Sequential takes ~{TEST_PAGES * 0.5:.0f} seconds (one at a time)")
    print(f"  - Concurrent takes ~{max(thread_time, async_time):.1f} seconds (many in parallel)")
    print(f"  - That's a {seq_time/min(thread_time, async_time):.0f}x speedup!")

if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=1)
    except:
        print("Server is not running! Start it with: docker compose up")
        exit(1)

    main()