#!/usr/bin/env python3

from flask import Flask, jsonify, abort
import random
import string
import time
from abc import ABC, abstractmethod
from config import *

# Validate configuration on startup
validate_config()

app = Flask(__name__)

# Page Type System
class PageType(ABC):
    """Abstract base class for different page types"""

    @abstractmethod
    def get_url_path(self, page_id):
        """Return the URL path for this page type"""
        pass

    @abstractmethod
    def get_delay(self):
        """Return the delay in seconds for this page type"""
        pass

    @abstractmethod
    def get_type_name(self):
        """Return a human-readable name for this page type"""
        pass

class RegularPageType(PageType):
    """Regular pages with configurable delay"""

    def get_url_path(self, page_id):
        return REGULAR_PAGE_PATH_TEMPLATE.format(page_id=page_id)

    def get_delay(self):
        return REGULAR_PAGE_DELAY

    def get_type_name(self):
        return "regular"

class DelayPageType(PageType):
    """High-delay pages with configurable delay"""

    def get_url_path(self, page_id):
        return DELAY_PAGE_PATH_TEMPLATE.format(page_id=page_id)

    def get_delay(self):
        return DELAY_PAGE_DELAY

    def get_type_name(self):
        return "delay"

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
    """Assign page types to page IDs"""
    pages = []
    regular_type = RegularPageType()
    delay_type = DelayPageType()

    for page_id in page_ids:
        # Configurable chance of being a delay page
        if random.random() < DELAY_PAGE_PROBABILITY:
            page_type = delay_type
        else:
            page_type = regular_type

        pages.append({
            "page_id": page_id,
            "type": page_type,
            "url": page_type.get_url_path(page_id)
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
    return [p for p in PAGES if p["type"].get_type_name() == "regular"]

def choose_target_page():
    """Choose a target page with configurable bias toward regular pages"""
    if random.random() < REGULAR_PAGE_BIAS:
        # Configurable chance: pick from regular pages
        regular_pages = get_regular_pages()
        if regular_pages:
            return random.choice(regular_pages)

    # Remaining chance or no regular pages: pick from all pages
    return random.choice(PAGES)

def build_graph():
    """Build an organic connected graph starting from a root page"""
    global GRAPH

    # Initialize all pages with empty link lists
    for page in PAGES:
        page_id = page["page_id"]
        GRAPH[page_id] = {
            "page_id": page_id,
            "page_type": page["type"].get_type_name(),
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
        target_page = choose_target_page()  # 90% bias toward regular pages

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
        "links": [PAGES[0]["url"]],
        "link_count": 1,
        "message": "This is the root page. Start crawling from here.",
        "total_pages_in_graph": len(PAGES),
        "page_type_distribution": {
            "regular": len([p for p in PAGES if p["type"].get_type_name() == "regular"]),
            "delay": len([p for p in PAGES if p["type"].get_type_name() == "delay"])
        },
        "requested_at": time.time(),
        "url": "/api/"
    }
    return jsonify(root_data)

@app.route('/api/<page_id>')
def get_regular_page(page_id):
    """Get a regular page with its links"""
    return serve_page(page_id, "regular")

@app.route('/api/delay/<page_id>')
def get_delay_page(page_id):
    """Get a delay page with its links"""
    return serve_page(page_id, "delay")

def serve_page(page_id, expected_type):
    """Generic page serving function"""
    if page_id not in GRAPH:
        abort(404, description=PAGE_NOT_FOUND_MESSAGE.format(page_id=page_id))

    page_obj = get_page_by_id(page_id)
    if not page_obj:
        abort(404, description=PAGE_NOT_FOUND_MESSAGE.format(page_id=page_id))

    # Verify page type matches the requested route
    if page_obj["type"].get_type_name() != expected_type:
        abort(404, description=WRONG_PAGE_TYPE_MESSAGE.format(page_id=page_id, expected_type=expected_type))

    # Apply the appropriate delay for this page type
    delay = page_obj["type"].get_delay()
    time.sleep(delay)

    page_data = GRAPH[page_id].copy()
    page_data["requested_at"] = time.time()
    page_data["url"] = page_obj["url"]
    page_data["delay_ms"] = int(delay * 1000)

    return jsonify(page_data)

@app.route('/graph/stats')
def graph_stats():
    """Get statistics about the graph"""
    page_ids = [p["page_id"] for p in PAGES]
    link_counts = [len(GRAPH[page_id]["links"]) for page_id in page_ids]

    # Count dead ends (pages with no outgoing links)
    dead_ends = [page_id for page_id in page_ids if len(GRAPH[page_id]["links"]) == 0]

    # Page type statistics
    regular_pages = [p for p in PAGES if p["type"].get_type_name() == "regular"]
    delay_pages = [p for p in PAGES if p["type"].get_type_name() == "delay"]

    # Verify connectivity by doing a BFS from first page
    visited = set()
    queue = [PAGES[0]["page_id"]]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for link in GRAPH[current]["links"]:
            # Extract page_id from URL (could be /api/xxxx or /api/delay/xxxx)
            parts = link.strip('/').split('/')
            linked_page = parts[-1]  # Last part is always the page_id
            if linked_page not in visited:
                queue.append(linked_page)

    is_connected = len(visited) == len(PAGES)

    # Calculate distribution
    link_distribution = {}
    for count in link_counts:
        link_distribution[count] = link_distribution.get(count, 0) + 1

    return jsonify({
        "total_pages": len(PAGES),
        "page_types": {
            "regular": {
                "count": len(regular_pages),
                "percentage": round(len(regular_pages) / len(PAGES) * 100, 1),
                "delay_ms": 500
            },
            "delay": {
                "count": len(delay_pages),
                "percentage": round(len(delay_pages) / len(PAGES) * 100, 1),
                "delay_ms": 5000
            }
        },
        "total_edges": sum(link_counts),
        "avg_links_per_page": round(sum(link_counts) / len(link_counts), 2),
        "min_links": min(link_counts),
        "max_links": max(link_counts),
        "dead_ends_count": len(dead_ends),
        "dead_ends": dead_ends[:MAX_DEAD_ENDS_SHOWN],  # Show configurable number of dead ends
        "is_connected": is_connected,
        "reachable_from_root": len(visited),
        "link_distribution": link_distribution,
        "pages_with_most_links": [
            {
                "page_id": page_id,
                "page_type": GRAPH[page_id]["page_type"],
                "link_count": len(GRAPH[page_id]["links"])
            }
            for page_id in sorted(page_ids, key=lambda p: len(GRAPH[p]["links"]), reverse=True)[:MAX_TOP_PAGES_SHOWN]
        ]
    })

@app.route('/graph/random')
def random_page():
    """Get a random page ID to start crawling from"""
    page = random.choice(PAGES)
    return jsonify({
        "page_id": page["page_id"],
        "page_type": page["type"].get_type_name(),
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
                "page_type": page["type"].get_type_name(),
                "url": page["url"]
            }
            for page in sample
        ],
        "message": "Sample pages for testing different concurrency approaches"
    })

@app.route('/graph/search/<page_id>')
def search_from_page(page_id):
    """Get all pages reachable from a given page (BFS traversal)"""
    if page_id not in GRAPH:
        abort(404, description=f"Page {page_id} not found")

    # Perform BFS to find all reachable pages
    visited = set()
    queue = [page_id]
    reachable = []

    while queue and len(visited) < MAX_SEARCH_RESULTS:  # Configurable limit to prevent timeout
        current = queue.pop(0)
        if current in visited:
            continue

        visited.add(current)
        reachable.append(current)

        # Add linked pages to queue
        for link in GRAPH[current]["links"]:
            linked_page_id = link.split('/')[-1]  # Extract page_id from /api/xxxx
            if linked_page_id not in visited:
                queue.append(linked_page_id)

    return jsonify({
        "start_page": page_id,
        "reachable_count": len(reachable),
        "reachable_pages": reachable,
        "reachable_urls": [f"/api/{pid}" for pid in reachable],
        "note": f"Limited to {MAX_SEARCH_RESULTS} pages to prevent timeout"
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
    regular_count = len([p for p in PAGES if p["type"].get_type_name() == "regular"])
    delay_count = len([p for p in PAGES if p["type"].get_type_name() == "delay"])
    print(f"  - {regular_count} regular pages (500ms delay)")
    print(f"  - {delay_count} delay pages (5000ms delay)")
    print("Available endpoints:")
    print("  http://localhost:5000/ - API documentation")
    print("  http://localhost:5000/health - Health check")
    print("  http://localhost:5000/graph/random - Get random starting page")
    print("  http://localhost:5000/graph/stats - Graph statistics")
    print(f"  {PAGES[0]['url']} - Example page")

    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)