#!/bin/bash

# BioM3 Model Weights Download Script
# This script downloads all required pre-trained weights for the BioM3 pipeline

set -e  # Exit on any error

echo "=========================================="
echo "BioM3 Model Weights Download Script"
echo "=========================================="

# Check if gdown is installed
if ! command -v gdown &> /dev/null; then
    echo "Installing gdown..."
    pip install gdown
else
    echo "gdown is already installed"
fi

# Create weights directory structure
echo "Creating weights directory structure..."
mkdir -p weights/LLMs weights/PenCL weights/Facilitator weights/ProteoScribe

# Function to check if file exists and has expected size
check_file() {
    local file_path="$1"
    local expected_size="$2"
    
    if [ -f "$file_path" ]; then
        local actual_size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "0")
        if [ "$actual_size" -gt 1000000 ]; then  # File exists and is >1MB
            echo "✓ $file_path already exists"
            return 0
        fi
    fi
    return 1
}

# Download LLMs
echo ""
echo "=== Downloading LLMs (ESM2 and PubMedBERT) ==="
cd weights/LLMs

# ESM2 model weights
if ! check_file "esm2_t33_650M_UR50D.pt" "2.4GB"; then
    echo "Downloading ESM2 model weights..."
    wget https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt
else
    echo "ESM2 model weights already exist"
fi

if ! check_file "esm2_t33_650M_UR50D-contact-regression.pt" "3.6KB"; then
    echo "Downloading ESM2 contact regression weights..."
    wget https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t33_650M_UR50D-contact-regression.pt
else
    echo "ESM2 contact regression weights already exist"
fi

# PubMedBERT model
if [ ! -d "BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext" ]; then
    echo "Downloading PubMedBERT model..."
    git lfs install
    git clone https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext
else
    echo "PubMedBERT model already exists"
fi

# Download PenCL weights
echo ""
echo "=== Downloading PenCL weights ==="
cd ../PenCL

if ! check_file "BioM3_PenCL_epoch20.bin" "2.8GB"; then
    echo "Downloading PenCL weights..."
    gdown --id 1Lup7Xqwa1NjJpoM2uvvBAdghoM-fecEj -O BioM3_PenCL_epoch20.bin
else
    echo "PenCL weights already exist"
fi

# Download Facilitator weights
echo ""
echo "=== Downloading Facilitator weights ==="
cd ../Facilitator

if ! check_file "BioM3_Facilitator_epoch20.bin" "4MB"; then
    echo "Downloading Facilitator weights..."
    gdown --id 1_YWwILXDkx9MSoSA1kfS-y0jk3Vy4HJE -O BioM3_Facilitator_epoch20.bin
else
    echo "Facilitator weights already exist"
fi

# Download ProteoScribe weights
echo ""
echo "=== Downloading ProteoScribe weights ==="
cd ../ProteoScribe

if ! check_file "BioM3_ProteoScribe_pfam_epoch20_v1.bin" "329MB"; then
    echo "Downloading ProteoScribe weights..."
    gdown --id 1c3CwvbOP_kp3FpLL1wPrjO6qtY-XiT26 -O BioM3_ProteoScribe_pfam_epoch20_v1.bin
else
    echo "ProteoScribe weights already exist"
fi

# Go back to original directory
cd ../..

echo ""
echo "=========================================="
echo "Download Summary"
echo "=========================================="

# Check all files
echo "Verifying downloaded files..."
echo ""

# LLMs
echo "LLMs:"
if [ -f "weights/LLMs/esm2_t33_650M_UR50D.pt" ]; then
    size=$(ls -lh weights/LLMs/esm2_t33_650M_UR50D.pt | awk '{print $5}')
    echo "  ✓ esm2_t33_650M_UR50D.pt ($size)"
else
    echo "  ✗ esm2_t33_650M_UR50D.pt (missing)"
fi

if [ -f "weights/LLMs/esm2_t33_650M_UR50D-contact-regression.pt" ]; then
    size=$(ls -lh weights/LLMs/esm2_t33_650M_UR50D-contact-regression.pt | awk '{print $5}')
    echo "  ✓ esm2_t33_650M_UR50D-contact-regression.pt ($size)"
else
    echo "  ✗ esm2_t33_650M_UR50D-contact-regression.pt (missing)"
fi

if [ -d "weights/LLMs/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext" ]; then
    echo "  ✓ BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext/ (directory)"
else
    echo "  ✗ BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext/ (missing)"
fi

# PenCL
echo ""
echo "PenCL:"
if [ -f "weights/PenCL/BioM3_PenCL_epoch20.bin" ]; then
    size=$(ls -lh weights/PenCL/BioM3_PenCL_epoch20.bin | awk '{print $5}')
    echo "  ✓ BioM3_PenCL_epoch20.bin ($size)"
else
    echo "  ✗ BioM3_PenCL_epoch20.bin (missing)"
fi

# Facilitator
echo ""
echo "Facilitator:"
if [ -f "weights/Facilitator/BioM3_Facilitator_epoch20.bin" ]; then
    size=$(ls -lh weights/Facilitator/BioM3_Facilitator_epoch20.bin | awk '{print $5}')
    echo "  ✓ BioM3_Facilitator_epoch20.bin ($size)"
else
    echo "  ✗ BioM3_Facilitator_epoch20.bin (missing)"
fi

# ProteoScribe
echo ""
echo "ProteoScribe:"
if [ -f "weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin" ]; then
    size=$(ls -lh weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin | awk '{print $5}')
    echo "  ✓ BioM3_ProteoScribe_pfam_epoch20_v1.bin ($size)"
else
    echo "  ✗ BioM3_ProteoScribe_pfam_epoch20_v1.bin (missing)"
fi

echo ""
echo "=========================================="
echo "All downloads completed!"
echo "=========================================="
echo ""
echo "Expected file sizes:"
echo "  - esm2_t33_650M_UR50D.pt: ~2.4GB"
echo "  - BioM3_PenCL_epoch20.bin: ~2.8GB"
echo "  - BioM3_Facilitator_epoch20.bin: ~4MB"
echo "  - BioM3_ProteoScribe_pfam_epoch20_v1.bin: ~329MB"
echo ""
echo "For detailed usage instructions, see:"
echo "  - weights/LLMs/README.md"
echo "  - weights/PenCL/README.md"
echo "  - weights/Facilitator/README.md"
echo "  - weights/ProteoScribe/README.md"
echo ""
echo "For troubleshooting, see DOWNLOAD_WEIGHTS.md" 