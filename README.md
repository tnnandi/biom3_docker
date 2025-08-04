# BioM3 User Guide

This guide will help you set up and run [BioM3](https://huggingface.co/niksapraljak1/BioM3) , a multi-stage protein design pipeline that generates protein sequences from text descriptions.

## Quick Start

### 1. Prerequisites

- **Docker Desktop** installed on your machine
  - Download from: https://www.docker.com/products/docker-desktop/
  - For MacBook: Choose the appropriate version (Intel chip or Apple chip)

### 2. One-Command Setup

Run the setup script to automatically:
- Pull the BioM3 Docker container
- Download all required model weights (~5.5GB total)
- Create necessary directories
- Set up an example prompt file

```bash
# Download the setup script
curl -O https://raw.githubusercontent.com/tnnandi/biom3/master/setup_biom3.sh

# Make it executable
chmod +x setup_biom3.sh

# Run the setup
./setup_biom3.sh
```

### 3. Run BioM3 (Option 1: using command line)

After setup is complete, run BioM3 with:

```bash
# Download the run script
curl -O https://raw.githubusercontent.com/tnnandi/biom3/master/run_biom3.sh

# Make it executable
chmod +x run_biom3.sh

# Run BioM3

## Option 1: Command Line Interface

```bash
# Run BioM3 with default parameters
./run_biom3.sh

# Or with custom parameters
./run_biom3.sh --diffusion_steps 512 --num_replicas 3

# Show help for all options
./run_biom3.sh --help
```

## Run BioM3 (Option 2: Using GUI (Recommended))

For a user-friendly GUI experience:

```bash
# Download the GUI launcher
curl -O https://raw.githubusercontent.com/tnnandi/biom3/master/run_gui.sh
curl -O https://raw.githubusercontent.com/tnnandi/biom3/master/biom3_gui.py

# Make it executable
chmod +x run_gui.sh

# Launch the GUI
./run_gui.sh
```

The GUI provides:
- **Setup Tab**: Download container and weights with progress tracking
- **Configuration Tab**: Set diffusion steps and number of replicas
- **Run Tab**: Enter protein descriptions and run the pipeline
- **Results Tab**: View generated sequences and open output folder
```

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Pull the Container

```bash
docker pull tnnandi/biom3:v1.1
```

### 2. Create Directories

```bash
mkdir -p input output weights/LLMs weights/PenCL weights/Facilitator weights/ProteoScribe
```

### 3. Download Weights

```bash
# Install required tools
pip install gdown
brew install wget  # On macOS
# sudo apt-get install wget  # On Ubuntu/Debian

# Download weights
curl -O https://raw.githubusercontent.com/tnnandi/biom3/master/download_weights.sh
chmod +x download_weights.sh
./download_weights.sh
```

### 4. Create Input File

Create `input/prompts.txt` with your protein descriptions:

```
PROTEIN NAME: Translation initiation factor IF-1. FUNCTION: One of the essential components for the initiation of protein synthesis. Binds in the vicinity of the A-site. Stabilizes the binding of IF-2 and IF-3 on the 30S subunit to which N-formylmethionyl-tRNA(fMet) subsequently binds. Helps modulate mRNA selection, yielding the 30S pre-initiation complex (PIC). Upon addition of the 50S ribosomal subunit, IF-1, IF-2 and IF-3 are released leaving the mature 70S translation initiation complex.
```

### 5. Run BioM3

```bash
docker run \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/weights:/app/weights \
  tnnandi/biom3:v1.1
```

## Input Format

Create a `prompts.txt` file in your `input/` directory with one protein description per line:

```
PROTEIN NAME: [Protein Name]. FUNCTION: [Detailed description of protein function, structure, and properties].
```

### Example Prompts

```
PROTEIN NAME: Green fluorescent protein. FUNCTION: A protein that exhibits bright green fluorescence when exposed to light in the blue to ultraviolet range. The protein has a beta-barrel structure with 11 beta strands and an alpha helix running through the center. The chromophore is formed by autocatalytic cyclization and oxidation of three amino acids.

PROTEIN NAME: Insulin. FUNCTION: A peptide hormone that regulates glucose metabolism. It consists of two polypeptide chains (A and B) linked by disulfide bonds. The A chain has 21 amino acids and the B chain has 30 amino acids. It promotes glucose uptake by cells and inhibits glucose production in the liver.
```

## Output Files

After running, you'll find the following files in your `output/` directory:

- `stage1_embeddings.json` - Text and protein embeddings from Stage 1
- `stage2_embeddings.json` - Facilitated embeddings from Stage 2  
- `stage3_sequences.json` - Generated protein sequences from Stage 3
- `structures_XXXX/` - Directory containing PDB structure files for each prompt
  - `structure_1.pdb`, `structure_2.pdb`, etc. - Predicted protein structures
  - `sequence_1.fasta`, `sequence_2.fasta`, etc. - Generated protein sequences

## Environment Variables

You can customize the pipeline by setting environment variables:

```bash
# Set number of diffusion steps (default: 1024)
export DIFFUSION_STEPS=512

# Set number of replicas to generate (default: 5)
export NUM_REPLICAS=3

# Run with custom parameters
docker run \
  -e DIFFUSION_STEPS=512 \
  -e NUM_REPLICAS=3 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/weights:/app/weights \
  tnnandi/biom3:v1.1
```

## Troubleshooting

### Common Issues

1. **Docker not running**
   ```
   Error: Docker is not running. Please start Docker Desktop first.
   ```
   Solution: Start Docker Desktop

2. **Weights download failed**
   ```
   Error: Failed to download weights
   ```
   Solution: Check internet connection and try again. The weights are large (~5.5GB total).

3. **Permission denied**
   ```
   Error: Permission denied
   ```
   Solution: Make scripts executable with `chmod +x script_name.sh`

4. **Container not found**
   ```
   Error: BioM3 container not found
   ```
   Solution: Run `./setup_biom3.sh` to pull the container

### MacBook Specific Issues

For Apple Silicon Macs, you may need to specify the platform:

```bash
docker run --platform linux/amd64 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/weights:/app/weights \
  tnnandi/biom3:v1.1
```

### Disk Space

Ensure you have at least 10GB of free disk space for:
- Docker container (~2GB)
- Model weights (~5.5GB)
- Output files (~1-2GB)

## Advanced Usage

### Custom Configuration

You can modify the pipeline by editing the configuration files in the container:

```bash
# Enter the container interactively
docker run -it \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/weights:/app/weights \
  tnnandi/biom3:v1.1 /bin/bash
```

### Running Multiple Prompts

Add multiple protein descriptions to `input/prompts.txt`, one per line:

```
PROTEIN NAME: Protein A. FUNCTION: Description A.
PROTEIN NAME: Protein B. FUNCTION: Description B.
PROTEIN NAME: Protein C. FUNCTION: Description C.
```

### Monitoring Progress

The pipeline shows progress for each stage:
- Stage 1: PenCL - Text and protein embedding generation
- Stage 2: Facilitator - Embedding facilitation
- Stage 3: ProteoScribe - Sequence generation
- Structure prediction (optional)

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the logs in the output directory
- Open an issue on the GitHub repository

## File Structure

After setup, your directory should look like:

```
your_project/
├── input/
│   └── prompts.txt          # Your protein descriptions
├── output/                  # Generated results
├── weights/
│   ├── LLMs/               # ESM2 and PubMedBERT models
│   ├── PenCL/              # PenCL model weights
│   ├── Facilitator/        # Facilitator model weights
│   └── ProteoScribe/       # ProteoScribe model weights
├── setup_biom3.sh          # Setup script
└── run_biom3.sh           # Run script
``` 