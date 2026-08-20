#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -f .env ]; then
  echo "Copy .env.example to .env and fill in your CognoDB credentials first."
  exit 1
fi
export $(grep -v '^#' .env | xargs)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
