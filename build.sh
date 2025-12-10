#!/usr/bin/env bash
# Build script for Render

# Install dependencies
pip install -r requirements.txt

# Collect static files
cd mysite
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput