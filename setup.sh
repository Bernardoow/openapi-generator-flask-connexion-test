#!/usr/bin/env bash
set -euo pipefail

kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${PYTHON_BIN:-python3.11}"
export PIP_CACHE_DIR="$kit_dir/target/pip-cache"
export PIP_DISABLE_PIP_VERSION_CHECK=1

if ! "$python_bin" -c 'import sys; assert sys.version_info[:2] == (3, 11)' 2>/dev/null; then
  echo 'Python 3.11 is required. Example with pyenv:' >&2
  echo 'PYTHON_BIN="$(pyenv prefix 3.11.8)/bin/python" ./setup.sh all' >&2
  exit 1
fi

setup() {
  local mode="$1" output="$kit_dir/target/connexion$1"
  if [[ ! -f "$output/requirements.txt" ]]; then
    echo "Generate the application first: $kit_dir/generate.sh $mode" >&2
    exit 1
  fi
  "$python_bin" -m venv "$output/.venv"
  "$output/.venv/bin/python" -m pip install \
    -c "$kit_dir/constraints-connexion$mode.txt" \
    -r "$output/requirements.txt" "$output"
}

case "${1:-all}" in
  2|3) setup "$1" ;;
  all) setup 2; setup 3 ;;
  *) echo "Usage: $0 [2|3|all]" >&2; exit 2 ;;
esac
