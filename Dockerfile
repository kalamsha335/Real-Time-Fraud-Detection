# Multi-stage production Dockerfile for Real-Time Fraud Detection Backend
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies including PostgreSQL client libraries and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python package dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application modules and model artifacts
COPY api/ /app/api/
COPY models/ /app/models/
COPY database/ /app/database/
COPY graph/ /app/graph/
COPY kafka/ /app/kafka/
COPY feature_store/ /app/feature_store/
COPY monitoring/ /app/monitoring/

# Create non-root system user for security best practices
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose FastAPI server port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

