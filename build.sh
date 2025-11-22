#!/bin/bash
set -e

# Install system dependencies for Render
apt-get update
apt-get install -y --no-install-recommends \
    chromium-browser \
    chromium-driver

# Install Python dependencies
pip install -r requirements.txt
