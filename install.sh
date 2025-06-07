#!/bin/bash
set -e

# Step 1: Ensure .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env_sample" ]; then
        echo "Creating .env from .env_sample..."
        cp .env_sample .env
    else
        echo "❌ .env_sample not found. Cannot create .env."
        exit 1
    fi
fi

# Step 2: Create virtualenv if not present
if [ ! -d "aigenv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv aigenv
fi

# Step 3: Activate venv
source aigenv/bin/activate

# Step 4: Upgrade pip
pip install --upgrade pip

# Step 5: Install requirements
if [ -f requirements.txt ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
elif [ -d dist ]; then
    echo "Installing from dist..."
    pip install dist/*.tar.gz
else
    echo "❌ No requirements.txt or dist/*.tar.gz found"
    exit 1
fi

