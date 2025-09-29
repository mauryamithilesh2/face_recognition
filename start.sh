#!/bin/bash

# Exit on any error
set -e

# Create staticfiles directory if it doesn't exist
mkdir -p /app/staticfiles

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
exec gunicorn face_attendance.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
