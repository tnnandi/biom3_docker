#!/bin/bash

# BioM3 Container Entry Point
echo "BioM3 Container Starting..."
echo "=========================="

# Check if CUDA is available
if command -v nvidia-smi &> /dev/null; then
    echo "CUDA detected:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
else
    echo "CUDA not detected, using CPU"
fi

# If arguments are provided, run them directly
if [ $# -gt 0 ]; then
    echo "Running command: $@"
    exec "$@"
    exit 0
fi

# Otherwise, run the BioM3 pipeline
echo "Running BioM3 pipeline..."

# Check input directory
if [ ! -d "/app/input" ]; then
    echo "Error: /app/input directory not found"
    exit 1
fi

# Check weights directory
if [ ! -d "/app/weights" ]; then
    echo "Error: /app/weights directory not found"
    echo "Please mount the weights directory containing BioM3 model files"
    exit 1
fi

# Find prompt file
PROMPT_FILE=""
if [ -f "/app/input/prompts.txt" ]; then
    PROMPT_FILE="/app/input/prompts.txt"
elif [ -f "/app/input/prompt.txt" ]; then
    PROMPT_FILE="/app/input/prompt.txt"
else
    echo "Error: No prompt file found in /app/input/"
    echo "Please provide prompts.txt or prompt.txt"
    exit 1
fi

echo "Using prompt file: $PROMPT_FILE"

# Run BioM3 pipeline
python3 biom3_container.py \
    --diffusion_steps "${DIFFUSION_STEPS:-1024}" \
    --num_replicas "${NUM_REPLICAS:-5}"

echo "Pipeline complete! Check /app/output for results." 