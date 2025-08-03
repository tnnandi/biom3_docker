# Use official Miniconda base image
FROM continuumio/miniconda3:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements_docker.txt .

# Install Python 3.10 and PyTorch 2.6+ via pip
RUN conda install python=3.10 -y && \
    pip install torch>=2.6.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies using pip
RUN pip3 install --no-cache-dir -r requirements_docker.txt

# Install fair-esm with specific version
RUN pip install fair-esm==2.0.0 --no-cache-dir

# Install openfold from GitHub (more reliable)
# RUN pip install git+https://github.com/aqlaboratory/openfold.git --no-cache-dir

# Copy BioM3 code
COPY BioM3/ ./BioM3/

 # Upgrade transformers to ensure compatibility with PyTorch 2.0.1
RUN pip3 install --no-cache-dir --upgrade transformers

# Downgrade transformers to a version known to be compatible with older models
# RUN pip3 install --no-cache-dir transformers==4.29.2

# Copy container scripts
COPY biom3_container.py .
# COPY esm_patch.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create input/output directories
RUN mkdir -p /app/input /app/output

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"] 