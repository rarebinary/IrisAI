#!/bin/bash
# IrisAI Launcher for macOS
# Double-click this file to start IrisAI

cd "$(dirname "$0")"

# Try to activate virtual environment, or create one
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
fi

# Load .env if present
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

echo "Starting IrisAI..."
python main.py

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "IrisAI exited with an error. Press Enter to close."
    read
fi
