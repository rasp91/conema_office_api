#!/bin/sh
#
# run_app.sh – activate venv and launch FastAPI via Uvicorn
#

###############################################################################
# 0. „Deaktivuj“ případné staré prostředí (sh nemá deactivate; jen varování)
###############################################################################
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Warning: another virtual environment is already active."
    echo "         It will remain active unless you started a fresh shell."
fi

###############################################################################
# 1. Přepni se do adresáře, kde leží tento skript
###############################################################################
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR" || exit 1

###############################################################################
# 2. Aktivuj (nebo vytvoř) virtuální prostředí
###############################################################################
if [ ! -f "venv/bin/activate" ]; then
    echo "Virtual environment not found – creating ./venv"
    python3 -m venv venv || {
        echo "Failed to create virtual environment"; exit 1; }
fi

. venv/bin/activate   # POSIX ekvivalent „source“

# 2.1 Ověř, že se aktivovalo
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtual environment is not activated. Exiting."; exit 1
fi

###############################################################################
# 3. Spusť Uvicorn
###############################################################################
exec uvicorn src.app:app --host 127.0.0.1 --port 8000 --reload
# (exec nahra