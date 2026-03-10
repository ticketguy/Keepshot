#!/bin/bash
# Load .env and start the FastAPI app
set -a
source "$(dirname "$0")/.env"
set +a

cd "$(dirname "$0")"
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
