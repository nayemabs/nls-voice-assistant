# Voice Assistant Docker Container
# Hybrid NLU with GLiNER + Faster-Whisper ASR
# Multi-platform support: CPU (any computer), CUDA GPU
# Note: Apple Silicon MPS only works natively (not in Docker)

# ============================================================
# Stage 1: Base image selection via build arg
# ============================================================
ARG BASE_IMAGE=python:3.11-slim
FROM ${BASE_IMAGE}

# Build arguments for configuration
ARG COMPUTE_TYPE=int8
ARG WHISPER_MODEL=small
ARG USE_HYBRID_NLU=true

# Set working directory
WORKDIR /app

# ============================================================
# Install system dependencies
# ============================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    portaudio19-dev \
    libsndfile1 \
    curl \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================
# Install Python dependencies
# ============================================================
COPY requirements.txt .

# Upgrade pip and install dependencies
# Install PyTorch CPU version explicitly for smaller image size
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================
# Download spaCy model
# ============================================================
RUN python -m spacy download en_core_web_sm

# ============================================================
# Copy application files
# ============================================================
COPY main.py .
COPY modules/ ./modules/
COPY tests/ ./tests/
COPY evaluate.py .
COPY test_audio_batch.py .

# Create directories for models and cache
RUN mkdir -p /app/logs /app/data \
    /root/.cache/huggingface \
    /root/.cache/torch \
    /root/.local/share/piper-tts

# ============================================================
# Pre-download models to speed up container startup
# ============================================================
# Pre-download Whisper model
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_MODEL}', device='cpu', compute_type='int8')" || true

# Pre-download GLiNER model (for hybrid NLU)
RUN python -c "from gliner import GLiNER; GLiNER.from_pretrained('urchade/gliner_medium-v2.1')" || true

# ============================================================
# Environment configuration
# ============================================================
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Whisper model configuration (can be overridden at runtime)
ENV WHISPER_MODEL_SIZE=${WHISPER_MODEL}
ENV WHISPER_COMPUTE_TYPE=${COMPUTE_TYPE}

# Default device (auto-detected at runtime)
ENV WHISPER_DEVICE=auto

# Hybrid NLU configuration
ENV USE_HYBRID_NLU=${USE_HYBRID_NLU}

# Hugging Face cache directory
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface

# ============================================================
# Healthcheck
# ============================================================
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "from modules.nlu import NLUModule; NLUModule(); print('OK')" || exit 1

# ============================================================
# Default command (text mode for Docker compatibility)
# ============================================================
CMD ["python", "main.py", "--text"]
