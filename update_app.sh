#!/bin/bash

# 0. Deactivate any currently activated virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    deactivate
fi

# 1. Change to the directory where this script is located
cd "$(dirname "$0")" || exit 1

# # 2. Activate the virtual environment
# if [[ ! -f "venv/bin/activate" ]]; then
#     echo "Virtual environment not found at ./venv/bin/activate"
#     exit 1
# fi
# source venv/bin/activate

# # 2.1 Check if venv is activated
# if [[ -z "$VIRTUAL_ENV" ]]; then
#     echo "Virtual environment is not activated. Exiting script."
#     exit 1
# fi

# # 3. Update pip, setuptools, and wheel
# python -m pip install --upgrade pip setuptools wheel

# # 4. Install dependencies from requirements.txt
# if [[ -f "requirements.txt" ]]; then
#     python -m pip install -r requirements.txt
# else
#     echo "requirements.txt not found!"
#     exit 1
# fi