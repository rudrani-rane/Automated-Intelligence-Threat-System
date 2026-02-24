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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install production WSGI server
RUN pip install --no-cache-dir uvicorn[standard] gunicorn

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 atis && \
    chown -R atis:atis /app
USER atis

# Expose port
EXPOSE 8000

# Health check — start-period covers GNN inference + 5-fold CV at boot (~90s)
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8000}/ || exit 1

# Railway injects $PORT; timeout=300 covers slow GNN startup under load
CMD gunicorn src.web.main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 300 \
    --access-logfile - \
    --error-logfile -
