#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source redcap_export/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python src/pipeline.py