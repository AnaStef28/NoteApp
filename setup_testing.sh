#!/bin/bash
# Setup script for testing environment

set -e

echo "Setting up testing environment for AI Notes..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Run tests
echo "Running tests..."
pytest

echo "Setup complete!"

