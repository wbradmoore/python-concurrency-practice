# Python Concurrency Practice

A hands-on learning repository for understanding different concurrency patterns in Python.

## Quick Start

1. **Start the demo server:**
   ```bash
   cd server
   docker compose up --build
   ```

2. **Verify it's running:**
   ```bash
   curl http://localhost:5000/health
   ```

3. **Run all tests:**
   ```bash
   cd server/tests
   ./run_all_tests.sh
   ```

4. **Explore the graph:**
   ```bash
   # Get API documentation
   curl http://localhost:5000/

   # Get a random starting page
   curl http://localhost:5000/graph/random

   # Visit a specific page
   curl http://localhost:5000/api/a1b2
   ```

## Demo Server

The server hosts a graph of 1000 interconnected web pages at URLs like `/api/a1b2` where each page contains links to other pages (average ~3 links per page, but some have none creating dead-ends).

**Page Types:** The server hosts 5 different page types with realistic delays and behaviors:
- **Regular pages (60%)**: 500ms delay - standard I/O-bound pages
- **Delay pages (10%)**: 5000ms delay - high-latency I/O operations
- **Failure pages (10%)**: 500ms delay + 90% error rate - unreliable services
- **CPU pages (10%)**: 100ms delay + CPU work required - single-core CPU load
- **Multi-core pages (10%)**: 100ms delay + parallel CPU work - multi-core CPU load

This creates perfect scenarios for testing concurrency patterns:

- **I/O-bound tasks**: Fetching regular and delay pages from the server
- **CPU-bound tasks**: Solving challenges from CPU pages (single-core work)
- **Multi-core tasks**: Solving challenges from multi-core pages (parallel work)
- **Error handling**: Managing failures from unreliable failure pages
- **Mixed workloads**: Crawling + CPU work + parallel processing + error recovery

## How It Works

The server provides a web graph where each page type demonstrates different concurrency challenges:

### 1. Regular Pages (60% - Standard I/O)
Simple pages with 500ms delay. Perfect for testing basic I/O concurrency.

```python
data = requests.get("http://localhost:5000/api/a1b2").json()
new_urls = [f"http://localhost:5000/api/{page_id}" for page_id in data["links"]]
```

### 2. Delay Pages (10% - High Latency I/O)
High-latency pages with 5000ms delay. Shows benefits of concurrent I/O. Similar code as above works.

### 3. Failure Pages (10% - Error Handling)
Unreliable pages with 90% failure rate. Requires retry logic and error handling.

```python
for attempt in range(5):
    try:
        data = requests.get("http://localhost:5000/api/m9n0").json()
        new_urls = [f"http://localhost:5000/api/{page_id}" for page_id in data["links"]]
        break
    except:
        time.sleep(0.1)
```

### 4. CPU Pages (10% - Single-Core Work)
Pages requiring CPU-intensive work to extract links. Good for testing CPU vs I/O concurrency.

```python
data = requests.get("http://localhost:5000/api/p3q4").json()
result = data["hashseeds"][0]  # Get first hashseed
for _ in range(5000000):
    result = hashlib.md5(result.encode()).hexdigest()
target_page_id = result[:6]  # First 6 characters of final hash
new_urls = [f"http://localhost:5000/api/{target_page_id}"]
```

### 5. Multi-Core Pages (10% - Parallel Work)
Pages requiring parallel CPU work. Shows benefits of multi-core processing.

```python
data = requests.get("http://localhost:5000/api/r5s6").json()
target_chars = []
for seed in data["quadseeds"][0]:  # Get first hexseed group (still called quadseeds for compatibility)
    result = seed
    for _ in range(1250000):
        result = hashlib.md5(result.encode()).hexdigest()
    target_chars.append(result[0])  # First character of final hash
target_page_id = "".join(target_chars)
new_urls = [f"http://localhost:5000/api/{target_page_id}"]
```

## Performance Comparison

Sequential crawling of 20 mixed pages:
- **Regular pages**: 20 × 500ms = ~10 seconds
- **Delay pages**: 2 × 5000ms = ~10 seconds
- **CPU pages**: 2 × 5000ms = ~10 seconds
- **Multi-core pages**: 2 × 20000ms = ~40 seconds (sequential)
- **Total**: ~70 seconds

With proper concurrency:
- **I/O concurrency** (threading/asyncio): ~5-10 seconds (4-7x speedup)
- **CPU concurrency** (multiprocessing): Depends on cores available
- **Multi-core optimization**: ~5 seconds instead of ~40 seconds (8x speedup)

## Learning Materials

- **[CONCEPTS.md](CONCEPTS.md)** - Complete guide to Python concurrency concepts
- **Examples** - See code samples above for each page type

## Project Structure

```
├── server/                    # Demo web server
│   ├── demo_server.py        # Flask server with extensible page types
│   ├── Dockerfile            # Container setup
│   ├── docker-compose.yml    # Service orchestration
│   └── tests/                # Server tests
│       ├── run_all_tests.sh  # Complete test runner
│       ├── test_*.py         # Individual test files
│       └── README.md         # Testing documentation
├── CONCEPTS.md               # Complete concurrency learning guide
└── README.md                 # This file
```

## Use Cases for Testing

1. **Web Crawling**: Fetch all pages starting from a random page
2. **Graph Analysis**: Find shortest paths, count reachable nodes
3. **Data Processing**: Extract patterns from the link structure
4. **Performance Comparison**: Time different concurrency approaches