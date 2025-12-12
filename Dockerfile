# Multi-stage Docker build for Smart Bandwidth Monitor

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies
RUN uv pip install --system --no-cache -e .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (including tools for network monitoring)
RUN apt-get update && apt-get install -y \
    libpcap0.8 \
    libpcap-dev \
    iptables \
    iproute2 \
    tcpdump \
    net-tools \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY pyproject.toml ./

# Create required directories with proper permissions
# Use chmod -R to ensure all files and subdirectories have correct permissions
RUN mkdir -p logs data static && \
    chmod -R 777 logs data static && \
    touch logs/.gitkeep data/.gitkeep static/.gitkeep

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENABLE_MONITORING=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with proper network capabilities
# Note: Container must run with NET_ADMIN and NET_RAW capabilities
# Create logs directory if mounted volume doesn't exist
CMD ["sh", "-c", "mkdir -p logs data static && chmod -R 777 logs data static && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"]
