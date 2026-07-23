#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo
  echo "  Python 3 is not installed."
  echo "  Mac:   brew install python"
  echo "  Linux: sudo apt install python3 python3-pip"
  echo
  exit 1
fi

python3 run_local.py
