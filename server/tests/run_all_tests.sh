#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${PURPLE}${BOLD}$1${NC}"
}

print_status() {
    case $2 in
        "success")
            echo -e "${GREEN}[SUCCESS] $1${NC}"
            ;;
        "error")
            echo -e "${RED}[ERROR] $1${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}[WARNING] $1${NC}"
            ;;
        *)
            echo -e "${CYAN}[INFO] $1${NC}"
            ;;
    esac
}

cleanup() {
    print_header "Cleaning Up"
    print_status "Stopping server..." "info"
    cd "$(dirname "$0")/.." || exit 1

    if command -v docker &> /dev/null; then
        if docker compose ps -q &> /dev/null; then
            docker compose down &> /dev/null
        elif command -v docker-compose &> /dev/null; then
            docker-compose down &> /dev/null
        fi
    fi
    print_status "Server stopped" "success"
}

# Handle interrupt signal (Ctrl+C) and exit
interrupt_handler() {
    echo -e "\n${YELLOW}[INFO] Interrupted by user (Ctrl+C)${NC}"
    print_header "Cleaning Up After Interrupt"
    cleanup
    exit 130
}

# Trap to ensure cleanup on exit and interrupt
trap cleanup EXIT
trap interrupt_handler INT

echo -e "${BOLD}${PURPLE}"
echo "Python Concurrency Practice - Test Runner"
echo "Testing Web Graph with 1000 Interconnected Pages"
echo -e "${NC}"

# Check if Docker is installed
print_status "Checking Docker installation..." "info"

if ! command -v docker &> /dev/null; then
    print_status "Docker is not installed!" "error"
    echo
    echo "To install Docker:"
    echo "  - Mac/Windows: Download Docker Desktop from https://www.docker.com/products/docker-desktop"
    echo "  - Linux: Run: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_status "Docker is installed but not running!" "error"
    echo
    echo "Please start Docker:"
    echo "  - Mac/Windows: Start Docker Desktop application"
    echo "  - Linux: Run: sudo systemctl start docker"
    exit 1
fi

print_status "Docker is installed and running" "success"

# Navigate to server directory
SERVER_ROOT="$(dirname "$0")/.."
cd "$SERVER_ROOT" || {
    print_status "Cannot find server directory" "error"
    exit 1
}

print_header "Starting Demo Server"

# Stop any existing container
print_status "Stopping any existing containers..." "info"
if docker compose ps -q &> /dev/null; then
    docker compose down &> /dev/null 2>&1
elif command -v docker-compose &> /dev/null; then
    docker-compose down &> /dev/null 2>&1
fi

print_status "Building and starting the web graph server..." "info"
print_status "This may take a minute on first run while Docker downloads images..." "info"

# Try docker compose (v2) first, then docker-compose (v1)
if docker compose up --build -d &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null && docker-compose up --build -d &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    print_status "Failed to start server with docker compose!" "error"
    exit 1
fi

# Wait for server to be ready
print_status "Waiting for server to be ready..." "info"
echo -n "Checking"

for i in {1..30}; do
    if curl -s http://localhost:5000/health &> /dev/null; then
        echo
        print_status "Server is ready!" "success"

        # Show server info
        echo -e "\n${BOLD}Server Info:${NC}"
        SERVER_INFO=$(curl -s http://localhost:5000/health 2>/dev/null)
        if [[ $? -eq 0 ]]; then
            echo "  • Status: healthy"
            echo "  • Graph size: $(echo "$SERVER_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['graph_size'])" 2>/dev/null || echo "1000") pages"
            echo "  • URL: http://localhost:5000"
        fi
        break
    fi

    if [[ $i -eq 30 ]]; then
        echo
        print_status "Server failed to start within 30 seconds!" "error"
        echo
        echo "Debug info:"
        $COMPOSE_CMD logs --tail=10
        exit 1
    fi

    echo -n "."
    sleep 1
done

print_header "Running Tests"

# Change to tests directory
cd tests || {
    print_status "Cannot find tests directory" "error"
    exit 1
}

# Find all test files
TEST_FILES=(test_*.py)

if [[ ${#TEST_FILES[@]} -eq 0 ]] || [[ ! -f "${TEST_FILES[0]}" ]]; then
    print_status "No test files found!" "warning"
    exit 0
fi

ALL_PASSED=true

# Run each test file
for test_file in "${TEST_FILES[@]}"; do
    if [[ -f "$test_file" ]]; then
        echo -e "\n${BOLD}Running: $test_file${NC}"
        echo "----------------------------------------"

        if timeout 120 python3 "$test_file"; then
            print_status "$test_file passed" "success"
        else
            print_status "$test_file failed" "error"
            ALL_PASSED=false
        fi
    fi
done

print_header "Test Summary"

if [[ "$ALL_PASSED" == "true" ]]; then
    print_status "All tests passed!" "success"
    echo -e "\n${GREEN}Everything is working correctly!${NC}"
    echo
    echo "You can now:"
    echo "  1. Start the server manually: docker compose up"
    echo "  2. Visit http://localhost:5000 to see the API"
    echo "  3. Try the concurrency examples in CONCEPTS.md"
    echo
    echo "The server will be automatically stopped when this script exits."

    # Ask if user wants to keep server running
    echo
    read -p "Do you want to keep the server running? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Server will keep running at http://localhost:5000" "info"
        print_status "To stop it later, run: docker compose down" "info"
        trap - EXIT  # Remove the cleanup trap
    fi

    exit 0
else
    print_status "Some tests failed" "error"
    echo
    echo "Check the output above for details."
    exit 1
fi