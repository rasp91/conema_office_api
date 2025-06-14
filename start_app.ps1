# PowerShell script to activate virtual environment and run a FastAPI app using Uvicorn

# 1. Change directory to the folder where this script is located
Set-Location -Path $PSScriptRoot

# 2. Activate the virtual environment
& ".\venv\Scripts\activate"

# 3. Run the Uvicorn server
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload