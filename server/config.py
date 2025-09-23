#!/usr/bin/env python3
"""
Configuration file for the Web Graph Server

This file contains all the configurable parameters used throughout the server
and tests. Modify these values to experiment with different graph structures
and performance characteristics.
"""

# Graph Structure
TOTAL_PAGES = 100               # Total number of pages in the graph
PAGE_ID_LENGTH = 6              # Length of each page ID (e.g., "a1b2c3")
AVG_LINKS_PER_PAGE = 3          # Average number of outbound links per page

# Page Types and Distribution
DELAY_PAGE_PROBABILITY = 0.1    # Probability that a page is a delay page (10%)
FAILURE_PAGE_PROBABILITY = 0.1  # Probability that a page is a failure page (10%)
CPU_PAGE_PROBABILITY = 0.1      # Probability that a page is a CPU-bound page (10%)
CORE_PAGE_PROBABILITY = 0.1     # Probability that a page is a multi-core page (10%)
# Regular pages = 1 - DELAY_PAGE_PROBABILITY - FAILURE_PAGE_PROBABILITY - CPU_PAGE_PROBABILITY - CORE_PAGE_PROBABILITY = 60%

# Timing Configuration (in seconds)
REGULAR_PAGE_DELAY = 0.5        # Delay for regular pages (500ms)
DELAY_PAGE_DELAY = 5.0          # Delay for delay pages (5000ms)
ROOT_PAGE_DELAY = 0.0           # No delay for root page
FAILURE_PAGE_DELAY = 0.5        # Delay for failure pages (500ms)
CPU_PAGE_DELAY = 0.1            # Delay for CPU pages (100ms - minimal I/O)
CORE_PAGE_DELAY = 0.1           # Delay for multi-core pages (100ms - minimal I/O)

# Failure Configuration
FAILURE_PAGE_ERROR_RATE = 0.9   # Probability that failure pages return 500 error (90%)

# CPU Configuration
CPU_PAGE_ITERATIONS = 5000000  # Number of hash iterations for CPU work (5M iterations)

# Multi-Core Configuration
CORE_PAGE_ITERATIONS_PER_CHAR = 1250000  # Hash iterations per character (1.25M iterations)
CORE_PAGE_CHARS = 6             # Number of characters to compute in parallel
CORE_SEEDS_PER_CHAR = 2         # Number of seeds to generate per hex character


# Server Configuration
SERVER_HOST = '0.0.0.0'         # Server bind address
SERVER_PORT = 5000              # Server port
DEBUG_MODE = True               # Flask debug mode

# Error Messages
PAGE_NOT_FOUND_MESSAGE = "Page {page_id} not found"

def validate_config():
    """Basic validation"""
    total_probability = DELAY_PAGE_PROBABILITY + FAILURE_PAGE_PROBABILITY + CPU_PAGE_PROBABILITY + CORE_PAGE_PROBABILITY
    if total_probability > 1.0:
        raise ValueError(f"Page type probabilities sum to {total_probability:.2f}, must be <= 1.0")
    return True

if __name__ == "__main__":
    validate_config()
    print(f"Web Graph Server Config: {TOTAL_PAGES} pages, {int(DELAY_PAGE_PROBABILITY*100)}% delay, {int(FAILURE_PAGE_PROBABILITY*100)}% failure, {int(CPU_PAGE_PROBABILITY*100)}% CPU, {int(CORE_PAGE_PROBABILITY*100)}% core pages")