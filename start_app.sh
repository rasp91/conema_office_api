#!/bin/bash

# 0. Deactivate any currently activated virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    deactivate
fi

# 1. Change to the directory where this script is located
cd "$(dirname "$0")" || exit 1

# 2. Activate the virtual environment
if [[ ! -f "venv/bin/activate" ]]; then
    echo "Virtual environment not found at ./venv/bin/activate"
    exit 1
fi
source venv/bin/activate

# 2.1 Check if venv is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Virtual environment is not activated. Exiting script."
    exit 1
fi

# 3. Run the Uvicorn server
uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload