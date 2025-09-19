# Tests

## Quick Start

Just run this command and everything will be handled for you:

```bash
./run_all_tests.sh
```

That's it! The script will:
- Check if Docker is installed and running
- Start the demo server automatically
- Run all tests
- Clean up when done

## What the Tests Do

### `test_graph_connectivity.py`
Verifies that all 1000 pages in the web graph are reachable by starting at `/api/` and following links. This is the foundational test that ensures the graph structure is correct for all the concurrency examples.

### `test_page_types.py`
Tests the different page types and their behaviors:
- Regular pages (500ms delay) vs delay pages (5000ms delay)
- Correct distribution (~90% regular, ~10% delay)
- Route validation and timing verification
- Link bias toward regular pages

### `test_concurrency_comparison.py`
Demonstrates performance differences between sequential and concurrent approaches with real I/O delays. Shows dramatic speedups possible with threading and asyncio.

**Test Results Show:**
- Total pages found vs expected (should be 1000/1000)
- Number of dead-ends (pages with no outgoing links)
- Crawling performance (pages per second)
- Full connectivity verification

## Requirements

- **Docker**: The script will check for you and provide installation instructions if needed
- **Python 3**: For running the test scripts (usually pre-installed on Mac/Linux)
- **curl**: For health checks (usually pre-installed)

## Manual Testing

If you want to run tests manually:

1. Start the server:
   ```bash
   cd .. && docker compose up --build -d
   ```

2. Run individual tests:
   ```bash
   python3 test_graph_connectivity.py
   python3 test_page_types.py
   python3 test_concurrency_comparison.py
   ```

3. Stop the server:
   ```bash
   cd .. && docker compose down
   ```

## For Developers

- Add new test files with the pattern `test_*.py`
- The test runner will automatically discover and run them
- Tests should return exit code 0 on success, non-zero on failure