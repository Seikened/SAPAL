FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install "fastapi>=0.111" "uvicorn[standard]>=0.30"

# Contexto = ./backend, así que aquí está main.py, routers/, etc.
COPY . /app