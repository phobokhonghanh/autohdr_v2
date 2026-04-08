#!/bin/bash

# run_local.sh - Utility to setup and run AutoHDR Backend locally

# Check if current directory is autohdr_backend
CURRENT_DIR=$(basename "$PWD")

if [ "$CURRENT_DIR" != "autohdr_backend" ]; then
    if [ "$CURRENT_DIR" == "autohdr_v2" ]; then
        echo "Moving to autohdr_backend directory..."
        cd autohdr_backend || { echo "Failed to enter autohdr_backend"; exit 1; }
    else
        echo "Error: Please run this script from 'autohdr_v2' or 'autohdr_backend' directory."
        exit 1
    fi
fi

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "Virtual environment 'venv' not found. Creating it..."
    python3 -m venv venv || { echo "Failed to create virtual environment"; exit 1; }
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Install or update requirements
echo "Installing requirements from requirements.txt..."
pip install -r requirements.txt || { echo "Failed to install requirements"; exit 1; }

# Clean up port 8000 if it's already in use
PORT=8000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "Port $PORT already in use. Cleaning up..."
    lsof -t -i:$PORT | xargs kill -9
fi

# Run the application
echo "Starting AutoHDR Backend (app.py)..."
python app.py
