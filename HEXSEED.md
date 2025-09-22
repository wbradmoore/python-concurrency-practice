# HEXSEED: Multi-Core Page Link Discovery

## Client Workflow (How to get a link from hexseeds)

1. Get core page with `multiseeds` list (contains 6-seed groups, kept as "multiseeds" for compatibility)
2. Pick any 6-seed group [seed1, seed2, seed3, seed4, seed5, seed6]
3. Process all 6 seeds in parallel:
4.   Thread 1: hash seed1 1,250,000 times, take first char
5.   Thread 2: hash seed2 1,250,000 times, take first char
6.   Thread 3: hash seed3 1,250,000 times, take first char
7.   Thread 4: hash seed4 1,250,000 times, take first char
8.   Thread 5: hash seed5 1,250,000 times, take first char
9.   Thread 6: hash seed6 1,250,000 times, take first char
10. Combine 6 chars in order to form page_id
11. Navigate to /api/{page_id}

## Server Workflow (How server decides on hexseeds)

### Pre-computation Phase (Server Startup)
1. Ensure at least CORE_SEEDS_PER_CHAR seeds for each hex character (0-9, a-f)
2. Generate random 16-character seeds using hex chars `[0-9a-f]`
3. For each seed: hash it 1,250,000 times to get resulting character (first char of final hash)
4. Store seed→character mappings in core_seeds dict (char -> list of seeds)
5. ALL page IDs come from hashcache cpu_seeds values (6-char hex)
6. Assign page types randomly across all hashcache page IDs

### Runtime Assignment
7. When building graph links, core pages can link to ANY page (all from hashcache)
8. `get_core_seeds_for_targets()` finds 6 unused seeds per target page_id
9. For each target character, find seed that produces that character
10. Group 6 seeds into hexseed list [seed1, seed2, seed3, seed4, seed5, seed6]
11. Mark used seeds to prevent duplicates across pages
12. Client must use parallel processing to discover targets efficiently

### Key Implementation Details
- **Iteration Count**: 1,250,000 iterations per character (CORE_PAGE_ITERATIONS_PER_CHAR)
- **Character Mapping**: Each seed produces one hex character [0-9a-f]
- **Page ID Formation**: Combine 6 characters to form valid 6-char hex page IDs
- **Parallel Advantage**: Sequential processing takes 6× longer than parallel
- **Seed Distribution**: Configurable CORE_SEEDS_PER_CHAR (default 2) per character
- **Compatibility**: Field still called "multiseeds" in API for backwards compatibility