# PowerShell script to activate virtual environment and run a FastAPI app using Uvicorn

# 1. Change directory to the folder where this script is located
Set-Location -Path $PSScriptRoot

# 2. Activate the virtual environment
& ".\venv\Scripts\activate"

# 3. Update Virtual Environment
python -m pip install --upgrade pip setuptools wheel

# 4. Install dependencies
python -m pip install -r requirements.txt
