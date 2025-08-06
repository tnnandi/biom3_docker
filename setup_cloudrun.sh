#!/bin/bash

# Setup script for BioM3 Google Cloud Run deployment
# This script prepares the environment and validates prerequisites

set -e

echo "=== BioM3 Cloud Run Setup ==="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed."
    echo "Please install Google Cloud SDK:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ gcloud CLI found"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "Please install Docker:"
    echo "https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker found"

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud."
    echo "Please run: gcloud auth login"
    exit 1
fi

echo "✅ gcloud authenticated"

# Check if project is set
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$CURRENT_PROJECT" ]; then
    echo "❌ No GCP project set."
    echo "Please set your project ID:"
    echo "gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ GCP project set: $CURRENT_PROJECT"

# Check for required files
echo ""
echo "Checking required files..."

REQUIRED_FILES=(
    "Dockerfile.cloudrun"
    "cloud_run_handler.py"
    "entrypoint_cloudrun.sh"
    "requirements_cloudrun.txt"
    "deploy_to_cloudrun.sh"
    "test_cloudrun.py"
    "cloudrun_client.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        MISSING_FILES=true
    fi
done

if [ "$MISSING_FILES" = true ]; then
    echo ""
    echo "Some required files are missing. Please ensure all files are present."
    exit 1
fi

# Check for configuration files
echo ""
echo "Checking configuration files..."

CONFIG_FILES=(
    "BioM3/stage1_config.json"
    "BioM3/stage2_config.json"
    "BioM3/stage3_config.json"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        MISSING_CONFIG=true
    fi
done

if [ "$MISSING_CONFIG" = true ]; then
    echo ""
    echo "Some configuration files are missing. These are required for deployment."
    echo "Please ensure all configuration files are present in the BioM3/ directory."
    exit 1
fi

# Check for weights directory
echo ""
echo "Checking weights directory..."

if [ -d "weights" ]; then
    echo "✅ weights directory found"
    
    # Check for specific weight files
    WEIGHT_FILES=(
        "weights/PenCL/BioM3_PenCL_epoch20.bin"
        "weights/Facilitator/BioM3_Facilitator_epoch20.bin"
        "weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin"
    )
    
    for file in "${WEIGHT_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "✅ $file"
        else
            echo "❌ $file (missing)"
            MISSING_WEIGHTS=true
        fi
    done
    
    if [ "$MISSING_WEIGHTS" = true ]; then
        echo ""
        echo "Some weight files are missing. Please run:"
        echo "./download_weights.sh"
    fi
else
    echo "❌ weights directory not found"
    echo "Please run: ./download_weights.sh"
fi

# Check for BioM3 directory
echo ""
echo "Checking BioM3 source code..."

if [ -d "BioM3" ]; then
    echo "✅ BioM3 directory found"
else
    echo "❌ BioM3 directory not found"
    echo "Please ensure the BioM3 source code is present."
    exit 1
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x deploy_to_cloudrun.sh
chmod +x entrypoint_cloudrun.sh

echo "✅ Scripts made executable"

# Enable required APIs
echo ""
echo "Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

echo "✅ APIs enabled"

# Set environment variables
echo ""
echo "Setting up environment variables..."
export PROJECT_ID="$CURRENT_PROJECT"
export REGION=${REGION:-"us-central1"}
export SERVICE_NAME=${SERVICE_NAME:-"biom3-service"}

echo "Environment variables:"
echo "  PROJECT_ID: $PROJECT_ID"
echo "  REGION: $REGION"
echo "  SERVICE_NAME: $SERVICE_NAME"

# Create .env file for easy access
cat > .env.cloudrun << EOF
# BioM3 Cloud Run Environment Variables
PROJECT_ID=$PROJECT_ID
REGION=$REGION
SERVICE_NAME=$SERVICE_NAME
MEMORY=8Gi
CPU=4
MAX_INSTANCES=10
TIMEOUT=3600
EOF

echo "✅ Environment file created: .env.cloudrun"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. If weights are missing, run: ./download_weights.sh"
echo "2. Deploy to Cloud Run: ./deploy_to_cloudrun.sh"
echo "3. Test the deployment: python test_cloudrun.py <service_url>"
echo ""
echo "Optional: Customize deployment by editing .env.cloudrun" 