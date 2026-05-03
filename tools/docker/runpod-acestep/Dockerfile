# RunPod Serverless handler for ACE-Step 1.5 Music Generation (models baked in)
#
# Build: docker buildx build --platform linux/amd64 -t ghcr.io/conalmullan/video-toolkit-acestep:latest --push .
#
# Image size: ~20GB (includes ~10GB model weights: DiT turbo + LM 1.7B + VAE + embedding)
# Cold start: ~30-45s (no model download needed)
#
# GPU Requirements:
#   - Minimum: 16GB VRAM (turbo DiT + 1.7B LM)
#   - Optimal: 24GB VRAM (AMPERE_24 / ADA_24)

FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.12 and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    git-lfs \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN git lfs install

WORKDIR /app

# CUDA environment
ENV CUDA_HOME=/usr/local/cuda
ENV PATH="${CUDA_HOME}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}"

# Install PyTorch 2.10 with CUDA 12.8 support (matches ACE-Step requirements)
RUN pip3 install --no-cache-dir --break-system-packages \
    torch==2.10.0+cu128 \
    torchaudio==2.10.0+cu128 \
    torchvision==0.25.0+cu128 \
    --index-url https://download.pytorch.org/whl/cu128

# Install ACE-Step core dependencies
RUN pip3 install --no-cache-dir --break-system-packages \
    "transformers>=4.51.0,<4.58.0" \
    diffusers \
    "accelerate>=1.12.0" \
    "safetensors>=0.7.0" \
    "soundfile>=0.13.1" \
    "einops>=0.8.1" \
    "scipy>=1.10.1" \
    "vector-quantize-pytorch>=1.27.15" \
    "numba>=0.63.1" \
    "torchcodec>=0.9.1" \
    "torchao>=0.14.1,<0.16.0" \
    toml \
    "loguru>=0.7.3" \
    "peft>=0.18.0"

# Install RunPod SDK and utilities
RUN pip3 install --no-cache-dir --break-system-packages \
    "runpod>=1.7.0" \
    "requests>=2.31.0" \
    "boto3>=1.34.0" \
    "huggingface_hub>=0.25.0"

# Set HF cache location
ENV HF_HOME=/root/.cache/huggingface

# === CLONE ACE-STEP REPO ===
# We need the full package for the inference pipeline
RUN git clone --depth 1 https://github.com/ACE-Step/ACE-Step-1.5.git /app/acestep-repo

# Install nano-vllm (LM inference backend, bundled in repo)
RUN cd /app/acestep-repo/acestep/third_parts/nano-vllm && \
    pip3 install --no-cache-dir --break-system-packages --no-deps -e .

# Install ace-step as package (without its torch/cuda deps since we installed them above)
RUN cd /app/acestep-repo && pip3 install --no-cache-dir --break-system-packages --no-deps -e .

# === BAKE MODELS INTO IMAGE ===
# Download all required models during build

# DiT turbo model (~4.8GB)
RUN python3 -c "\
from huggingface_hub import snapshot_download; \
import os; \
os.makedirs('/root/.cache/huggingface', exist_ok=True); \
print('Downloading ACE-Step DiT turbo model...'); \
snapshot_download('ACE-Step/Ace-Step1.5', \
    allow_patterns=['acestep-v15-turbo/*', 'vae/*', 'config.json'], \
    cache_dir='/root/.cache/huggingface'); \
print('DiT turbo + VAE downloaded'); \
"

# LM 1.7B model (~3.7GB)
RUN python3 -c "\
from huggingface_hub import snapshot_download; \
print('Downloading ACE-Step LM 1.7B...'); \
snapshot_download('ACE-Step/Ace-Step1.5', \
    allow_patterns=['acestep-5Hz-lm-1.7B/*'], \
    cache_dir='/root/.cache/huggingface'); \
print('LM 1.7B downloaded'); \
"

# Embedding model (~1.2GB)
RUN python3 -c "\
from huggingface_hub import snapshot_download; \
print('Downloading Qwen3 Embedding 0.6B...'); \
snapshot_download('ACE-Step/Ace-Step1.5', \
    allow_patterns=['Qwen3-Embedding-0.6B/*'], \
    cache_dir='/root/.cache/huggingface'); \
print('Embedding model downloaded'); \
"

# Copy handler
COPY handler.py /app/handler.py

ENV PYTHONUNBUFFERED=1

# Configure ACE-Step for turbo mode
ENV ACESTEP_CONFIG_PATH=acestep-v15-turbo
ENV ACESTEP_LM_MODEL_PATH=acestep-5Hz-lm-1.7B
ENV ACESTEP_DEVICE=cuda
ENV ACESTEP_INIT_LLM=false

# Health check
RUN python3 -c "\
import torch; \
print(f'PyTorch {torch.__version__}, CUDA available: {torch.cuda.is_available()}'); \
print('ACE-Step handler ready'); \
"

CMD ["python3", "-u", "/app/handler.py"]
