1. start with the root / page, which will be a regular page
2. ensure hashcache.json has enough entries:
    - Need at least TOTAL_PAGES cpu_seeds (so any page can be linked from CPU pages)
    - Need at least CORE_SEEDS_PER_CHAR seeds for each hex character (for core page linking)
3. use ALL page IDs from hashcache.json:
    - ALL page IDs come from cpu_seeds values in hashcache (these are the 6-char hex target IDs)
    - This ensures every page can be reached via CPU hashseed solving
4. assign page types to the hashcache page IDs:
    - Distribute types (cpu, core, regular, delay, failure) according to configured probabilities
5. build the graph by creating links:
    - Start with a tree structure where each new page has one incoming link
    - Add additional random edges until average links per page is reached
6. handle special link types:
    - CPU pages: store hashseeds (keys from hashcache) that hash to target page IDs
    - Core pages: store hexseeds (lists of 6 seeds from core_seeds) that hash to target page IDs
    - Regular/delay/failure pages: store direct page ID links 