#!/usr/bin/env bash
set -euo pipefail

source redcap_export/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python pipeline.py