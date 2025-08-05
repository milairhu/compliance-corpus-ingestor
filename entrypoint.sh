#!/bin/sh
set -e

if [ -z "$QDRANT_URL" ]; then
  echo "Error: QDRANT_URL environment variable is not set."
  exit 1
fi
if [ -z "$CORPUS" ]; then
  echo "Error: CORPUS environment variable is not set."
  exit 1
fi

uvicorn main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

sleep 15

# Populate the Qdrant database with the provided corpus
curl -X POST http://localhost:8000/corpus/clean \
  -H "Content-Type: application/json" \
  -d '{"qdrant_url": "'${QDRANT_URL}'"}'
curl -X POST http://localhost:8000/corpus/ingest \
  -H "Content-Type: application/json" \
  -d '{"qdrant_url": "'${QDRANT_URL}'", "corpus": "'${CORPUS}'"}'

wait $UVICORN_PID