# HASHSEED: CPU Page Link Discovery

## Client Workflow (How to get a link from a hashseed)

1. Get CPU page with `hashseeds` list
2. Pick any seed from the list
3. Set result = seed
4. Loop 5,000,000 times: result = md5(result).hexdigest()
5. Extract first 6 chars of final result as page_id
6. Navigate to /api/{page_id}

## Server Workflow (How server decides on hashseeds)

### Pre-computation Phase (Server Startup)
1. Calculate total hashseeds needed: `(CPU_pages × AVG_LINKS_PER_PAGE) × 1.1` buffer
2. Generate random 16-character seeds using hex chars `[0-9a-f]`
3. For each seed: hash it 5,000,000 times to get resulting page_id
4. Store seed→page_id mappings in `CPU_SEED_POOL`
5. Use page_ids from seed pool as actual graph page IDs
6. Assign page types ensuring seed-generated pages become CPU pages

### Runtime Assignment
7. When building graph links, CPU pages only get hashseeds for targets in pool
8. `get_cpu_seeds_for_targets()` finds unused seeds that hash to link targets
9. Mark used seeds to prevent duplicates across pages
10. Client must perform CPU work to discover actual valid page_ids

### Key Implementation Details
- **Iteration Count**: 5,000,000 iterations (configurable CPU work)
- **Page ID Generation**: ALL page IDs come from hashcache cpu_seeds values (6-char hex)
- **Type Assignment**: Pages from seed pools are guaranteed to get correct types
- **Link Filtering**: CPU pages only provide seeds for targets they can actually produce