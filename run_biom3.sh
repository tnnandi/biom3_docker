#!/bin/bash

# BioM3 Run Script
# This script runs the BioM3 container with proper volume mounts

set -e  # Exit on any error

# Configuration
DOCKER_USERNAME="tnnandi"
IMAGE_NAME="biom3"
VERSION="v1.1"

# Default parameters
DIFFUSION_STEPS=1024
NUM_REPLICAS=1

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

# Check if required directories exist
check_directories() {
    print_status "Checking required directories..."
    
    if [ ! -d "input" ]; then
        print_error "Input directory not found. Please run setup_biom3.sh first."
        exit 1
    fi
    
    if [ ! -d "weights" ]; then
        print_error "Weights directory not found. Please run setup_biom3.sh first."
        exit 1
    fi
    
    if [ ! -d "output" ]; then
        print_status "Creating output directory..."
        mkdir -p output
    fi
    
    print_success "All directories are ready"
}

# Check if prompt file exists
check_prompt_file() {
    print_status "Checking prompt file..."
    
    if [ ! -f "input/prompts.txt" ]; then
        print_warning "No prompts.txt found in input directory."
        print_status "Creating example prompt file..."
        cat > input/prompts.txt << 'EOF'
PROTEIN NAME: Translation initiation factor IF-1. FUNCTION: One of the essential components for the initiation of protein synthesis. Binds in the vicinity of the A-site. Stabilizes the binding of IF-2 and IF-3 on the 30S subunit to which N-formylmethionyl-tRNA(fMet) subsequently binds. Helps modulate mRNA selection, yielding the 30S pre-initiation complex (PIC). Upon addition of the 50S ribosomal subunit, IF-1, IF-2 and IF-3 are released leaving the mature 70S translation initiation complex.
EOF
        print_success "Created example prompt file at input/prompts.txt"
        print_warning "Please edit input/prompts.txt with your own protein descriptions before running again."
        exit 1
    fi
    
    print_success "Prompt file found"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --diffusion_steps)
                DIFFUSION_STEPS="$2"
                shift 2
                ;;
            --num_replicas)
                NUM_REPLICAS="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help information
show_help() {
    echo "BioM3 Run Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --diffusion_steps N    Number of diffusion steps (default: 1024)"
    echo "  --num_replicas N       Number of replicas to generate (default: 5)"
    echo "  --help, -h            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use default parameters"
    echo "  $0 --diffusion_steps 512             # Use 512 diffusion steps"
    echo "  $0 --num_replicas 3                  # Generate 3 replicas"
    echo "  $0 --diffusion_steps 512 --num_replicas 3  # Both parameters"
    echo ""
}

# Check if Docker container exists
check_container() {
    print_status "Checking Docker container..."
    
    if ! docker images | grep -q "$DOCKER_USERNAME/$IMAGE_NAME"; then
        print_error "BioM3 container not found. Please run setup_biom3.sh first."
        exit 1
    fi
    
    print_success "Docker container is available"
}

# Run BioM3
run_biom3() {
    print_status "Starting BioM3 pipeline..."
    print_status "Parameters:"
    print_status "  - Diffusion steps: $DIFFUSION_STEPS"
    print_status "  - Number of replicas: $NUM_REPLICAS"
    echo ""
    
    # Get current directory
    CURRENT_DIR=$(pwd)
    
    # Run the container with environment variables
    docker run \
        -e DIFFUSION_STEPS="$DIFFUSION_STEPS" \
        -e NUM_REPLICAS="$NUM_REPLICAS" \
        -v "$CURRENT_DIR/input:/app/input" \
        -v "$CURRENT_DIR/output:/app/output" \
        -v "$CURRENT_DIR/weights:/app/weights" \
        "$DOCKER_USERNAME/$IMAGE_NAME:$VERSION"
    
    print_success "BioM3 pipeline completed!"
    echo ""
    print_status "Results are available in the output/ directory"
}

# Main execution
main() {
    echo "=========================================="
    echo "BioM3 Run Script"
    echo "=========================================="
    echo ""
    
    # Parse command line arguments
    parse_arguments "$@"
    
    check_directories
    check_prompt_file
    check_container
    run_biom3
}

# Run main function
main "$@" 