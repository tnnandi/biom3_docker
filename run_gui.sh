#!/bin/bash

# BioM3 GUI Launcher
# This script launches the BioM3 GUI application

echo "=========================================="
echo "BioM3 GUI Launcher"
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if tkinter is available
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: tkinter is not available."
    echo "Please install tkinter for your Python installation."
    echo ""
    echo "On Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "On macOS: brew install python-tk"
    echo "On Windows: tkinter should be included with Python"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker is not installed."
    echo "Please install Docker Desktop to use BioM3."
    echo "Download from: https://www.docker.com/products/docker-desktop/"
    echo ""
    echo "The GUI will still launch, but you won't be able to run the pipeline."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Warning: Docker is not running."
    echo "Please start Docker Desktop before using BioM3."
    echo ""
    echo "The GUI will still launch, but you won't be able to run the pipeline."
fi

echo "Launching BioM3 GUI..."
echo ""

# Run the GUI
python3 biom3_gui.py 