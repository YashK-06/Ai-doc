#!/usr/bin/env bash
# Pulls the model configured in api/.env so extraction runs fully locally.
# Run this once when you are able to download (~5 GB for qwen3:8b).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../api/.env"

MODEL=""
if [ -f "$ENV_FILE" ]; then
    MODEL=$(grep -E '^OLLAMA_MODEL=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
fi

MODEL="${MODEL:-qwen3:8b}"

echo "Pulling $MODEL from Ollama (this can take a while)..."
ollama pull "$MODEL"

echo ""
echo "Done. Restart the API server and extraction will run fully local:"
echo "  .venv/bin/uvicorn api.main:app --port 8000"
