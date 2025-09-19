#!/usr/bin/env python3

from flask import Flask, jsonify, abort
import random
import string
import time
from config import *

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
    # Add configurable number of random edges to create cycles and increase connectivity
    edges_added = 0
    attempts = 0

    while edges_added < ADDITIONAL_EDGES and attempts < MAX_ATTEMPTS_EDGE_GENERATION:
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
        "description": "A graph of 1000 interconnected web pages for concurrency testing",
        "total_pages": len(PAGE_IDS),
        "links": [PAGES[0]["url"]],
        "concurrency_tests": [
            "Crawl the entire graph",
            "Find shortest path between two pages",
            "Count total unique pages reachable from a starting point",
            "Find pages with most/least outbound links"
        ]
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

    page_type = page_obj["type"].get_type_name()

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
            # Generate a random seed - the target page ID is determined by the hash result
            seed = f"cpu_seed_{random.randint(10000, 99999)}"
            page_data["hashseed"] = seed
        else:
            page_data["hashseed"] = f"cpu_seed_{random.randint(10000, 99999)}"
        del page_data["links"]  # Remove links field

    # For multi-core pages, use hashseed dict instead of links
    elif page_type == "core":
        if link_page_ids:
            target_page_id = link_page_ids[0]
            page_data["hashseed"] = {
                "1": f"core_seed_{random.randint(10000, 99999)}_1",
                "2": f"core_seed_{random.randint(10000, 99999)}_2",
                "3": f"core_seed_{random.randint(10000, 99999)}_3",
                "4": f"core_seed_{random.randint(10000, 99999)}_4"
            }
        else:
            page_data["hashseed"] = {
                "1": f"core_seed_{random.randint(10000, 99999)}_1",
                "2": f"core_seed_{random.randint(10000, 99999)}_2",
                "3": f"core_seed_{random.randint(10000, 99999)}_3",
                "4": f"core_seed_{random.randint(10000, 99999)}_4"
            }
        del page_data["links"]  # Remove links field

    # For regular/delay/failure pages, keep links as page IDs
    else:
        page_data["links"] = link_page_ids

    return jsonify(page_data)


@app.route('/graph/random')
def random_page():
    """Get a random page ID to start crawling from"""
    page = random.choice(PAGES)
    return jsonify({
        "page_id": page["page_id"],
        "page_type": page["type"],
        "url": page["url"],
        "message": "Use this as a starting point for crawling"
    })

@app.route('/graph/sample')
def sample_pages():
    """Get a sample of pages for testing"""
    sample_size = min(MAX_SAMPLE_SIZE, len(PAGES))
    sample = random.sample(PAGES, sample_size)

    return jsonify({
        "sample_size": sample_size,
        "pages": [
            {
                "page_id": page["page_id"],
                "page_type": page["type"],
                "url": page["url"]
            }
            for page in sample
        ],
        "message": "Sample pages for testing different concurrency approaches"
    })


@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "message": "Web Graph Server is running",
        "graph_size": len(PAGE_IDS)
    })

if __name__ == '__main__':
    print("Starting Web Graph Server...")
    print(f"Generated graph with {len(PAGES)} pages")
    regular_count = len([p for p in PAGES if p["type"] == "regular"])
    delay_count = len([p for p in PAGES if p["type"] == "delay"])
    failure_count = len([p for p in PAGES if p["type"] == "failure"])
    cpu_count = len([p for p in PAGES if p["type"] == "cpu"])
    core_count = len([p for p in PAGES if p["type"] == "core"])
    print(f"  - {regular_count} regular pages (500ms delay)")
    print(f"  - {delay_count} delay pages (5000ms delay)")
    print(f"  - {failure_count} failure pages (500ms delay, 90% error rate)")
    print(f"  - {cpu_count} CPU pages (100ms delay, requires {CPU_PAGE_ITERATIONS:,} hash iterations)")
    print(f"  - {core_count} multi-core pages (100ms delay, requires {CORE_PAGE_ITERATIONS_PER_CHAR:,} iterations per character)")
    print("Available endpoints:")
    print("  http://localhost:5000/ - API documentation")
    print("  http://localhost:5000/health - Health check")
    print("  http://localhost:5000/graph/random - Get random starting page")
    print("  http://localhost:5000/graph/stats - Graph statistics")
    print(f"  {PAGES[0]['url']} - Example page")

    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)