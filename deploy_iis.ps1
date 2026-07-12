#Requires -Version 5.1

<#
.SYNOPSIS
    Deploy Roechling Office API on IIS with HttpPlatformHandler.
.DESCRIPTION
    1. Pull latest code from git
    2. Create / update Python virtual environment
    3. Install pip dependencies
    4. Run Alembic validation and optionally migrate
    5. Optionally recycle IIS application pool
#>

# --- Configuration ------------------------------------------------------------
$AppPath     = "E:\\api\\office_api"
$VenvPath    = "$AppPath\\venv"
$Python      = "E:\\Python313\\python.exe"
$AppPoolName = "rchl_office_api"
# -----------------------------------------------------------------------------

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$msg)
    Write-Host "`n[STEP] $msg" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$msg)
    Write-Host "[OK]   $msg" -ForegroundColor Green
}

function Wait-ForExit {
    param([string]$prompt = "Press Enter to exit")
    [void](Read-Host $prompt)
}

function Abort {
    param([string]$msg)
    Write-Host "[FAIL] $msg" -ForegroundColor Red
    Wait-ForExit
    exit 1
}

# Validate config values before use (AppPoolName is used in elevated command)
if ($AppPoolName -notmatch '^[\w\-\.]+$') {
    Abort "AppPoolName '$AppPoolName' contains invalid characters."
}

# --- 1. Validate prerequisites ------------------------------------------------
Write-Step "Validating prerequisites"

foreach ($tool in @("git")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Abort "'$tool' is not installed or not in PATH."
    }
    Write-Ok "$tool  $((Get-Command $tool).Source)"
}

if (-not (Test-Path $Python)) {
    Abort "Configured Python executable not found: $Python"
}
Write-Ok "python $Python"

if (-not (Test-Path $AppPath)) {
    Abort "App path not found: $AppPath"
}

if (-not (Test-Path (Join-Path $AppPath "requirements.txt"))) {
    Abort "requirements.txt not found in $AppPath"
}
Write-Ok "requirements.txt found"

if (-not (Test-Path (Join-Path $AppPath "alembic_validator.py"))) {
    Abort "alembic_validator.py not found in $AppPath"
}
Write-Ok "alembic_validator.py found"

# --- 2. Pull latest code ------------------------------------------------------
Write-Step "Pulling latest code from Git"
Set-Location -Path $AppPath
git pull
if ($LASTEXITCODE -ne 0) {
    Abort "git pull failed (exit $LASTEXITCODE)."
}
Write-Ok "Git pull succeeded"

# --- 3. Create/update venv ----------------------------------------------------
Write-Step "Preparing virtual environment"
if (-not (Test-Path (Join-Path $VenvPath "Scripts\python.exe"))) {
    Write-Host "Creating venv at $VenvPath" -ForegroundColor Yellow
    & $Python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Abort "venv creation failed (exit $LASTEXITCODE)."
    }
    Write-Ok "Venv created"
} else {
    Write-Ok "Venv already exists"
}

$PipExe    = Join-Path $VenvPath "Scripts\pip.exe"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $PipExe) -or -not (Test-Path $PythonExe)) {
    Abort "Venv appears incomplete (missing pip.exe or python.exe)."
}

# --- 4. Install dependencies --------------------------------------------------
Write-Step "Installing dependencies"

& $PipExe install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Abort "pip self-upgrade failed (exit $LASTEXITCODE)."
}

& $PipExe install --upgrade setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Abort "setuptools/wheel upgrade failed (exit $LASTEXITCODE)."
}

& $PipExe install --upgrade -r (Join-Path $AppPath "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Abort "requirements installation failed (exit $LASTEXITCODE)."
}
Write-Ok "Dependencies installed"

# --- 5. Alembic validation ----------------------------------------------------
Write-Step "Running Alembic validation"
& $PythonExe (Join-Path $AppPath "alembic_validator.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "Schema drift detected." -ForegroundColor Yellow
    $applyMigrations = Read-Host "Apply latest migration now? (y/N)"

    if ($applyMigrations -match '^[Yy]$') {
        & $PythonExe -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) {
            Abort "Alembic migration failed (exit $LASTEXITCODE)."
        }
        Write-Ok "Migrations applied"
    } else {
        Abort "Migrations skipped - deployment aborted."
    }
} else {
    Write-Ok "Schema is up to date"
}

# --- 6. Optional IIS app pool recycle ----------------------------------------
Write-Host ""
$confirmRecycle = Read-Host "Recycle IIS App Pool '$AppPoolName'? (y/N)"

if ($confirmRecycle -match '^[Yy]$') {
    Write-Step "Recycling IIS Application Pool '$AppPoolName'"
    Write-Host "A UAC prompt may appear to elevate recycle command." -ForegroundColor DarkGray

    $recycleCmd = "Import-Module WebAdministration; " +
                  "`$pool = Get-Item 'IIS:\AppPools\$AppPoolName' -ErrorAction SilentlyContinue; " +
                  "if (`$null -eq `$pool) { Write-Host 'FAIL: App Pool $AppPoolName not found.' -ForegroundColor Red; exit 1 }; " +
                  "if (`$pool.State -eq 'Stopped') { Start-WebAppPool -Name '$AppPoolName' } else { Restart-WebAppPool -Name '$AppPoolName' }; " +
                  "Write-Host 'OK: App Pool $AppPoolName recycled.' -ForegroundColor Green"

    $proc = Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoProfile", "-Command", $recycleCmd `
        -Verb RunAs `
        -Wait `
        -PassThru

    if ($proc.ExitCode -ne 0) {
        Abort "App Pool recycle failed or UAC was cancelled (exit $($proc.ExitCode))."
    }

    Write-Ok "Application Pool '$AppPoolName' recycled"
} else {
    Write-Host "IIS recycle skipped." -ForegroundColor DarkGray
}

# --- Done ---------------------------------------------------------------------
Write-Host ""
Write-Host "Deployment complete." -ForegroundColor Green
Wait-ForExit
