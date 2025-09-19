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

**Important:** Each page has a 500ms delay (except the root `/api/`), simulating realistic network latency. This means:
- Sequential crawling: ~500 seconds (8.3 minutes) to fetch all pages
- With concurrency: Can be reduced to seconds!

This creates perfect scenarios for testing concurrency patterns:

- **I/O-bound tasks**: Fetching pages from the server
- **CPU-bound tasks**: Processing/analyzing the graph data
- **Mixed workloads**: Crawling + computing shortest paths, etc.

## Learning Materials

- **[CONCEPTS.md](CONCEPTS.md)** - Complete guide to Python concurrency concepts
- **Examples** - Practical implementations of each concurrency approach (coming soon)

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