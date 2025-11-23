#!/bin/bash
set -euo pipefail

python3 kill_port.py || true
poetry run uvicorn app.main:app --reload --port 8000
