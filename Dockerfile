# ================================================
# ATIS - Dockerfile for Production Deployment
# ================================================

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install CPU-only PyTorch first (avoids downloading the ~1.5GB CUDA build,
# which is useless on free-tier CPU servers like HF Spaces / Render).
# Use --extra-index-url so PyPI stays available for dependency resolution.
RUN pip install --no-cache-dir \
    torch==2.10.0+cpu \
    torchvision==0.25.0+cpu \
    torchaudio==2.10.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies (torch lines stripped so pip won't re-download CUDA build)
RUN grep -v -E '^(torch|torchvision|torchaudio)==' requirements.txt > /tmp/req_notorch.txt && \
    pip install --no-cache-dir -r /tmp/req_notorch.txt

# Install production WSGI server
RUN pip install --no-cache-dir 'uvicorn[standard]' gunicorn

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 atis && \
    chown -R atis:atis /app
USER atis

# Expose port
EXPOSE 8000

# HF Spaces uses port 7860 by default; override with PORT env var if needed
EXPOSE 7860

# Health check — start-period covers GNN inference + 5-fold CV at boot (~90s)
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:${PORT:-7860}/ || exit 1

# timeout=300 covers slow GNN startup; PORT defaults to 7860 for HF Spaces
CMD gunicorn src.web.main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-7860} \
    --timeout 300 \
    --access-logfile - \
    --error-logfile -
