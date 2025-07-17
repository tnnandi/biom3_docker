# BioM3 Model Weights Download Instructions

This document provides comprehensive instructions for downloading all pre-trained model weights required to run the BioM3 pipeline.

## Prerequisites

Install `gdown` for downloading from Google Drive:
```bash
pip install gdown
```

## Model Components Overview

The BioM3 pipeline consists of four main components, each requiring specific pre-trained weights:

1. **LLMs** - ESM2 and PubMedBERT models for compiling PenCL
2. **PenCL** - Stage 1: Text-protein sequence alignment
3. **Facilitator** - Stage 2: Embedding facilitation
4. **ProteoScribe** - Stage 3: Protein sequence generation

## Detailed Download Instructions

Each component has its own README with specific instructions and usage examples:

### 1. LLMs (ESM2 and PubMedBERT)
- **Purpose**: Pre-trained weights for compiling PenCL model
- **Files**: ESM2 model weights and PubMedBERT model
- **Detailed Instructions**: [weights/LLMs/README.md](weights/LLMs/README.md)

**Quick download commands:**
```bash
cd weights/LLMs

# ESM2 model weights
wget https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt
wget https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t33_650M_UR50D-contact-regression.pt

# PubMedBERT model
git lfs install
git clone https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext
```

### 2. PenCL (Stage 1)
- **Purpose**: Text-protein sequence alignment model
- **File**: `BioM3_PenCL_epoch20.bin`
- **Detailed Instructions**: [weights/PenCL/README.md](weights/PenCL/README.md)

**Quick download command:**
```bash
cd weights/PenCL
gdown --id 1Lup7Xqwa1NjJpoM2uvvBAdghoM-fecEj -O BioM3_PenCL_epoch20.bin
```

### 3. Facilitator (Stage 2)
- **Purpose**: Facilitates alignment between text and protein embeddings
- **File**: `BioM3_Facilitator_epoch20.bin`
- **Detailed Instructions**: [weights/Facilitator/README.md](weights/Facilitator/README.md)

**Quick download command:**
```bash
cd weights/Facilitator
gdown --id 1_YWwILXDkx9MSoSA1kfS-y0jk3Vy4HJE -O BioM3_Facilitator_epoch20.bin
```

### 4. ProteoScribe (Stage 3)
- **Purpose**: Generates protein sequences from facilitated embeddings
- **File**: `BioM3_ProteoScribe_pfam_epoch20_v1.bin`
- **Detailed Instructions**: [weights/ProteoScribe/README.md](weights/ProteoScribe/README.md)

**Quick download command:**
```bash
cd weights/ProteoScribe
gdown --id 1c3CwvbOP_kp3FpLL1wPrjO6qtY-XiT26 -O BioM3_ProteoScribe_pfam_epoch20_v1.bin
```

## Complete Download Script

For convenience, you can run this script to download all weights at once:

```bash
#!/bin/bash
# Download all BioM3 model weights

# Install gdown if not already installed
pip install gdown

# Create weights directory structure
mkdir -p weights/LLMs weights/PenCL weights/Facilitator weights/ProteoScribe

# Download LLMs
cd weights/LLMs
echo "Downloading ESM2 model weights..."
wget https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt
wget https://dl.fbaipublicfiles.com/fair-esm/regression/esm2_t33_650M_UR50D-contact-regression.pt

echo "Downloading PubMedBERT model..."
git lfs install
git clone https://huggingface.co/microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext

# Download PenCL weights
cd ../PenCL
echo "Downloading PenCL weights..."
gdown --id 1Lup7Xqwa1NjJpoM2uvvBAdghoM-fecEj -O BioM3_PenCL_epoch20.bin

# Download Facilitator weights
cd ../Facilitator
echo "Downloading Facilitator weights..."
gdown --id 1_YWwILXDkx9MSoSA1kfS-y0jk3Vy4HJE -O BioM3_Facilitator_epoch20.bin

# Download ProteoScribe weights
cd ../ProteoScribe
echo "Downloading ProteoScribe weights..."
gdown --id 1c3CwvbOP_kp3FpLL1wPrjO6qtY-XiT26 -O BioM3_ProteoScribe_pfam_epoch20_v1.bin

echo "All weights downloaded successfully!"
```

Save this as `download_weights.sh` and run:
```bash
chmod +x download_weights.sh
./download_weights.sh
```

## Expected File Structure

After downloading all weights, your directory structure should look like this:

```
weights/
├── LLMs/
│   ├── esm2_t33_650M_UR50D.pt                    (~2.4GB)
│   ├── esm2_t33_650M_UR50D-contact-regression.pt (~3.6KB)
│   └── BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext/
│       ├── config.json
│       ├── pytorch_model.bin
│       ├── tokenizer.json
│       └── ...
├── PenCL/
│   └── BioM3_PenCL_epoch20.bin                   (~2.8GB)
├── Facilitator/
│   └── BioM3_Facilitator_epoch20.bin             (~4MB)
└── ProteoScribe/
    └── BioM3_ProteoScribe_pfam_epoch20_v1.bin    (~329MB)
```

## Verification

To verify that all weights have been downloaded correctly, check the file sizes:

```bash
# Check file sizes (approximate)
ls -lh weights/LLMs/esm2_t33_650M_UR50D.pt  # Should be ~2.4GB
ls -lh weights/PenCL/BioM3_PenCL_epoch20.bin  # Should be ~2.8GB
ls -lh weights/Facilitator/BioM3_Facilitator_epoch20.bin  # Should be ~4MB
ls -lh weights/ProteoScribe/BioM3_ProteoScribe_pfam_epoch20_v1.bin  # Should be ~329MB
```

## Troubleshooting

### Common Issues

1. **Download fails with gdown**
   - Try using `gdown --no-cookies`
   - Check your internet connection
   - Verify the Google Drive link is still active

2. **Git LFS issues**
   - Ensure `git-lfs` is installed: `git lfs install`
   - On some systems, you may need to install it separately: `apt-get install git-lfs` or `brew install git-lfs`

3. **Permission errors**
   - Make sure you have write permissions in the weights directory
   - Try running with `sudo` if necessary (though not recommended)

4. **Incomplete downloads**
   - Check file sizes against the expected sizes listed above
   - Re-download if files are significantly smaller than expected
   - Use `wget -c` to resume interrupted downloads

5. **Out of disk space**
   - Ensure you have at least 6GB of free space for all weights
   - Check available space with `df -h`

### Getting Help

If you encounter issues not covered here:

1. Check the individual README files in each weights subdirectory for component-specific troubleshooting
2. Open an issue in the BioM3 repository
3. Contact the BioM3 team at niksapraljak1@uchicago.edu

## Usage After Download

Once all weights are downloaded, you can:

1. **Run individual stages** - See the main [README.md](README.md) for stage-specific instructions
2. **Use the Docker container** - See the main README for container usage
3. **Load models programmatically** - See individual READMEs in weights subdirectories for code examples

## Citation

If you use these weights in your research, please cite:

```bibtex
Natural Language Prompts Guide the Design of Novel Functional Protein Sequences
bioRxiv 2024.11.11.622734
doi: https://doi.org/10.1101/2024.11.11.622734
```

---

**Note**: This document provides download instructions only. For detailed usage examples and model loading code, refer to the individual README files in each weights subdirectory. 