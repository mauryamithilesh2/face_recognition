# Use slim python base image
FROM python:3.11-slim

# Install minimal runtime libraries (avoid heavy build toolchain)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    liblapack3 \
    libx11-6 \
    curl \
    cmake \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Speed up pip and prefer wheels to avoid building from source (dlib)
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install python dependencies (prefer binary wheels)
RUN pip install --prefer-binary -r requirements.txt

# Copy the rest of the project
COPY . .

# Create staticfiles directory
RUN mkdir -p /app/staticfiles

# Make startup script executable
RUN chmod +x /app/start.sh

# Expose port (Railway will override this)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/healthz || exit 1

# Use startup script
CMD ["/app/start.sh"]
