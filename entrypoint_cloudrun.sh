#!/bin/bash

# Google Cloud Run Entrypoint for BioM3
# This script starts the HTTP server for Google Cloud Run

set -e

echo "Starting BioM3 Cloud Run service..."

# Check if weights directory exists
if [ ! -d "/app/weights" ]; then
    echo "Warning: Weights directory not found. Please ensure weights are properly mounted."
    echo "Expected weights structure:"
    echo "  /app/weights/PenCL/BioM3_PenCL_epoch20.bin"
    echo "  /app/weights/Facilitator/BioM3_Facilitator_epoch20.bin"
    echo "  /app/weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin"
fi

# Check if configuration files exist
for config_file in stage1_config.json stage2_config.json stage3_config.json; do
    if [ ! -f "/app/$config_file" ]; then
        echo "Error: Configuration file $config_file not found"
        exit 1
    fi
done

# Create input/output directories if they don't exist
mkdir -p /app/input /app/output

# Set default input file if it doesn't exist
if [ ! -f "/app/input/prompts.txt" ]; then
    echo "Creating default prompts file..."
    cat > /app/input/prompts.txt << EOF
PROTEIN NAME: Translation initiation factor IF-1. FUNCTION: One of the essential components for the initiation of protein synthesis. Binds in the vicinity of the A-site. Stabilizes the binding of IF-2 and IF-3 on the 30S subunit to which N-formylmethionyl-tRNA(fMet) subsequently binds. Helps modulate mRNA selection, yielding the 30S pre-initiation complex (PIC). Upon addition of the 50S ribosomal subunit, IF-1, IF-2 and IF-3 are released leaving the mature 70S translation initiation complex.
EOF
fi

# Set environment variables for Cloud Run
export PORT=${PORT:-8080}
export DIFFUSION_STEPS=${DIFFUSION_STEPS:-1024}
export NUM_REPLICAS=${NUM_REPLICAS:-5}

echo "Environment variables:"
echo "  PORT: $PORT"
echo "  DIFFUSION_STEPS: $DIFFUSION_STEPS"
echo "  NUM_REPLICAS: $NUM_REPLICAS"

# Check if Python and required modules are available
echo "Checking Python environment..."
python3 --version
python3 -c "import flask; print('Flask available')" || echo "Flask not available"
python3 -c "import torch; print('PyTorch available')" || echo "PyTorch not available"

# List files in /app directory for debugging
echo "Files in /app directory:"
ls -la /app/

# Start the HTTP server with better error handling
echo "Starting HTTP server on port $PORT..."
echo "Command: python3 cloud_run_handler.py"
exec python3 cloud_run_handler.py 