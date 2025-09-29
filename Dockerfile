# Use slim python base image
FROM python:3.12-slim

# Install system dependencies required by dlib & face-recognition
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    make \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

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
