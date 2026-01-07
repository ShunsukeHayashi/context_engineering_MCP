# Context Engineering MCP Platform - Multi-stage Docker Build
# Supports all three services: AI Guides, Context Engineering, and Workflow System

# ========================================
# Stage 1: Base Python Environment
# ========================================
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ========================================
# Stage 2: Node.js for MCP Server
# ========================================
FROM node:18-slim AS node-deps

WORKDIR /app/mcp-server
COPY mcp-server/package*.json ./
RUN npm ci --only=production

# ========================================
# Stage 3: Application Code
# ========================================
FROM base AS app

# Copy Node.js and MCP server
COPY --from=node-deps /usr/local/bin/node /usr/local/bin/
COPY --from=node-deps /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-deps /app/mcp-server/node_modules /app/mcp-server/node_modules

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs templates

# Create non-root user for security
RUN addgroup --system appgroup && \
    adduser --system --group appuser --home /app

# Set ownership
RUN chown -R appuser:appgroup /app
USER appuser

# ========================================
# Stage 4: Production Image
# ========================================
FROM app AS production

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_ENV=production \
    LOG_LEVEL=info \
    UVICORN_HOST=0.0.0.0

# Health check script
COPY --chown=appuser:appgroup <<EOF /app/healthcheck.py
#!/usr/bin/env python3
import sys
import requests
import subprocess
import time

def check_service(url, name):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {name} is healthy")
            return True
        else:
            print(f"❌ {name} returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        return False

def main():
    services = [
        ("http://localhost:8888/health", "AI Guides API"),
        ("http://localhost:9001/api/stats", "Context Engineering API"),
    ]
    
    all_healthy = True
    for url, name in services:
        if not check_service(url, name):
            all_healthy = False
    
    if all_healthy:
        print("🎉 All services are healthy")
        sys.exit(0)
    else:
        print("💥 Some services are unhealthy")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

RUN chmod +x /app/healthcheck.py

# Expose ports for all services
EXPOSE 8888 9001 9002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python /app/healthcheck.py

# Default command (can be overridden)
CMD ["python", "main.py"]