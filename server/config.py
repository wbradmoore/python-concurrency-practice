#!/usr/bin/env python3
"""
Configuration file for the Web Graph Server

This file contains all the configurable parameters used throughout the server
and tests. Modify these values to experiment with different graph structures
and performance characteristics.
"""

# Graph Structure
TOTAL_PAGES = 1000              # Total number of pages in the graph
PAGE_ID_LENGTH = 4              # Length of each page ID (e.g., "a1b2")
ADDITIONAL_EDGES = 2000         # Random edges added after tree construction
                               # This creates cycles and increases connectivity

# Page Types and Distribution
DELAY_PAGE_PROBABILITY = 0.1    # Probability that a page is a delay page (10%)
REGULAR_PAGE_BIAS = 0.9         # Probability links go to regular pages (90%)

# Timing Configuration (in seconds)
REGULAR_PAGE_DELAY = 0.5        # Delay for regular pages (500ms)
DELAY_PAGE_DELAY = 5.0          # Delay for delay pages (5000ms)
ROOT_PAGE_DELAY = 0.0           # No delay for root page

# Network Simulation
MIN_NETWORK_LATENCY = 0.01      # Minimum simulated network latency (10ms)
MAX_NETWORK_LATENCY = 0.05      # Maximum simulated network latency (50ms)

# Test Configuration
DEFAULT_TEST_PAGES = 20         # Default number of pages for performance tests
MAX_SAMPLE_SIZE = 20            # Maximum sample size for /graph/sample endpoint
MAX_SEARCH_RESULTS = 100        # Maximum pages returned by /graph/search
CONNECTIVITY_TEST_TIMEOUT = 120 # Timeout for connectivity tests (seconds)

# Threading and Concurrency Limits
DEFAULT_THREAD_WORKERS = 10     # Default number of threads for concurrent tests
MAX_CONCURRENT_REQUESTS = 10    # Default concurrency limit for async tests

# Server Configuration
SERVER_HOST = '0.0.0.0'         # Server bind address
SERVER_PORT = 5000              # Server port
DEBUG_MODE = True               # Flask debug mode

# Graph Generation Limits
MAX_ATTEMPTS_EDGE_GENERATION = 10000  # Prevent infinite loops during graph generation
MAX_PAGES_SAMPLE_ENDPOINT = 50000     # Safety limit for /dataset endpoint
MAX_DELAY_ENDPOINT = 10               # Maximum delay for /slow endpoint (seconds)

# Statistics Display
MAX_DEAD_ENDS_SHOWN = 10        # Number of dead-end examples to show in stats
MAX_TOP_PAGES_SHOWN = 5         # Number of top-linked pages to show in stats

# URL Patterns
ROOT_PATH = "/api/"
REGULAR_PAGE_PATH_TEMPLATE = "/api/{page_id}"
DELAY_PAGE_PATH_TEMPLATE = "/api/delay/{page_id}"

# Error Messages
PAGE_NOT_FOUND_MESSAGE = "Page {page_id} not found"
WRONG_PAGE_TYPE_MESSAGE = "Page {page_id} is not a {expected_type} page"

# Performance Test Configuration
PERFORMANCE_TEST_CONFIG = {
    "sequential": {
        "name": "Sequential",
        "description": "One request at a time"
    },
    "threading": {
        "name": "Threading",
        "description": "Multiple threads handling I/O concurrently",
        "workers": DEFAULT_THREAD_WORKERS
    },
    "asyncio": {
        "name": "Asyncio",
        "description": "Async/await with event loop",
        "concurrent_limit": MAX_CONCURRENT_REQUESTS
    }
}

# Validation ranges for configuration
CONFIG_VALIDATION = {
    "TOTAL_PAGES": {"min": 10, "max": 100000},
    "PAGE_ID_LENGTH": {"min": 2, "max": 8},
    "DELAY_PAGE_PROBABILITY": {"min": 0.0, "max": 1.0},
    "REGULAR_PAGE_BIAS": {"min": 0.0, "max": 1.0},
    "REGULAR_PAGE_DELAY": {"min": 0.0, "max": 10.0},
    "DELAY_PAGE_DELAY": {"min": 0.0, "max": 30.0}
}

def validate_config():
    """Validate configuration values are within acceptable ranges"""
    import sys

    errors = []

    for param, limits in CONFIG_VALIDATION.items():
        value = globals().get(param)
        if value is None:
            errors.append(f"Missing configuration parameter: {param}")
            continue

        if "min" in limits and value < limits["min"]:
            errors.append(f"{param} = {value} is below minimum {limits['min']}")
        if "max" in limits and value > limits["max"]:
            errors.append(f"{param} = {value} is above maximum {limits['max']}")

    # Logical validations
    if DELAY_PAGE_PROBABILITY + (1 - DELAY_PAGE_PROBABILITY) != 1.0:
        errors.append("Page type probabilities must sum to 1.0")

    if REGULAR_PAGE_BIAS > 1.0 or REGULAR_PAGE_BIAS < 0.0:
        errors.append("REGULAR_PAGE_BIAS must be between 0.0 and 1.0")

    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)

    return True

def get_page_type_distribution():
    """Calculate expected page type counts"""
    regular_count = int(TOTAL_PAGES * (1 - DELAY_PAGE_PROBABILITY))
    delay_count = TOTAL_PAGES - regular_count

    return {
        "regular": regular_count,
        "delay": delay_count,
        "total": TOTAL_PAGES
    }

def get_timing_info():
    """Get timing information for documentation"""
    return {
        "regular_page": {
            "delay_ms": int(REGULAR_PAGE_DELAY * 1000),
            "delay_seconds": REGULAR_PAGE_DELAY
        },
        "delay_page": {
            "delay_ms": int(DELAY_PAGE_DELAY * 1000),
            "delay_seconds": DELAY_PAGE_DELAY
        },
        "root_page": {
            "delay_ms": int(ROOT_PAGE_DELAY * 1000),
            "delay_seconds": ROOT_PAGE_DELAY
        }
    }

if __name__ == "__main__":
    # Validate configuration when run directly
    validate_config()

    # Print configuration summary
    print("Web Graph Server Configuration")

    dist = get_page_type_distribution()
    timing = get_timing_info()

    print(f"Graph Structure:")
    print(f"  Total pages: {TOTAL_PAGES}")
    print(f"  Additional edges: {ADDITIONAL_EDGES}")
    print(f"  Regular pages: {dist['regular']} ({(1-DELAY_PAGE_PROBABILITY)*100:.1f}%)")
    print(f"  Delay pages: {dist['delay']} ({DELAY_PAGE_PROBABILITY*100:.1f}%)")

    print(f"\nTiming Configuration:")
    print(f"  Regular pages: {timing['regular_page']['delay_ms']}ms")
    print(f"  Delay pages: {timing['delay_page']['delay_ms']}ms")
    print(f"  Root page: {timing['root_page']['delay_ms']}ms")

    print(f"\nLink Distribution:")
    print(f"  Links to regular pages: {REGULAR_PAGE_BIAS*100:.1f}%")
    print(f"  Links to delay pages: {(1-REGULAR_PAGE_BIAS)*100:.1f}%")

    print(f"\nServer Settings:")
    print(f"  Host: {SERVER_HOST}")
    print(f"  Port: {SERVER_PORT}")
    print(f"  Debug: {DEBUG_MODE}")

    print("\nConfiguration is valid!")