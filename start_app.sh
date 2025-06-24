#!/bin/sh

# 0. Deactivate any currently activated virtual environment (symbolic only)
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Warning: Existing virtual environment detected (manual deactivation may be needed)"
    unset VIRTUAL_ENV
fi

# 1. Change to the directory where this script is located
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR" || exit 1

# 2. Activate the virtual environment
if [ ! -f "venv/bin/activate" ]; then
    echo "Error: Virtual environment not found at ./venv/bin/activate"
    exit 1
fi

. venv/bin/activate

# 2.1 Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtual environment is not activated. Exiting script."
    exit 1
fi

# 3. Update pip, setuptools, wheel
python3 -m pip install --upgrade pip setuptools wheel

# 4. Install dependencies
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
else
    echo "requirements.txt not found!"
    exit 1
fi