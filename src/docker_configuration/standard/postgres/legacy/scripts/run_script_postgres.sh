#!/bin/bash
# or
# !/bin/sh
set -e

echo "Starting Postgres orchestration..."
# Run the initial setup of the database
python /app/setup-postgres.py
# Technically no pause of the system needed due to defined backoff
#sleep 5
# Run of the respective experiments
#python /app/db_test_postgres.py




