#!/bin/sh

# 0. "Deaktivace" předchozího virtuálního prostředí – pouze symbolická
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Warning: Existing virtual environment detected (manual deactivation may be needed)"
    unset VIRTUAL_ENV
fi

# 1. Přepnutí do adresáře, kde je skript umístěn
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR" || exit 1

# 2. Aktivace virtuálního prostředí
if [ ! -f "venv/bin/activate" ]; then
    echo "Virtual environment not found at ./venv/bin/activate"
    exit 1
fi

. "venv/bin/activate"

# 2.1 Ověření, že se aktivovalo
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtual environment is not activated. Exiting script."
    exit 1
fi

# 3. Aktualizace pip, setuptools, wheel
python3 -m pip install --upgrade pip setuptools wheel

# 4. Instalace requirements.txt
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
else
    echo "requirements.txt not found!"
    exit 1
fi