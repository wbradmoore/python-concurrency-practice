# Python Concurrency Practice

This repository demonstrates different concurrency approaches in Python using a demo web server with 1000 interconnected pages.

## Concurrency Approaches

### 1. Threading (I/O-bound tasks)
Best for network requests and file operations.

```python
import threading
import requests

def fetch_page(url):
    response = requests.get(url)
    return response.json()

threads = []
for i in range(5):
    t = threading.Thread(target=fetch_page, args=(f"http://localhost:5000/api/page{i}",))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

### 2. Multiprocessing (CPU-bound tasks)
Best for computational work that can be parallelized.

```python
from multiprocessing import Pool

def cpu_work(data):
    # Expensive computation
    result = sum(i*i for i in range(data))
    return result

with Pool(4) as pool:
    results = pool.map(cpu_work, [100000, 200000, 300000, 400000])
```

### 3. Asyncio (High-concurrency I/O)
Best for many concurrent I/O operations.

```python
import asyncio
import aiohttp

async def fetch_page(session, url):
    async with session.get(url) as response:
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, f"http://localhost:5000/api/page{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)

asyncio.run(main())
```

## Demo Server

The server provides 5 page types for testing different scenarios:

- **Regular pages** (60%): 500ms delay
- **Delay pages** (10%): 5000ms delay
- **Failure pages** (10%): 90% error rate
- **CPU pages** (10%): Requires hash computation
- **Core pages** (10%): Parallel hash computation

### Starting the Server
```bash
docker compose up
```

### Page Types

**Regular Pages:**
```python
data = requests.get("http://localhost:5000/api/a1b2").json()
for link in data["links"]:
    # Process linked pages
```

**CPU Pages:**
```python
data = requests.get("http://localhost:5000/api/a1b2").json()
result = data["hashseed"]
for i in range(50000000):
    result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()
target_page = result[:4]
```

**Multi-Core Pages:**
```python
data = requests.get("http://localhost:5000/api/a1b2").json()
hashseeds = data["hashseed"]  # Dict with keys "1", "2", "3", "4"

# Solve in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = []
    for pos, seed in hashseeds.items():
        futures.append(executor.submit(solve_hash, seed))
    results = [f.result() for f in futures]
```

## Performance Testing

Compare approaches by crawling the graph:

```python
# Sequential (baseline)
def crawl_sequential(start_url, max_pages=50):
    visited = set()
    to_visit = [start_url]
    while to_visit and len(visited) < max_pages:
        current = to_visit.pop(0)
        if current in visited:
            continue
        visited.add(current)
        data = requests.get(current).json()
        to_visit.extend(data.get("links", []))
    return visited

# Threading
def crawl_threaded(start_url, max_pages=50, num_threads=5):
    # Use ThreadPoolExecutor with worker threads
    # Process pages concurrently

# Asyncio
async def crawl_async(start_url, max_pages=50, max_concurrent=10):
    # Use aiohttp with semaphore for concurrency control
    # Process many pages simultaneously
```

## When to Use Each

| Task Type | Best Approach | Why |
|-----------|---------------|-----|
| Web scraping | Asyncio or Threading | I/O-bound with waiting |
| File processing | Threading | I/O-bound |
| Math computation | Multiprocessing | CPU-bound |
| Image processing | Multiprocessing | CPU-bound |
| Database queries | Threading/Asyncio | I/O-bound |

## Key Libraries

- `threading` - Thread-based parallelism
- `multiprocessing` - Process-based parallelism
- `asyncio` - Asynchronous I/O
- `concurrent.futures` - High-level interface
- `aiohttp` - Async HTTP client
- `requests` - Synchronous HTTP client