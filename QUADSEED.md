# QUADSEED: Multi-Core Page Link Discovery

## Client Workflow (How to get a link from quadseeds)

1. Get core page with `quadseeds` list of 4-seed groups
2. Pick any 4-seed group [seed1, seed2, seed3, seed4]
3. Process all 4 seeds in parallel:
4.   Thread 1: hash seed1 12,500,000 times, take first char
5.   Thread 2: hash seed2 12,500,000 times, take first char
6.   Thread 3: hash seed3 12,500,000 times, take first char
7.   Thread 4: hash seed4 12,500,000 times, take first char
8. Combine 4 chars in order to form page_id
9. Navigate to /api/{page_id}

## Server Workflow (How server decides on quadseeds)

### Pre-computation Phase (Server Startup)
1. Calculate total character seeds needed: `(core_pages × AVG_LINKS_PER_PAGE × 4) × 1.1` buffer
2. Generate random 16-character seeds using `[a-z0-9]`
3. For each seed: hash it 12,500,000 times to get resulting character (first char of final hash)
4. Store seed→character mappings in `CORE_SEED_POOL`
5. Create core page IDs by combining groups of 4 characters from pool
6. Assign page types ensuring character-generated pages become core pages

### Runtime Assignment
7. When building graph links, core pages only get quadseeds for any valid targets
8. `get_core_seeds_for_targets()` finds 4 unused seeds per target page_id
9. For each target character, find seed that produces that character
10. Group 4 seeds into quadseed [seed1, seed2, seed3, seed4]
11. Mark used seeds to prevent duplicates across pages
12. Client must use parallel processing to discover targets

### Key Implementation Details
- **Iteration Count**: 12,500,000 iterations per character (~5 seconds total when parallel)
- **Character Mapping**: Each seed produces one hex character [0-9a-f]
- **Page ID Formation**: Combine 4 characters to form valid 4-char page IDs
- **Parallel Advantage**: Sequential processing takes 4× longer than parallel
- **Seed Distribution**: ~8.25 seeds available per character on average