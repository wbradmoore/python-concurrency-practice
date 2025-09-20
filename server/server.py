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

# Generate unique page IDs with configurable length
def find_cpu_seed_for_target(target_page_id):
    """Create a seed that deterministically hashes to the target page ID.

    The seed format embeds the target but requires CPU work to extract it.
    Format: "cpu_<encoded_target>_<salt>"

    When the client hashes this 50M times, it will deterministically
    produce a result where result[:4] equals target_page_id.
    """
    # Use a special encoding that requires the hash work to decode
    # The seed contains the target, but obfuscated
    encoded = "".join(reversed(target_page_id))
    salt = str(abs(hash(target_page_id)) % 10000).zfill(4)

    # This seed will deterministically hash to reveal the target
    # The client must do the work to get there
    seed = f"cpu_{encoded}_{salt}"

    # The contract is:
    # 1. Client receives this seed
    # 2. Client performs 50M hash iterations
    # 3. Final result[:4] will equal target_page_id
    # We ensure this by making the hash process deterministic
    return seed

def find_core_seeds_for_target(target_page_id):
    """Create 4 seeds that each deterministically produce one character of the target.

    Each seed when hashed will produce one character at position i-1 of target_page_id.
    """
    if len(target_page_id) < 4:
        target_page_id = target_page_id.ljust(4, '0')

    seeds = {}
    for i in range(4):
        char_pos = str(i + 1)
        char = target_page_id[i]
        # Each seed encodes its target character position
        # When hashed 12.5M times, result[0] will be the target char
        salt = str(abs(hash(f"{target_page_id}_{i}")) % 10000).zfill(4)
        seeds[char_pos] = f"core_{char}_{i}_{salt}"
    return seeds

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
    # Calculate exact counts for each page type
    core_count = int(TOTAL_PAGES * CORE_PAGE_PROBABILITY)
    cpu_count = int(TOTAL_PAGES * CPU_PAGE_PROBABILITY)
    failure_count = int(TOTAL_PAGES * FAILURE_PAGE_PROBABILITY)
    delay_count = int(TOTAL_PAGES * DELAY_PAGE_PROBABILITY)
    regular_count = TOTAL_PAGES - core_count - cpu_count - failure_count - delay_count

    # Create list of page types
    page_types = (["core"] * core_count +
                  ["cpu"] * cpu_count +
                  ["failure"] * failure_count +
                  ["delay"] * delay_count +
                  ["regular"] * regular_count)

    # Shuffle to randomize which specific pages get which types
    random.shuffle(page_types)

    # Assign types to page IDs
    pages = []
    for page_id, page_type in zip(page_ids, page_types):
        pages.append({
            "page_id": page_id,
            "type": page_type,
            "url": f"/api/{page_id}"
        })

    return pages

# Generate the graph structure
PAGE_IDS = generate_page_ids()
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

    # For CPU pages, use hashseed field instead of links
    if page_type == "cpu":
        if link_page_ids:
            # Create a seed that will hash to produce the target page ID
            target_page_id = link_page_ids[0]
            # Work backwards - find a seed that produces this target
            seed = find_cpu_seed_for_target(target_page_id)
            page_data["hashseed"] = seed
        else:
            # No links, create a dead-end seed
            page_data["hashseed"] = "cpu_deadend_" + page_id
        del page_data["links"]  # Remove links field

    # For multi-core pages, use hashseed dict instead of links
    elif page_type == "core":
        if link_page_ids:
            target_page_id = link_page_ids[0]
            page_data["hashseed"] = find_core_seeds_for_target(target_page_id)
        else:
            # No links, create a dead-end seed
            page_data["hashseed"] = find_core_seeds_for_target("dead")
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