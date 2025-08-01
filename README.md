# BioM3 Container

A containerized version of BioM3 (https://huggingface.co/niksapraljak1/BioM3), a multi-stage protein design pipeline that generates protein sequences from text descriptions (and optionally predicts their structures using third party tools like esmfold).

## Quick Start

### Prerequisites

- **Docker Desktop** installed on your machine
  - Download from: https://www.docker.com/products/docker-desktop/
  - For MacBook: Choose the appropriate version (Intel chip or Apple chip)

### Pull the Container

```bash
docker pull tnnandi/biom3-container:v1.0
```

### Prepare Your Files

1. **Create input directory and add your prompts:**
   ```bash
   mkdir -p input
   touch input/prompts.txt
   ```
   Enter your prompt (example available below) in prompts.txt

2. **Create output directory:**
   ```bash
   mkdir -p output
   ```

3. **Download model weights**
Before running models, you need to download the pre-trained weights. We provide comprehensive download instructions in a separate file to keep this README clean and focused.

**Quick start:**
```bash
# Install gdown for downloading
pip install gdown
# Install wget for downloading
brew install wget

# Download all weights at once
curl -O https://raw.githubusercontent.com/tnnandi/biom3_docker/master/download_weights.sh

chmod +x download_weights.sh
./download_weights.sh
```

For detailed instructions, troubleshooting, and individual component downloads, see [DOWNLOAD_WEIGHTS.md](DOWNLOAD_WEIGHTS.md).



### Run the Container

```bash
docker run \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/weights:/app/weights \
  tnnandi/biom3-container:v1.0
```

### Command Arguments

- `-v $(pwd)/input:/app/input`: Mounts your local `input/` directory to the container
- `-v $(pwd)/output:/app/output`: Mounts your local `output/` directory to the container  
- `-v $(pwd)/weights:/app/weights`: Mounts your local `weights/` directory to the container

## Input Format

Create a `prompts.txt` file in your `input/` directory with one protein description per line:

```
PROTEIN NAME: Translation initiation factor IF-1. FUNCTION: One of the essential components for the initiation of protein synthesis. Binds in the vicinity of the A-site. Stabilizes the binding of IF-2 and IF-3 on the 30S subunit to which N-formylmethionyl-tRNA(fMet) subsequently binds. Helps modulate mRNA selection, yielding the 30S pre-initiation complex (PIC). Upon addition of the 50S ribosomal subunit, IF-1, IF-2 and IF-3 are released leaving the mature 70S translation initiation complex.
```

## Output Files

After running, you'll find the following files in your local `output/` directory:

- `stage1_embeddings.json` (ignore)
- `stage2_embeddings.json` (ignore)  
- `stage3_sequences.json`: Generated protein sequences from Stage 3
- `structures_XXXX/`: Directory containing PDB structure files for each prompt
  - `structure_1.pdb`, `structure_2.pdb`, etc.: Predicted protein structures
  - `sequence_1.fasta`, `sequence_2.fasta`, etc.: Generated protein sequences

## MacBook Specific Instructions

```bash
# Add platform specification for compatibility
docker run --platform linux/amd64 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/weights:/app/weights \
  tnnandi/biom3-container:latest
```

## Troubleshooting
curl -O https://raw.githubusercontent.com/tnnandi/BioM3/main/download_weights.sh
### Common Issues

1. **"No such file or directory" errors**
   - Make sure you're running the command from the directory containing your `input/`, `output/`, and `weights/` folders

2. **Permission denied errors**
   - On MacBook, ensure Docker Desktop has permission to access your filesystem

3. **Container fails to start**
   - Check that Docker Desktop is running
   - Verify the container was pulled successfully: `docker images`

4. **Structure prediction fails**
   - The pipeline will still generate sequences even if structure prediction fails
   - Check the `output/` directory for generated sequences in FASTA format

### Check Container Status

```bash
# List running containers
docker ps

# View container logs
docker logs <container_id>

# Check if container exists
docker images | grep biom3-container
```

## Pipeline Stages

1. **Stage 1 (PenCL)**: Converts text descriptions to numerical embeddings
2. **Stage 2 (Facilitator)**: Transforms text embeddings to protein space
3. **Stage 3 (ProteoScribe)**: Generates protein sequences from facilitated embeddings
4. **Structure Prediction**: Predicts 3D protein structures using ESMFold

## Requirements

- **Input**: Text descriptions of proteins in the specified format
- **Weights**: Model weights directory (contact authors for access)
- **Output**: Local directory for saving results
- **Hardware**: CPU or GPU (GPU recommended for faster processing)

## NOTE: The structure prediction module is being fixed

