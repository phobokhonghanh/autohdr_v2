#!/bin/bash
# Start script for Railway/Production
# Ensures $PORT is correctly expanded by the shell

# Default to 8000 if PORT is not set (e.g. local testing)
PORT_VALUE=${PORT:-8000}

echo "🚀 Starting server on port $PORT_VALUE..."
python -m uvicorn app:app --host 0.0.0.0 --port "$PORT_VALUE"
