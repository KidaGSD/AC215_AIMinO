#!/usr/bin/env bash
set -e

echo "Starting LLM Agent API Server..."

# Start Ollama if using ollama backend
LLM_BACKEND=${LLM_BACKEND:-huggingface}
if [ "$LLM_BACKEND" = "ollama" ]; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 3

    echo "Waiting for Ollama to be ready..."
    for i in {1..60}; do
        if curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
            echo "Ollama is ready"
            break
        fi
        sleep 1
    done

    echo "Pulling model (if not present)..."
    ollama pull llama3.2:3b || true
else
    echo "LLM_BACKEND is $LLM_BACKEND, skipping Ollama startup"
fi

# Start API server
echo "Starting LLM Agent API server..."
cd /app
if [ -f napariLLM.py ]; then
    python napariLLM.py
else
    echo "Error: napariLLM.py not found!"
    exit 1
fi
