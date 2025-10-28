#!/bin/bash
set -e

echo "Waiting for Neo4j to be ready..."
while ! curl -s http://sm3_neo4j:7474 >/dev/null; do
    sleep 1
done

echo "Starting Neo4j data ingestion..."
cd /app/pyingest
python3 src/main/ingest.py /app/config_neo4j.yml