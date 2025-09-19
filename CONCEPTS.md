# Python Concurrency Concepts: A Learning Guide

This document explains different types of concurrency in Python and the libraries used to implement them, ordered from simplest to most complex concepts.

## 1. Sequential Programming (Baseline)

Before diving into concurrency, it's important to understand sequential programming - where code executes one instruction at a time, in order.

```python
def process_data():
    data = fetch_data()      # Step 1
    result = transform(data) # Step 2
    save_result(result)      # Step 3
```

**When to use**: Simple scripts, learning, when operations are fast and don't benefit from concurrency.

## 2. Threading (Concurrent Execution)

Threading allows multiple threads to run concurrently within a single process. In Python, threads are limited by the Global Interpreter Lock (GIL) but are excellent for I/O-bound tasks.

### Built-in Libraries:
- **`threading`** - High-level threading interface
- **`_thread`** - Low-level threading (rarely used directly)

```python
import threading
import time

def worker(name):
    print(f"Worker {name} starting")
    time.sleep(2)  # Simulates I/O operation
    print(f"Worker {name} finished")

# Create and start threads
threads = []
for i in range(3):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

# Wait for all threads to complete
for t in threads:
    t.join()
```

**Best for**: I/O-bound tasks (file operations, network requests, database queries)
**Limitations**: GIL prevents true parallelism for CPU-bound tasks

## 3. Multiprocessing (Parallel Execution)

Multiprocessing creates separate processes, each with its own Python interpreter and memory space, bypassing the GIL limitation.

### Built-in Libraries:
- **`multiprocessing`** - Process-based parallelism
- **`concurrent.futures`** - High-level interface for threading and multiprocessing

```python
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

def cpu_intensive_task(n):
    # Simulate CPU-intensive work
    total = sum(i * i for i in range(n))
    return total

# Using multiprocessing
if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(cpu_intensive_task, 1000000) for _ in range(4)]
        results = [future.result() for future in futures]
```

**Best for**: CPU-bound tasks, true parallelism
**Overhead**: Higher memory usage and inter-process communication costs

## 4. Asynchronous Programming (Cooperative Concurrency)

Async programming uses cooperative multitasking where tasks voluntarily yield control, allowing other tasks to run. This is ideal for I/O-bound operations.

### Built-in Libraries:
- **`asyncio`** - Asynchronous I/O, event loop, coroutines
- **`async`/`await`** - Language syntax for async programming

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    urls = ['http://example.com'] * 5

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    return results

# Run the async function
asyncio.run(main())
```

**Best for**: I/O-bound tasks with many concurrent operations
**Advantages**: Low memory overhead, excellent for web scraping, API calls

## 5. Third-Party Concurrency Libraries

### 5.1 `concurrent.futures` (Built-in but Advanced)
High-level interface that abstracts threading and multiprocessing:

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

def io_task(url):
    # Simulate network request
    time.sleep(1)
    return f"Result from {url}"

# Thread pool for I/O-bound tasks
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(io_task, f"url_{i}") for i in range(10)]
    for future in as_completed(futures):
        print(future.result())
```

### 5.2 `trio` - Modern Async Library
A user-friendly async library with structured concurrency:

```python
import trio

async def child_task(name):
    print(f"Task {name} starting")
    await trio.sleep(1)
    print(f"Task {name} done")

async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(child_task, "A")
        nursery.start_soon(child_task, "B")
        nursery.start_soon(child_task, "C")

trio.run(main)
```

### 5.3 `joblib` - Simple Parallelism
Easy-to-use library for embarrassingly parallel problems:

```python
from joblib import Parallel, delayed

def square(x):
    return x * x

# Parallel execution
results = Parallel(n_jobs=4)(delayed(square)(i) for i in range(10))
```

### 5.4 `celery` - Distributed Task Queue
For distributed computing and background task processing:

```python
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def add(x, y):
    return x + y

# Usage
result = add.delay(4, 4)
print(result.get())  # Gets result when ready
```

## 6. Advanced Concurrency Patterns

### 6.1 Producer-Consumer with Queues

```python
import threading
import queue
import time

def producer(q):
    for i in range(5):
        item = f"item_{i}"
        q.put(item)
        print(f"Produced {item}")
        time.sleep(0.1)

def consumer(q):
    while True:
        item = q.get()
        if item is None:
            break
        print(f"Consumed {item}")
        q.task_done()

q = queue.Queue()
threading.Thread(target=producer, args=(q,)).start()
threading.Thread(target=consumer, args=(q,)).start()
```

### 6.2 Async Context Managers and Generators

```python
import asyncio

class AsyncResource:
    async def __aenter__(self):
        print("Acquiring resource")
        await asyncio.sleep(0.1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("Releasing resource")
        await asyncio.sleep(0.1)

async def use_resource():
    async with AsyncResource() as resource:
        print("Using resource")
        await asyncio.sleep(0.5)
```

## 7. Specialized Libraries for Specific Use Cases

### 7.1 `gevent` - Green Threads
Cooperative concurrency using monkey patching:

```python
import gevent
from gevent import monkey
monkey.patch_all()  # Makes standard library async

import requests

def fetch(url):
    response = requests.get(url)
    return response.status_code

urls = ['http://example.com'] * 5
jobs = [gevent.spawn(fetch, url) for url in urls]
gevent.joinall(jobs)
results = [job.value for job in jobs]
```

### 7.2 `dask` - Parallel Computing
For data science and large-scale computations:

```python
import dask.array as da

# Create large array
x = da.random.random((10000, 10000), chunks=(1000, 1000))

# Parallel computation
result = (x + x.T).mean().compute()
```

### 7.3 `ray` - Distributed Computing
For machine learning and distributed applications:

```python
import ray

@ray.remote
def compute_pi(num_samples):
    import random
    count = 0
    for _ in range(num_samples):
        x, y = random.random(), random.random()
        if x*x + y*y <= 1:
            count += 1
    return count

ray.init()
futures = [compute_pi.remote(1000000) for _ in range(4)]
results = ray.get(futures)
pi_estimate = 4 * sum(results) / (4 * 1000000)
```

## 8. When to Use Each Approach

| Use Case | Recommended Approach | Library |
|----------|---------------------|---------|
| I/O-bound, few concurrent operations | Threading | `threading` |
| I/O-bound, many concurrent operations | Async | `asyncio`, `trio` |
| CPU-bound, parallel processing | Multiprocessing | `multiprocessing`, `joblib` |
| Web scraping | Async or Threading | `asyncio` + `aiohttp` |
| Data processing | Multiprocessing | `dask`, `multiprocessing` |
| Background tasks | Task queues | `celery`, `rq` |
| Machine learning | Distributed computing | `ray`, `dask` |
| Simple parallel loops | High-level abstractions | `joblib`, `concurrent.futures` |

## 9. Common Pitfalls and Best Practices

### Threading Pitfalls:
- **Race conditions**: Use locks when sharing data
- **Deadlocks**: Always acquire locks in the same order
- **GIL limitations**: Threading won't speed up CPU-bound tasks

### Multiprocessing Pitfalls:
- **Pickling issues**: Objects must be serializable
- **Memory overhead**: Each process has its own memory space
- **Communication costs**: Inter-process communication is expensive

### Async Pitfalls:
- **Blocking calls**: Use async versions of I/O operations
- **CPU-bound tasks**: Will block the event loop
- **Learning curve**: Different mental model from synchronous code

### Best Practices:
1. **Profile first**: Measure before optimizing
2. **Start simple**: Use the simplest solution that works
3. **Handle errors**: Concurrent code makes error handling more complex
4. **Test thoroughly**: Race conditions are hard to reproduce
5. **Use appropriate abstractions**: Higher-level libraries often provide better APIs

## 10. Learning Path Recommendation

1. **Start with threading** for I/O-bound tasks
2. **Learn multiprocessing** for CPU-bound tasks
3. **Master asyncio** for high-concurrency I/O
4. **Explore concurrent.futures** for cleaner APIs
5. **Try specialized libraries** (trio, gevent) for specific needs
6. **Scale up** with distributed computing (ray, dask, celery)

This progression moves from simple concepts to increasingly sophisticated approaches, building a solid foundation for understanding Python concurrency.

---

## Practical Examples Using the Demo Server

The included demo server provides a perfect testing ground for all concurrency approaches. Start the server with:

```bash
docker-compose up --build
```

Then test different approaches against the web graph:

### Sequential Web Crawling (Baseline)

```python
import requests
import time

def crawl_sequential(base_url, start_page, max_pages=50):
    """Crawl pages sequentially - slowest approach"""
    visited = set()
    to_visit = [f"/api/{start_page}"]

    start_time = time.time()

    while to_visit and len(visited) < max_pages:
        current_path = to_visit.pop(0)
        if current_path in visited:
            continue

        visited.add(current_path)

        try:
            response = requests.get(f"{base_url}{current_path}")
            data = response.json()

            # Add linked pages to visit queue
            for link in data["links"]:
                if link not in visited:
                    to_visit.append(link)

        except requests.RequestException as e:
            print(f"Error fetching {current_path}: {e}")

    elapsed = time.time() - start_time
    print(f"Sequential: Visited {len(visited)} pages in {elapsed:.2f}s")
    return visited

# Usage
start_page = requests.get("http://localhost:5000/graph/random").json()["page_id"]
pages = crawl_sequential("http://localhost:5000", start_page)
```

### Threading for I/O-Bound Web Crawling

```python
import requests
import threading
import time
from queue import Queue

def crawl_with_threading(base_url, start_page, max_pages=50, num_threads=5):
    """Crawl using threading - good for I/O-bound web requests"""
    visited = set()
    visited_lock = threading.Lock()
    to_visit = Queue()
    to_visit.put(f"/api/{start_page}")

    start_time = time.time()

    def worker():
        while True:
            try:
                current_path = to_visit.get(timeout=1)
            except:
                break

            with visited_lock:
                if current_path in visited or len(visited) >= max_pages:
                    to_visit.task_done()
                    continue
                visited.add(current_path)

            try:
                response = requests.get(f"{base_url}{current_path}")
                data = response.json()

                # Add new links to queue
                for link in data["links"]:
                    with visited_lock:
                        if link not in visited:
                            to_visit.put(link)

            except requests.RequestException as e:
                print(f"Error fetching {current_path}: {e}")

            to_visit.task_done()

    # Start worker threads
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        threads.append(t)

    # Wait for completion
    to_visit.join()

    elapsed = time.time() - start_time
    print(f"Threading ({num_threads} threads): Visited {len(visited)} pages in {elapsed:.2f}s")
    return visited
```

### Async Web Crawling

```python
import asyncio
import aiohttp
import time

async def crawl_with_asyncio(base_url, start_page, max_pages=50, max_concurrent=10):
    """Crawl using asyncio - excellent for many concurrent I/O operations"""
    visited = set()
    to_visit = [f"/api/{start_page}"]
    semaphore = asyncio.Semaphore(max_concurrent)

    start_time = time.time()

    async def fetch_page(session, path):
        async with semaphore:
            if path in visited or len(visited) >= max_pages:
                return []

            visited.add(path)

            try:
                async with session.get(f"{base_url}{path}") as response:
                    data = await response.json()
                    return data["links"]
            except Exception as e:
                print(f"Error fetching {path}: {e}")
                return []

    async with aiohttp.ClientSession() as session:
        while to_visit and len(visited) < max_pages:
            # Process current batch
            tasks = [fetch_page(session, path) for path in to_visit[:max_concurrent]]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect new links
            new_links = []
            for result in results:
                if isinstance(result, list):
                    new_links.extend(result)

            # Update to_visit with unvisited links
            to_visit = [link for link in new_links if link not in visited]

    elapsed = time.time() - start_time
    print(f"Asyncio ({max_concurrent} concurrent): Visited {len(visited)} pages in {elapsed:.2f}s")
    return visited

# Usage
async def main():
    response = requests.get("http://localhost:5000/graph/random")
    start_page = response.json()["page_id"]
    pages = await crawl_with_asyncio("http://localhost:5000", start_page)

asyncio.run(main())
```

### Multiprocessing for CPU-Intensive Graph Analysis

```python
import requests
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import time

def analyze_page_content(page_data):
    """CPU-intensive analysis of page content"""
    page_id = page_data["page_id"]
    links = page_data["links"]

    # Simulate CPU-intensive work
    link_analysis = {}
    for link in links:
        link_id = link.split('/')[-1]
        # Simulate complex computation
        score = sum(ord(c) for c in link_id) * len(link_id)
        link_analysis[link_id] = score

    return {
        "page_id": page_id,
        "link_count": len(links),
        "total_score": sum(link_analysis.values()),
        "analysis": link_analysis
    }

def crawl_and_analyze_parallel(base_url, num_workers=4):
    """Fetch pages sequentially, then analyze in parallel"""
    # First, gather some pages
    sample = requests.get(f"{base_url}/graph/sample").json()
    pages_data = []

    print(f"Fetching {len(sample['page_ids'])} pages...")
    for page_id in sample["page_ids"][:20]:  # Limit for demo
        response = requests.get(f"{base_url}/api/{page_id}")
        pages_data.append(response.json())

    # Analyze pages in parallel
    print(f"Analyzing with {num_workers} processes...")
    start_time = time.time()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(analyze_page_content, pages_data))

    elapsed = time.time() - start_time
    total_score = sum(r["total_score"] for r in results)

    print(f"Multiprocessing ({num_workers} processes): Analyzed {len(results)} pages in {elapsed:.2f}s")
    print(f"Total analysis score: {total_score}")
    return results

# Usage
results = crawl_and_analyze_parallel("http://localhost:5000")
```

### Performance Comparison Script

```python
import time
import requests

def compare_approaches():
    """Compare different concurrency approaches"""
    base_url = "http://localhost:5000"

    # Get starting page
    start_response = requests.get(f"{base_url}/graph/random")
    start_page = start_response.json()["page_id"]

    print(f"Starting from page: {start_page}")
    print("=" * 50)

    # Test each approach
    approaches = [
        ("Sequential", lambda: crawl_sequential(base_url, start_page, 30)),
        ("Threading", lambda: crawl_with_threading(base_url, start_page, 30, 5)),
        ("Asyncio", lambda: asyncio.run(crawl_with_asyncio(base_url, start_page, 30, 10)))
    ]

    results = {}
    for name, func in approaches:
        print(f"\nTesting {name}...")
        try:
            start_time = time.time()
            pages = func()
            elapsed = time.time() - start_time
            results[name] = {"pages": len(pages), "time": elapsed}
            print(f"{name}: {len(pages)} pages in {elapsed:.2f}s")
        except Exception as e:
            print(f"{name} failed: {e}")
            results[name] = {"error": str(e)}

    print("\n" + "=" * 50)
    print("RESULTS SUMMARY:")
    for name, result in results.items():
        if "error" not in result:
            print(f"{name:12}: {result['pages']} pages in {result['time']:.2f}s "
                  f"({result['pages']/result['time']:.1f} pages/sec)")

# Run comparison
if __name__ == "__main__":
    compare_approaches()
```

### Testing Different Libraries

```python
# Using requests-futures for simple async-like behavior
from requests_futures.sessions import FuturesSession

def crawl_with_requests_futures(base_url, start_page, max_pages=50):
    """Using requests-futures for concurrent requests"""
    session = FuturesSession(max_workers=5)
    visited = set()
    to_visit = [f"/api/{start_page}"]

    start_time = time.time()

    while to_visit and len(visited) < max_pages:
        # Submit batch of requests
        futures = []
        current_batch = to_visit[:5]  # Process 5 at a time
        to_visit = to_visit[5:]

        for path in current_batch:
            if path not in visited:
                visited.add(path)
                future = session.get(f"{base_url}{path}")
                futures.append((path, future))

        # Collect results
        for path, future in futures:
            try:
                response = future.result(timeout=5)
                data = response.json()
                for link in data["links"]:
                    if link not in visited:
                        to_visit.append(link)
            except Exception as e:
                print(f"Error with {path}: {e}")

    elapsed = time.time() - start_time
    print(f"Requests-futures: Visited {len(visited)} pages in {elapsed:.2f}s")
    return visited
```

This hands-on approach lets you see the performance differences between each concurrency model using real I/O operations and CPU work.