# PowerShell script to activate virtual environment and run a FastAPI app using Uvicorn

# 0. Deactivate any currently activated virtual environment
if ($env:VIRTUAL_ENV) {
    & "$env:VIRTUAL_ENV\Scripts\deactivate"
}

# 1. Change directory to the folder where this script is located
Set-Location -Path $PSScriptRoot

# 2. Activate the virtual environment
& ".\venv\Scripts\activate"

# 2.1 Check if venv is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Error "Virtual environment is not activated. Exiting script."
    exit 1
}

# 3. Update Virtual Environment
python -m pip install --upgrade pip setuptools wheel

# 4. Install dependencies
python -m pip install -r requirements.txt
