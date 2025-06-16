# FastAPI - Roechling Office API

## Install VENV
```sh
    python -m venv venv
```

## Instal PIP + PAckages
```sh
    python -m pip install --upgrade pip
    pip install --upgrade setuptools wheel
    pip install --upgrade -r .\requirements.txt
```

## Start APP
```sh
    uvicorn main:app --reload --host 0.0.0.0 --port 8005
```

## Deploy
```sh
    sudo docker build --no-cache -t roechling-office-fastapi-app:latest .
```