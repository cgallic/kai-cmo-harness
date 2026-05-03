# RunPod Serverless handler for FLUX.2 Klein 4B (models baked in)
#
# Build: docker buildx build --platform linux/amd64 -t ghcr.io/conalmullan/video-toolkit-flux2:latest --push .
#
# Image size: ~15GB (includes ~8GB model weights)
# Cold start: ~30s (no model download needed)
#
# GPU Requirements:
#   - Minimum: 16GB VRAM (RTX 4070 Ti, A4000)
#   - Optimal: 24GB VRAM (RTX 4090, ADA_24)

FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    python3.11-dev \
    git \
    git-lfs \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

RUN git lfs install

WORKDIR /app

# CUDA environment
ENV CUDA_HOME=/usr/local/cuda
ENV PATH="${CUDA_HOME}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}"

# Install PyTorch with CUDA 12.4 support
RUN pip3 install --no-cache-dir \
    torch==2.5.1 \
    torchvision==0.20.1 \
    --index-url https://download.pytorch.org/whl/cu124

# Install diffusers from git (required for Flux2KleinPipeline)
RUN pip3 install --no-cache-dir git+https://github.com/huggingface/diffusers

# Install dependencies
RUN pip3 install --no-cache-dir \
    transformers>=4.45.0 \
    accelerate>=0.30.0 \
    safetensors>=0.4.0 \
    sentencepiece>=0.2.0 \
    protobuf>=4.25.0 \
    Pillow>=10.0.0 \
    numpy>=1.26.0

# Install RunPod SDK and utilities
RUN pip3 install --no-cache-dir \
    runpod>=1.7.0 \
    requests>=2.31.0 \
    boto3>=1.34.0 \
    huggingface_hub>=0.25.0

# Set HF cache location
ENV HF_HOME=/root/.cache/huggingface

# === BAKE MODEL INTO IMAGE ===
# Download FLUX.2 Klein 4B during build (~8GB)
RUN python3 -c "\
from huggingface_hub import snapshot_download; \
import os; \
os.makedirs('/root/.cache/huggingface', exist_ok=True); \
print('Downloading FLUX.2 Klein 4B model...'); \
snapshot_download('black-forest-labs/FLUX.2-klein-4B', cache_dir='/root/.cache/huggingface'); \
print('Model downloaded successfully'); \
"

# Copy handler
COPY handler.py /app/handler.py

ENV PYTHONUNBUFFERED=1

# Health check — verify torch and diffusers
RUN python3 -c "\
import torch; \
from diffusers import Flux2KleinPipeline; \
print(f'PyTorch {torch.__version__}, CUDA available: {torch.cuda.is_available()}'); \
print('Flux2KleinPipeline: available'); \
"

CMD ["python3", "-u", "/app/handler.py"]
