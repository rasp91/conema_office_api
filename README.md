# FastAPI - Roechling Office API

Installation and operation on **Windows Server** with **IIS + HttpPlatformHandler**.

IIS starts and supervises the `uvicorn` process through the HttpPlatformHandler module and acts as a reverse proxy (HTTPS, hostname, logging).

The examples below use these paths. If yours differ, update them in `web.config` and `deploy_iis.ps1` as well:

| What | Path |
|---|---|
| Application (git checkout) | `E:\api\office_api` |
| Python | `E:\Python313\python.exe` |
| MSYS2 | `C:\msys64` |
| IIS App Pool | `rchl_office_api` |

---

## Installation

### 1. Prerequisites
- **Python 3.11+ (64-bit)**. During installation choose *Install for all users* and a custom location (e.g. `E:\Python313`). A per-user install under `AppData` is not accessible to the App Pool account.
- **Git for Windows**
- **IIS** with the *Web Server* and *Management Tools* roles (Server Manager → Add Roles and Features)
- **HttpPlatformHandler v1.2**: https://www.iis.net/downloads/microsoft/httpplatformhandler
- (optional) **URL Rewrite** for HTTP → HTTPS redirects

### 2. MSYS2 + Pango (required by WeasyPrint)
WeasyPrint, used for the guest book PDFs, needs the Pango (GTK) libraries, which on Windows are installed through MSYS2.

1. Download and install MSYS2 from https://www.msys2.org into `C:\msys64`.
2. Open the **MSYS2 MINGW64** console and install Pango:
   ```bash
   pacman -Syu        # if the console closes itself, reopen it and run the command again
   pacman -S mingw-w64-x86_64-pango
   ```
3. Check that `C:\msys64\mingw64\bin\libpango-1.0-0.dll` exists.

> Do **not** add `C:\msys64\mingw64\bin` to the system `PATH`. It would clash with other DLLs, and Python 3.8+ ignores `PATH` when loading DLLs anyway. WeasyPrint finds the libraries through the `WEASYPRINT_DLL_DIRECTORIES` environment variable, which `web.config` sets.

### 3. Get the application and dependencies
```powershell
git clone <repo-url> E:\api\office_api
cd E:\api\office_api
E:\Python313\python.exe -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\venv\Scripts\pip.exe install -r requirements.txt
```

Verify WeasyPrint:
```powershell
$env:WEASYPRINT_DLL_DIRECTORIES = "C:\msys64\mingw64\bin"
.\venv\Scripts\python.exe -m weasyprint --info
.\venv\Scripts\python.exe -c "from weasyprint import HTML; HTML(string='<p>Příliš žluťoučký kůň ✓</p>').write_pdf('test.pdf')"
```
Open `test.pdf` and check the Czech diacritics and the ✓ character, then delete the file.

### 4. Configure `.env`
```powershell
Copy-Item .env.template .env
```
Fill in the values. Set `ROOT_PATH` to the application root, e.g. `ROOT_PATH="E:\api\office_api"`. The `logs\` and `data\` folders are created there.

### 5. Database migrations
```powershell
.\venv\Scripts\python.exe alembic_validator.py
.\venv\Scripts\python.exe -m alembic upgrade head
```

### 6. `web.config`
```powershell
Copy-Item web.config.template web.config
```
Adjust the paths in `processPath`, `--app-dir`, `stdoutLogFile` and `WEASYPRINT_DLL_DIRECTORIES`. `web.config` is in `.gitignore`, so `git pull` never overwrites it.

> Keep `processesPerApplication` at `1`. The SharePoint sync lock lives in process memory only, so multiple processes could run the sync concurrently.

### 7. IIS – App Pool and site
Run as administrator:
```powershell
Import-Module WebAdministration

# Allow the handlers section in web.config (once per server)
& "$env:windir\system32\inetsrv\appcmd.exe" unlock config -section:system.webServer/handlers

# App Pool without .NET, always running, no idle shutdown
New-WebAppPool -Name "rchl_office_api"
Set-ItemProperty "IIS:\AppPools\rchl_office_api" -Name managedRuntimeVersion -Value ""
Set-ItemProperty "IIS:\AppPools\rchl_office_api" -Name startMode -Value "AlwaysRunning"
Set-ItemProperty "IIS:\AppPools\rchl_office_api" -Name processModel.idleTimeout -Value "00:00:00"

# Site (adjust port/hostname; add the HTTPS binding in IIS Manager)
New-Website -Name "rchl_office_api" -PhysicalPath "E:\api\office_api" -ApplicationPool "rchl_office_api" -Port 8005
```

### 8. Permissions for the App Pool account
The process runs as `IIS AppPool\rchl_office_api`. It needs read access to Python, the application and MSYS2, and write access to `logs` and `data`:
```powershell
$id = "IIS AppPool\rchl_office_api"
icacls "E:\Python313"           /grant "${id}:(OI)(CI)RX" /T
icacls "E:\api\office_api"      /grant "${id}:(OI)(CI)RX" /T
icacls "C:\msys64\mingw64"      /grant "${id}:(OI)(CI)RX" /T
icacls "E:\api\office_api\logs" /grant "${id}:(OI)(CI)M" /T
icacls "E:\api\office_api\data" /grant "${id}:(OI)(CI)M" /T
```

### 9. Verification
- `http://localhost:8005/docs` shows the Swagger UI.
- Register a test guest and download the PDF. The first PDF after startup can take longer while fontconfig builds its font cache from `C:\Windows\Fonts`.
- Logs: `E:\api\office_api\logs\app.*.log`, `global.log` and the process output `iis-stdout_*.log`.

### 10. SharePoint sync
Schedule `scripts\sync-sharepoint.ps1` in Task Scheduler with the site URL from step 7 (see the script header for details).

---

## Updating
```powershell
E:\api\office_api\deploy_iis.ps1
```
The script runs `git pull`, updates dependencies, verifies WeasyPrint, checks migrations and recycles the App Pool.

## Troubleshooting
| Error | Cause / fix |
|---|---|
| `OSError: cannot load library 'libgobject-2.0-0'` | WeasyPrint cannot find Pango: MSYS2/Pango is missing or `WEASYPRINT_DLL_DIRECTORIES` in `web.config` is wrong. |
| IIS `502.5` / `502.3` | The process failed to start. Check `logs\iis-stdout_*.log`; usually missing permissions (step 8) or a missing `.env`. |
| `.env config file not found` | `.env` must be in the application root next to `alembic.ini`. |
| Boxes instead of characters in the PDF | The font lacks the glyph. Change `font-family` in `src/v1/guest_book/form.py`, e.g. `"Segoe UI", "Segoe UI Symbol", sans-serif`. |
| `500.19` – config section locked | The `appcmd unlock` from step 7 was not run. |

---

## Local development (Windows)
```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\venv\Scripts\pip.exe install -r requirements.txt
uvicorn src.app:app --reload --host 0.0.0.0 --port 8005
```
PDF generation also needs MSYS2 + Pango locally (step 2) and `$env:WEASYPRINT_DLL_DIRECTORIES = "C:\msys64\mingw64\bin"` in the shell before starting uvicorn.
