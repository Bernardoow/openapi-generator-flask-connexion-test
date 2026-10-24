#!/usr/bin/env bash
set -euo pipefail

kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mode="${1:-}"
if [[ "$mode" != 2 && "$mode" != 3 ]] || [[ $# -gt 2 ]] || \
   [[ -n "${2:-}" && "${2:-}" != --include-nulls ]]; then
  echo "Usage: $0 {2|3} [--include-nulls]" >&2
  exit 2
fi
output="$kit_dir/target/connexion$mode"
python_bin="$output/.venv/bin/python"
if [[ ! -x "$python_bin" ]]; then
  echo "Prepare the environment first: $kit_dir/setup.sh $mode" >&2
  exit 1
fi

export PYTHONPATH="$output:$kit_dir"
cd "$output"
if [[ "${2:-}" == --include-nulls ]]; then
  adapter=JSONProvider
  if [[ "$mode" == 3 ]]; then adapter=JSONEncoder; fi
  exec "$python_bin" -c '
import sys
from openapi_server import encoder
from openapi_server.__main__ import main
getattr(encoder, sys.argv[1]).include_nulls = True
main()
' "$adapter"
fi
exec "$python_bin" -m openapi_server
