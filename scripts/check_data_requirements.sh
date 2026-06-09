#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}

PYTHONPATH=backend ${PYTHON_CMD} backend/scripts/check_data_requirements.py
