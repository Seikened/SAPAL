#!/usr/bin/env bash
set -euo pipefail
uv run uvicorn backend.main:app --reload --port 8000
