<#
.SYNOPSIS
    Triggers a SharePoint articles sync (POST /kiosk/sharepoint/sync) and logs the result.
    Intended to be run periodically via Windows Task Scheduler.

.PARAMETER ApiBaseUrl
    Base URL of the running roechling_office_api instance. Adjust for your deployment
    (e.g. "http://127.0.0.1:8005" for the documented dev port, or the production URL).

.EXAMPLE
    powershell.exe -ExecutionPolicy Bypass -File sync-sharepoint.ps1 -ApiBaseUrl "http://127.0.0.1:8005"

.EXAMPLE
    Absolute path with a custom (e.g. production) API base URL - use this form in Task Scheduler,
    since the task's working directory won't be this script's folder:

    powershell.exe -ExecutionPolicy Bypass -File "D:\Python\roechling_office_api\scripts\sync-sharepoint.ps1" -ApiBaseUrl "https://your-production-url"

    In Task Scheduler's action, split this as:
      Program/script:  powershell.exe
      Add arguments:   -ExecutionPolicy Bypass -File "D:\Python\roechling_office_api\scripts\sync-sharepoint.ps1" -ApiBaseUrl "https://your-production-url"
#>

param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8005"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "sharepoint-sync.log"
$MaxLogSizeBytes = 10MB
$MaxArchives = 5

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log([string]$Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$timestamp | $Message" -Encoding utf8
}

# Rotate: archive the current log with a timestamp suffix once it crosses the size
# threshold, then prune archives beyond $MaxArchives - mirrors the app's own daily
# TimedRotatingFileHandler(backupCount=5) convention in src/logger.py, just size-triggered.
function Rotate-LogIfNeeded {
    if (-not (Test-Path $LogFile)) { return }
    if ((Get-Item $LogFile).Length -lt $MaxLogSizeBytes) { return }

    $archiveName = "sharepoint-sync.{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss")
    Move-Item -Path $LogFile -Destination (Join-Path $LogDir $archiveName) -Force

    $archives = Get-ChildItem -Path $LogDir -Filter "sharepoint-sync.*.log" | Sort-Object LastWriteTime -Descending
    if ($archives.Count -gt $MaxArchives) {
        $archives | Select-Object -Skip $MaxArchives | Remove-Item -Force
    }
}

function Get-EnvValue([string]$Name) {
    if (-not (Test-Path $EnvFile)) {
        throw "Could not find .env at $EnvFile to read $Name"
    }
    $line = Select-String -Path $EnvFile -Pattern "^$Name\s*=" | Select-Object -First 1
    if (-not $line) {
        throw "$Name not found in $EnvFile"
    }
    return ($line.Line -split '=', 2)[1].Trim().Trim('"')
}

try {
    Rotate-LogIfNeeded
} catch {
    Write-Log "ERROR - log rotation failed: $($_.Exception.Message)"
}

try {
    $apiKey = Get-EnvValue "API_KEY"
    $syncKey = Get-EnvValue "SP_SYNC_KEY"
    $uri = "$ApiBaseUrl/kiosk/sharepoint/sync"
    $response = Invoke-RestMethod -Method Post -Uri $uri -Headers @{ "API-KEY" = $apiKey; "SYNC-KEY" = $syncKey } -TimeoutSec 120
    Write-Log "OK - synced $($response.synced) articles"
    exit 0
} catch {
    Write-Log "ERROR - $($_.Exception.Message)"
    exit 1
}
