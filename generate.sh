#!/usr/bin/env bash
set -euo pipefail

kit_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${OPENAPI_GENERATOR_DIR:-}" || ! -d "$OPENAPI_GENERATOR_DIR" ]]; then
  echo 'Set OPENAPI_GENERATOR_DIR to the OpenAPI Generator checkout under review.' >&2
  echo 'Example: export OPENAPI_GENERATOR_DIR=/path/to/openapi-generator' >&2
  exit 1
fi
repo_dir="$(cd -- "$OPENAPI_GENERATOR_DIR" && pwd)"
cli_jar="$repo_dir/modules/openapi-generator-cli/target/openapi-generator-cli.jar"

if [[ ! -f "$cli_jar" ]]; then
  echo "Missing JAR: $cli_jar. Build it from the generator checkout:" >&2
  echo './mvnw package -DskipTests -Dmaven.javadoc.skip=true -Djacoco.skip=true' >&2
  exit 1
fi
if [[ ! -f "$repo_dir/modules/openapi-generator/src/main/resources/python-flask/encoder.mustache" ]]; then
  echo 'The selected checkout does not contain the python-flask templates.' >&2
  exit 1
fi

generate() {
  local mode="$1" use_connexion3=false port=8082
  if [[ "$mode" == 3 ]]; then
    use_connexion3=true
    port=8083
  fi
  java -jar "$cli_jar" generate \
    -g python-flask \
    -i "$kit_dir/openapi.yaml" \
    -o "$kit_dir/target/connexion$mode" \
    -t "$repo_dir/modules/openapi-generator/src/main/resources/python-flask" \
    --additional-properties="useConnexion3=$use_connexion3,serverPort=$port"
}

case "${1:-all}" in
  2|3) generate "$1" ;;
  all) generate 2; generate 3 ;;
  *) echo "Usage: $0 [2|3|all]" >&2; exit 2 ;;
esac
