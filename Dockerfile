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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Run migrations and collectstatic on container startup
CMD python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    gunicorn face_attendance.wsgi:application --bind 0.0.0.0:8000
