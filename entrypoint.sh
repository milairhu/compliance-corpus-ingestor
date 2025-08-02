#!/bin/sh
set -e

ARGS=""

[ -n "${QDRANT_URL}" ] && ARGS="${ARGS} --qdrant-url ${QDRANT_URL}"
[ -n "${CORPUS_DIR}" ] && ARGS="${ARGS} --corpus ${CORPUS_DIR}"

eval python ingestor.py $ARGS