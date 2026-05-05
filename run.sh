#!/bin/bash

# Termi-music Run Script for Linux/macOS

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if requirements are installed (simple check for textual)
if ! python3 -c "import textual" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the application
python3 main.py
