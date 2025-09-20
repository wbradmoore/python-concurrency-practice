#!/usr/bin/env python3

import random
import string
import time
import hashlib

from config import *
from flask import Flask, abort, jsonify

# Validate configuration on startup
validate_config()

app = Flask(__name__)

# Page Type Configuration
PAGE_TYPES = {
    "regular": {"delay": REGULAR_PAGE_DELAY},
    "delay": {"delay": DELAY_PAGE_DELAY},
    "failure": {"delay": FAILURE_PAGE_DELAY},
    "cpu": {"delay": CPU_PAGE_DELAY},
    "core": {"delay": CORE_PAGE_DELAY}
}

# Pre-computed seed pools
CPU_SEED_POOL = {}  # seed -> page_id mapping
CORE_SEED_POOL = {}  # seed -> character mapping
USED_CPU_SEEDS = set()
USED_CORE_SEEDS = set()

def calculate_needed_seeds():
    """Calculate how many seeds we need for CPU and core pages"""
    cpu_pages = int(TOTAL_PAGES * CPU_PAGE_PROBABILITY)
    core_pages = int(TOTAL_PAGES * CORE_PAGE_PROBABILITY)

    # Each page has average links
    cpu_seeds_needed = cpu_pages * AVG_LINKS_PER_PAGE
    core_seeds_needed = core_pages * AVG_LINKS_PER_PAGE * CORE_PAGE_CHARS

    # Add 10% buffer
    cpu_seeds_needed = int(cpu_seeds_needed * 1.1)
    core_seeds_needed = int(core_seeds_needed * 1.1)

    return cpu_seeds_needed, core_seeds_needed

def generate_random_seed():
    """Generate a random seed string"""
    import string
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=16))

def compute_cpu_seed_pools():
    """Pre-compute CPU seed pools by generating random seeds and hashing them"""
    global CPU_SEED_POOL

    cpu_needed, _ = calculate_needed_seeds()
    print(f"Computing {cpu_needed} CPU seeds...")

    seeds_generated = 0
    attempts = 0
    max_attempts = cpu_needed * 10  # Limit attempts to avoid infinite loops

    while seeds_generated < cpu_needed and attempts < max_attempts:
        attempts += 1
        seed = generate_random_seed()

        # Hash the seed to see what page ID it produces
        result = seed
        for i in range(CPU_PAGE_ITERATIONS):
            result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()

        page_id = result[:PAGE_ID_LENGTH]

        # Keep this seed->page_id mapping if we haven't used this seed before
        if seed not in CPU_SEED_POOL:
            CPU_SEED_POOL[seed] = page_id
            seeds_generated += 1

        if attempts % 100 == 0:
            print(f"  Generated {seeds_generated}/{cpu_needed} CPU seeds ({attempts} attempts)")

    print(f"Generated {seeds_generated} CPU seeds in {attempts} attempts")

def compute_core_seed_pools():
    """Pre-compute core seed pools by generating random seeds and hashing them"""
    global CORE_SEED_POOL

    _, core_needed = calculate_needed_seeds()
    print(f"Computing {core_needed} core character seeds...")

    seeds_generated = 0
    attempts = 0
    max_attempts = core_needed * 10

    while seeds_generated < core_needed and attempts < max_attempts:
        attempts += 1
        seed = generate_random_seed()

        # Hash the seed 12.5M times
        result = seed
        for i in range(CORE_PAGE_ITERATIONS_PER_CHAR):
            result = hashlib.md5(f"{result}_{i}".encode()).hexdigest()

        char = result[0]  # First character

        # Store seed -> character mapping
        if seed not in CORE_SEED_POOL:
            CORE_SEED_POOL[seed] = char
            seeds_generated += 1

        if attempts % 100 == 0:
            print(f"  Generated {seeds_generated}/{core_needed} core seeds ({attempts} attempts)")

    print(f"Generated {seeds_generated} core character seeds in {attempts} attempts")

def get_cpu_seeds_for_targets(target_page_ids):
    """Get CPU seeds that hash to the target page IDs"""
    seeds = []
    available_targets = set(CPU_SEED_POOL.values())

    for target in target_page_ids:
        # Only provide seeds for targets we actually have seeds for
        if target in available_targets:
            # Find an unused seed that maps to this target
            for seed, page_id in CPU_SEED_POOL.items():
                if page_id == target and seed not in USED_CPU_SEEDS:
                    seeds.append(seed)
                    USED_CPU_SEEDS.add(seed)
                    break
    return seeds

def get_core_seeds_for_targets(target_page_ids):
    """Get core seed groups (4 seeds each) that hash to the target page IDs"""
    seed_groups = []

    for target in target_page_ids:
        if len(target) < 4:
            target = target.ljust(4, '0')

        # Find 4 seeds that produce the 4 characters of this target
        quad = []
        for char in target[:4]:
            found_seed = False
            for seed, seed_char in CORE_SEED_POOL.items():
                if seed_char == char and seed not in USED_CORE_SEEDS:
                    quad.append(seed)
                    USED_CORE_SEEDS.add(seed)
                    found_seed = True
                    break

            if not found_seed:
                # Couldn't find a seed for this character, abandon this target
                break

        if len(quad) == 4:
            seed_groups.append(quad)

    return seed_groups

def generate_page_ids(count=TOTAL_PAGES):
    """Generate unique page IDs with configurable length"""
    chars = string.ascii_lowercase + string.digits
    page_ids = set()

    while len(page_ids) < count:
        page_id = ''.join(random.choices(chars, k=PAGE_ID_LENGTH))
        page_ids.add(page_id)

    return list(page_ids)

def assign_page_types(page_ids):
    """Assign page types to page IDs with exact percentages"""
    global CPU_SEED_POOL, CORE_SEED_POOL

    # Get page IDs that came from seed pools
    cpu_page_ids_from_seeds = set(CPU_SEED_POOL.values())
    core_page_ids_from_seeds = set()

    # For core, we need to reconstruct which page IDs came from core seeds
    core_chars = list(CORE_SEED_POOL.values())
    for i in range(0, len(core_chars) - 3, 4):
        page_id = ''.join(core_chars[i:i+4])
        core_page_ids_from_seeds.add(page_id)

    # Calculate exact counts for each page type
    core_count = int(TOTAL_PAGES * CORE_PAGE_PROBABILITY)
    cpu_count = int(TOTAL_PAGES * CPU_PAGE_PROBABILITY)
    failure_count = int(TOTAL_PAGES * FAILURE_PAGE_PROBABILITY)
    delay_count = int(TOTAL_PAGES * DELAY_PAGE_PROBABILITY)
    regular_count = TOTAL_PAGES - core_count - cpu_count - failure_count - delay_count

    # Assign types to page IDs
    pages = []
    assigned_cpu = 0
    assigned_core = 0
    assigned_failure = 0
    assigned_delay = 0

    for page_id in page_ids:
        # Assign page types based on seed pools first
        if page_id in cpu_page_ids_from_seeds and assigned_cpu < cpu_count:
            page_type = "cpu"
            assigned_cpu += 1
        elif page_id in core_page_ids_from_seeds and assigned_core < core_count:
            page_type = "core"
            assigned_core += 1
        # For remaining pages, assign other types randomly
        elif assigned_failure < failure_count:
            page_type = "failure"
            assigned_failure += 1
        elif assigned_delay < delay_count:
            page_type = "delay"
            assigned_delay += 1
        else:
            page_type = "regular"

        pages.append({
            "page_id": page_id,
            "type": page_type,
            "url": f"/api/{page_id}"
        })

    return pages

# Generate the graph structure
print("Pre-computing hashseed pools...")
compute_cpu_seed_pools()
compute_core_seed_pools()

print("Collecting page IDs from seed pools...")
# Get page IDs from CPU seed pool
cpu_page_ids = list(CPU_SEED_POOL.values())

# For core seeds, we need to generate page IDs by combining 4 characters
# Group core seeds by character and create valid page IDs
core_chars = list(CORE_SEED_POOL.values())
core_page_ids = []
# Create page IDs from groups of 4 characters
for i in range(0, len(core_chars) - 3, 4):
    page_id = ''.join(core_chars[i:i+4])
    core_page_ids.append(page_id)

# Generate additional random page IDs to reach TOTAL_PAGES
existing_page_ids = set(cpu_page_ids + core_page_ids)
print(f"Generated {len(cpu_page_ids)} CPU page IDs and {len(core_page_ids)} core page IDs")

# Fill remaining pages with random IDs
additional_needed = TOTAL_PAGES - len(existing_page_ids)
if additional_needed > 0:
    print(f"Generating {additional_needed} additional random page IDs...")
    additional_ids = generate_page_ids(additional_needed)
    # Make sure they don't conflict with seed-generated IDs
    while any(pid in existing_page_ids for pid in additional_ids):
        additional_ids = generate_page_ids(additional_needed)
    PAGE_IDS = list(existing_page_ids) + additional_ids
else:
    PAGE_IDS = list(existing_page_ids)

print("Assigning page types...")
PAGES = assign_page_types(PAGE_IDS)
GRAPH = {}


def get_page_by_id(page_id):
    """Find a page object by its ID"""
    for page in PAGES:
        if page["page_id"] == page_id:
            return page
    return None

def get_regular_pages():
    """Get all regular (non-delay) pages"""
    return [p for p in PAGES if p["type"] == "regular"]

def choose_target_page():
    """Choose a target page randomly from all pages"""
    return random.choice(PAGES)

def build_graph():
    """Build an organic connected graph starting from a root page"""
    global GRAPH

    # Initialize all pages with empty link lists
    for page in PAGES:
        page_id = page["page_id"]
        GRAPH[page_id] = {
            "page_id": page_id,
            "page_type": page["type"],
            "links": [],
            "link_count": 0,
            "generated_at": time.time()
        }

    # Start with first page as root, build a tree by adding pages one at a time
    pages_in_tree = [PAGES[0]]  # Start with first page
    pages_not_added = PAGES[1:]  # All other pages

    # Build tree structure: add each new page with one link from an existing page
    while pages_not_added:
        # Pick a random page already in the tree to link from
        source_page = random.choice(pages_in_tree)
        # Pick a new page to add
        new_page = pages_not_added.pop(0)

        # Add link from source to new page
        source_id = source_page["page_id"]
        GRAPH[source_id]["links"].append(new_page["url"])

        # Add new page to tree
        pages_in_tree.append(new_page)

    # Now we have a tree with (TOTAL_PAGES - 1) edges
    # Add more edges to reach target average links per page
    target_total_edges = TOTAL_PAGES * AVG_LINKS_PER_PAGE
    additional_edges_needed = target_total_edges - (TOTAL_PAGES - 1)
    edges_added = 0
    attempts = 0

    while edges_added < additional_edges_needed and attempts < MAX_ATTEMPTS_EDGE_GENERATION:
        attempts += 1
        source_page = random.choice(PAGES)
        target_page = choose_target_page()  # Random selection from all page types

        source_id = source_page["page_id"]
        target_url = target_page["url"]

        # Don't add self-loops or duplicate edges
        if source_id != target_page["page_id"] and target_url not in GRAPH[source_id]["links"]:
            GRAPH[source_id]["links"].append(target_url)
            edges_added += 1

    # Update link counts
    for page in PAGES:
        page_id = page["page_id"]
        GRAPH[page_id]["link_count"] = len(GRAPH[page_id]["links"])

# Build the graph on startup
build_graph()

@app.route('/')
def index():
    """API documentation and graph info"""
    return jsonify({
        "name": "Web Graph Server",
        "description": f"A graph of {TOTAL_PAGES} interconnected web pages for concurrency testing",
        "total_pages": len(PAGE_IDS),
        "links": [PAGES[0]["url"]]
    })

@app.route('/api/')
@app.route('/api')
def get_root_page():
    """Get the root page - entry point to the graph"""
    # The root page links to the first page in our graph
    root_data = {
        "page_id": "root",
        "page_type": "root",
        "links": [PAGES[0]["page_id"]],
        "link_count": 1,
        "message": "This is the root page. Start crawling from here.",
        "total_pages_in_graph": len(PAGES),
        "page_type_distribution": {
            "regular": len([p for p in PAGES if p["type"] == "regular"]),
            "delay": len([p for p in PAGES if p["type"] == "delay"]),
            "failure": len([p for p in PAGES if p["type"] == "failure"]),
            "cpu": len([p for p in PAGES if p["type"] == "cpu"]),
            "core": len([p for p in PAGES if p["type"] == "core"])
        },
        "requested_at": time.time(),
        "url": "/api/"
    }
    return jsonify(root_data)

@app.route('/api/<page_id>')
def get_page(page_id):
    """Get a page with its links"""
    return serve_page(page_id)

def serve_page(page_id):
    """Generic page serving function"""
    if page_id not in GRAPH:
        abort(404, description=PAGE_NOT_FOUND_MESSAGE.format(page_id=page_id))

    page_obj = get_page_by_id(page_id)
    if not page_obj:
        abort(404, description=PAGE_NOT_FOUND_MESSAGE.format(page_id=page_id))

    page_type = page_obj["type"]

    # Apply the appropriate delay for this page type
    delay = PAGE_TYPES[page_obj["type"]]["delay"]
    time.sleep(delay)

    # Check if this is a failure page and should fail
    if page_type == "failure" and random.random() < FAILURE_PAGE_ERROR_RATE:
        abort(500, description=f"Failure page {page_id} failed (simulated error)")

    page_data = GRAPH[page_id].copy()
    page_data["requested_at"] = time.time()
    page_data["url"] = f"/api/{page_id}"
    page_data["delay_ms"] = int(delay * 1000)

    # Convert links to just page IDs (not full URLs)
    link_page_ids = []
    for link in page_data["links"]:
        # Extract target page ID from link URL
        target_page_id = link.split('/')[-1]
        link_page_ids.append(target_page_id)

    # For CPU pages, use hashseeds list instead of links
    if page_type == "cpu":
        if link_page_ids:
            # Get pre-computed seeds for these targets
            seeds = get_cpu_seeds_for_targets(link_page_ids)
            page_data["hashseeds"] = seeds
        else:
            # No links, empty list
            page_data["hashseeds"] = []
        del page_data["links"]  # Remove links field

    # For multi-core pages, use quadseeds list of lists instead of links
    elif page_type == "core":
        if link_page_ids:
            # Get pre-computed seed groups for these targets
            seed_groups = get_core_seeds_for_targets(link_page_ids)
            page_data["quadseeds"] = seed_groups
        else:
            # No links, empty list
            page_data["quadseeds"] = []
        del page_data["links"]  # Remove links field

    # For regular/delay/failure pages, keep links as page IDs
    else:
        page_data["links"] = link_page_ids

    return jsonify(page_data)


@app.route('/graph/random')
def random_page():
    """Get a random page ID to start crawling from (may not reach all pages)"""
    page = random.choice(PAGES)
    return "", 307, {"Location": f"/api/{page['page_id']}"}

@app.route('/api/test/regular')
def test_regular():
    """Redirect to a random regular page"""
    regular_pages = [p for p in PAGES if p["type"] == "regular"]
    if not regular_pages:
        abort(404, description="No regular pages found")
    page = random.choice(regular_pages)
    return "", 307, {"Location": f"/api/{page['page_id']}"}

@app.route('/api/test/delay')
def test_delay():
    """Redirect to a random delay page"""
    delay_pages = [p for p in PAGES if p["type"] == "delay"]
    if not delay_pages:
        abort(404, description="No delay pages found")
    page = random.choice(delay_pages)
    return "", 307, {"Location": f"/api/{page['page_id']}"}

@app.route('/api/test/failure')
def test_failure():
    """Redirect to a random failure page"""
    failure_pages = [p for p in PAGES if p["type"] == "failure"]
    if not failure_pages:
        abort(404, description="No failure pages found")
    page = random.choice(failure_pages)
    return "", 307, {"Location": f"/api/{page['page_id']}"}

@app.route('/api/test/cpu')
def test_cpu():
    """Redirect to a random CPU page"""
    cpu_pages = [p for p in PAGES if p["type"] == "cpu"]
    if not cpu_pages:
        abort(404, description="No CPU pages found")
    page = random.choice(cpu_pages)
    return "", 307, {"Location": f"/api/{page['page_id']}"}

@app.route('/api/test/core')
def test_core():
    """Redirect to a random multi-core page"""
    core_pages = [p for p in PAGES if p["type"] == "core"]
    if not core_pages:
        abort(404, description="No core pages found")
    page = random.choice(core_pages)
    return "", 307, {"Location": f"/api/{page['page_id']}"}



if __name__ == '__main__':
    print("Starting Web Graph Server...")
    print(f"Generated graph with {len(PAGES)} pages")
    regular_count = len([p for p in PAGES if p["type"] == "regular"])
    delay_count = len([p for p in PAGES if p["type"] == "delay"])
    failure_count = len([p for p in PAGES if p["type"] == "failure"])
    cpu_count = len([p for p in PAGES if p["type"] == "cpu"])
    core_count = len([p for p in PAGES if p["type"] == "core"])
    print(f"  - {regular_count} regular pages ({int(REGULAR_PAGE_DELAY*1000)}ms delay)")
    print(f"  - {delay_count} delay pages ({int(DELAY_PAGE_DELAY*1000)}ms delay)")
    print(f"  - {failure_count} failure pages ({int(FAILURE_PAGE_DELAY*1000)}ms delay, {int(FAILURE_PAGE_ERROR_RATE*100)}% error rate)")
    print(f"  - {cpu_count} CPU pages ({int(CPU_PAGE_DELAY*1000)}ms delay, requires {CPU_PAGE_ITERATIONS:,} hash iterations)")
    print(f"  - {core_count} multi-core pages ({int(CORE_PAGE_DELAY*1000)}ms delay, requires {CORE_PAGE_ITERATIONS_PER_CHAR:,} iterations per character)")
    print("Available endpoints:")
    print(f"  http://localhost:{SERVER_PORT}/ - API documentation")
    print(f"  http://localhost:{SERVER_PORT}/graph/random - Get random starting page")
    print(f"  {PAGES[0]['url']} - Example page")

    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)