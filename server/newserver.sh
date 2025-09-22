#!/bin/bash
docker compose down
docker compose build
docker compose up -d

echo "Waiting for server to be ready..."
while ! curl -s http://localhost:5000/api/ > /dev/null 2>&1; do
    sleep 1
done
echo "Server is ready!"
