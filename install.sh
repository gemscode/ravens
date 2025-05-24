#!/bin/bash
set -e

# Virtualenv aigenv
python3 -m venv aigenv
source aigenv/bin/activate

# Upgrade 
pip install --upgrade pip

# Requirements
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
elif [ -d dist ]; then
    pip install dist/*.tar.gz
fi
