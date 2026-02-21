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
    libpq-dev \
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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')"

# Production command with Gunicorn + Uvicorn workers
CMD ["gunicorn", "src.web.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
