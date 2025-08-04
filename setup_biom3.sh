#!/bin/bash

# BioM3 Complete Setup Script
# This script pulls the BioM3 container and downloads all required weights

set -e  # Exit on any error

echo "=========================================="
echo "BioM3 Complete Setup Script"
echo "=========================================="

# Configuration
DOCKER_USERNAME="tnnandi"
IMAGE_NAME="biom3"
VERSION="v1.1"
LATEST_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop first:"
        echo "  https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Pull the Docker container
pull_container() {
    print_status "Pulling BioM3 container from Docker Hub..."
    
    # Try to pull the specific version first
    if docker pull $DOCKER_USERNAME/$IMAGE_NAME:$VERSION; then
        print_success "Successfully pulled $DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
    else
        print_warning "Failed to pull specific version, trying latest..."
        if docker pull $DOCKER_USERNAME/$IMAGE_NAME:$LATEST_TAG; then
            print_success "Successfully pulled $DOCKER_USERNAME/$IMAGE_NAME:$LATEST_TAG"
        else
            print_error "Failed to pull container. Please check your internet connection and Docker Hub access."
            exit 1
        fi
    fi
}

# Install required tools
install_tools() {
    print_status "Checking and installing required tools..."
    
    # Check for gdown
    if ! command -v gdown &> /dev/null; then
        print_status "Installing gdown..."
        pip install gdown
    else
        print_success "gdown is already installed"
    fi
    
    # Check for wget
    if ! command -v wget &> /dev/null; then
        print_status "Installing wget..."
        if command -v brew &> /dev/null; then
            brew install wget
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y wget
        elif command -v yum &> /dev/null; then
            sudo yum install -y wget
        else
            print_warning "Could not install wget automatically. Please install it manually."
        fi
    else
        print_success "wget is already installed"
    fi
    
    # Check for git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install Git first."
        exit 1
    else
        print_success "Git is already installed"
    fi
}

# Create directory structure
create_directories() {
    print_status "Creating directory structure..."
    
    mkdir -p input output weights/LLMs weights/PenCL weights/Facilitator weights/ProteoScribe
    
    print_success "Directory structure created"
}

# Download weights
download_weights() {
    print_status "Starting weights download..."
    
    # Check if weights already exist
    if [ -f "weights/PenCL/BioM3_PenCL_epoch20.bin" ] && \
       [ -f "weights/Facilitator/BioM3_Facilitator_epoch20.bin" ] && \
       [ -f "weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin" ]; then
        print_success "Weights already exist, skipping download"
        return 0
    fi
    
    # Function to check if file exists and has expected size
    check_file() {
        local file_path="$1"
        local expected_size="$2"
        
        if [ -f "$file_path" ]; then
            local actual_size=$(stat -f%z "$file_path" 2>/dev/null || stat -c%s "$file_path" 2>/dev/null || echo "0")
            if [ "$actual_size" -gt 1000000 ]; then  # File exists and is >1MB
                return 0
            fi
        fi
        return 1
    }
    
    # Download LLMs
    print_status "Downloading LLMs (ESM2 and PubMedBERT)..."
    cd weights/LLMs
    
    # ESM2 model weights
    if ! check_file "esm2_t33_650M_UR50D.pt" "2.4GB"; then
        print_status "Downloading ESM2 model weights (2.4GB)..."
        wget https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt
    else
        print_success "ESM2 model weights already exist"
    fi
    
    if ! check_file "esm2_t33_650M_UR50D-contact-regression.pt" "3.6KB"; then
        print_status "Downloading ESM2 contact regression weights..."
        wget https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t33_650M_UR50D-contact-regression.pt
    else
        print_success "ESM2 contact regression weights already exist"
    fi
    
    # PubMedBERT model
    if [ ! -d "BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext" ]; then
        print_status "Downloading PubMedBERT model..."
        git lfs install
        git clone https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext
    else
        print_success "PubMedBERT model already exists"
    fi
    
    # Download PenCL weights
    print_status "Downloading PenCL weights..."
    cd ../PenCL
    
    if ! check_file "BioM3_PenCL_epoch20.bin" "2.8GB"; then
        print_status "Downloading PenCL weights (2.8GB)..."
        gdown --id 1Lup7Xqwa1NjJpoM2uvvBAdghoM-fecEj -O BioM3_PenCL_epoch20.bin
    else
        print_success "PenCL weights already exist"
    fi
    
    # Download Facilitator weights
    print_status "Downloading Facilitator weights..."
    cd ../Facilitator
    
    if ! check_file "BioM3_Facilitator_epoch20.bin" "4MB"; then
        print_status "Downloading Facilitator weights..."
        gdown --id 1_YWwILXDkx9MSoSA1kfS-y0jk3Vy4HJE -O BioM3_Facilitator_epoch20.bin
    else
        print_success "Facilitator weights already exist"
    fi
    
    # Download ProteoScribe weights
    print_status "Downloading ProteoScribe weights..."
    cd ../ProteoScribe
    
    if ! check_file "BioM3_ProteoScribe_pfam_epoch20_v1.bin" "329MB"; then
        print_status "Downloading ProteoScribe weights (329MB)..."
        gdown --id 1c3CwvbOP_kp3FpLL1wPrjO6qtY-XiT26 -O BioM3_ProteoScribe_pfam_epoch20_v1.bin
    else
        print_success "ProteoScribe weights already exist"
    fi
    
    # Go back to original directory
    cd ../..
}

# Create example prompt file
create_example_prompt() {
    print_status "Creating example prompt file..."
    
    if [ ! -f "input/prompts.txt" ]; then
        cat > input/prompts.txt << 'EOF'
PROTEIN NAME: Translation initiation factor IF-1. FUNCTION: One of the essential components for the initiation of protein synthesis. Binds in the vicinity of the A-site. Stabilizes the binding of IF-2 and IF-3 on the 30S subunit to which N-formylmethionyl-tRNA(fMet) subsequently binds. Helps modulate mRNA selection, yielding the 30S pre-initiation complex (PIC). Upon addition of the 50S ribosomal subunit, IF-1, IF-2 and IF-3 are released leaving the mature 70S translation initiation complex.
EOF
        print_success "Created example prompt file at input/prompts.txt"
    else
        print_success "Prompt file already exists at input/prompts.txt"
    fi
}

# Verify setup
verify_setup() {
    print_status "Verifying setup..."
    
    local all_good=true
    
    # Check container
    if docker images | grep -q "$DOCKER_USERNAME/$IMAGE_NAME"; then
        print_success "✓ Docker container is available"
    else
        print_error "✗ Docker container not found"
        all_good=false
    fi
    
    # Check weights
    if [ -f "weights/PenCL/BioM3_PenCL_epoch20.bin" ]; then
        print_success "✓ PenCL weights found"
    else
        print_error "✗ PenCL weights missing"
        all_good=false
    fi
    
    if [ -f "weights/Facilitator/BioM3_Facilitator_epoch20.bin" ]; then
        print_success "✓ Facilitator weights found"
    else
        print_error "✗ Facilitator weights missing"
        all_good=false
    fi
    
    if [ -f "weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin" ]; then
        print_success "✓ ProteoScribe weights found"
    else
        print_error "✗ ProteoScribe weights missing"
        all_good=false
    fi
    
    if [ -f "weights/LLMs/esm2_t33_650M_UR50D.pt" ]; then
        print_success "✓ ESM2 weights found"
    else
        print_error "✗ ESM2 weights missing"
        all_good=false
    fi
    
    if [ -d "weights/LLMs/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext" ]; then
        print_success "✓ PubMedBERT model found"
    else
        print_error "✗ PubMedBERT model missing"
        all_good=false
    fi
    
    if [ "$all_good" = true ]; then
        print_success "All components verified successfully!"
    else
        print_error "Some components are missing. Please check the errors above."
        exit 1
    fi
}

# Show usage instructions
show_usage() {
    echo ""
    echo "=========================================="
    echo "BioM3 Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Your BioM3 environment is ready to use!"
    echo ""
    echo "To run BioM3:"
    echo "  docker run \\"
    echo "    -v \$(pwd)/input:/app/input \\"
    echo "    -v \$(pwd)/output:/app/output \\"
    echo "    -v \$(pwd)/weights:/app/weights \\"
    echo "    $DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
    echo ""
    echo "Or use the run script:"
    echo "  ./run_biom3.sh"
    echo ""
    echo "Directory structure:"
    echo "  input/          - Your protein prompts (prompts.txt)"
    echo "  output/         - Generated sequences and structures"
    echo "  weights/        - Model weights (downloaded automatically)"
    echo ""
    echo "For more information, see README.md"
}

# Main execution
main() {
    echo "Starting BioM3 setup..."
    echo ""
    
    check_docker
    pull_container
    install_tools
    create_directories
    download_weights
    create_example_prompt
    verify_setup
    show_usage
}

# Run main function
main "$@" 