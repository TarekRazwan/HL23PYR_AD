#!/usr/bin/env bash
set -euo pipefail
echo ">>> Creating conda env (hl23pyr) and installing NEURON/NetPyNE + tools"
if command -v conda >/dev/null 2>&1; then
  conda env create -f environment.yml || conda env update -f environment.yml
  echo "Activate with: conda activate hl23pyr"
else
  echo "[!] Conda not found. Falling back to pip (system env)."
  python3 -m pip install -r requirements.txt
fi
echo "Done."