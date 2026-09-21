#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "==================================================================="
echo "   Starting SyncLM Studio — TechDocs Sync Engine for NotebookLM    "
echo "==================================================================="

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Check frontend build
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend application..."
    cd frontend
    npm install
    npm run build
    cd "$DIR"
fi

echo "Starting FastAPI Server on http://0.0.0.0:8000 ..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
