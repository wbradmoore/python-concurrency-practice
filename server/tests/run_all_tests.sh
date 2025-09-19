#!/bin/bash


cleanup() {
    echo "Stopping server..."
    cd "$(dirname "$0")/.." || exit 1
    docker compose down &> /dev/null 2>&1
}

trap cleanup EXIT

echo "Python Concurrency Practice - Test Runner"

if ! command -v docker &> /dev/null; then
    echo "Docker not installed. Install from https://www.docker.com"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "Docker not running. Please start Docker."
    exit 1
fi

cd "$(dirname "$0")/.." || exit 1

echo "Starting server..."
docker compose down &> /dev/null 2>&1
docker compose up --build -d &> /dev/null

echo -n "Waiting for server"
for i in {1..30}; do
    if curl -s http://localhost:5000/health &> /dev/null; then
        echo " ready!"
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo " failed!"
        exit 1
    fi
    echo -n "."
    sleep 1
done

cd tests || exit 1

echo "Running tests..."
ALL_PASSED=true

for test_file in test_*.py; do
    if [[ -f "$test_file" ]]; then
        echo "Running $test_file..."
        if timeout 120 python3 "$test_file"; then
            echo "✓ $test_file passed"
        else
            echo "✗ $test_file failed"
            ALL_PASSED=false
        fi
    fi
done

if [[ "$ALL_PASSED" == "true" ]]; then
    echo "All tests passed!"
    exit 0
else
    echo "Some tests failed"
    exit 1
fi