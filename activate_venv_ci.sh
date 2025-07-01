#!/bin/bash

set -e
 echo "Python version:"
python3 --version

echo "Creating virtual environment at $VENV_DIR"
python3 -m venv "$VENV_DIR"

echo "Activating virtual environment"
source "$VENV_DIR/bin/activate"

echo "Ensuring pip cache directory exists: $PIP_CACHE_DIR"
mkdir -p "$PIP_CACHE_DIR"

echo "Upgrading pip"
python3 -m pip install --upgrade pip

echo "Installing requirements using pip cache"
pip install --cache-dir="$PIP_CACHE_DIR" -r requirements.txt

echo "Installing Playwright"
python3 -m playwright install
