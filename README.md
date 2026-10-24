# Flask JSON serialization: Connexion 2 and 3

Standalone HTTP reproduction and verification kit for the `python-flask` generator
changes in [OpenAPI Generator PR #25376](https://github.com/OpenAPITools/openapi-generator/pull/25376).

The kit generates two applications from the same OpenAPI document, using the
templates in the generator checkout selected by the reviewer. It exercises the
generated models, serializer, and application entry point over real HTTP.
The serialization fix itself belongs in OpenAPI Generator; it is not copied here.

## Prerequisites

- An OpenAPI Generator checkout containing the changes under review, including
  the `useConnexion3` option and the JSON serialization fix.
- Java suitable for that generator checkout, and its built CLI JAR.
- Python 3.11 with `venv`, Bash, and access to PyPI for dependency installation.
- Free local ports 8082 and 8083.
- Optional: the VS Code REST Client extension for the `.http` files.

Build the CLI in the **generator checkout** if it is missing:

```bash
./mvnw package -DskipTests -Dmaven.javadoc.skip=true -Djacoco.skip=true
```

The CLI must support `useConnexion3`. Template changes are loaded directly from
the selected checkout with `-t`, so those changes do not require rebuilding an
otherwise compatible JAR.

## Generate and install

```bash
git clone https://github.com/Bernardoow/openapi-generator-flask-connexion-test.git
cd openapi-generator-flask-connexion-test

export OPENAPI_GENERATOR_DIR=/absolute/path/to/openapi-generator
./generate.sh all
PYTHON_BIN=python3.11 ./setup.sh all
```

With pyenv, an explicit interpreter avoids a shim selecting another version:

```bash
PYTHON_BIN="$(pyenv prefix 3.11.8)/bin/python" ./setup.sh all
```

Each generated application gets its own directory and virtual environment:

| Variant | Output | Pinned direct dependencies |
|---|---|---|
| Connexion 2 | `target/connexion2/` | Connexion 2.15.1, Flask 2.3.3 |
| Connexion 3 | `target/connexion3/` | Connexion 3.3.0, Flask 3.1.3 |

Other dependencies follow the generated requirements. Generated applications,
virtual environments, caches, and logs are ignored by Git.
Use `generate.sh 2` / `generate.sh 3` and `setup.sh 2` / `setup.sh 3` to prepare
one variant. Regenerate and restart the applications after changing templates.

The complete generation commands, from this repository, are:

```bash
java -jar "$OPENAPI_GENERATOR_DIR/modules/openapi-generator-cli/target/openapi-generator-cli.jar" generate \
  -g python-flask -i openapi.yaml -o target/connexion2 \
  -t "$OPENAPI_GENERATOR_DIR/modules/openapi-generator/src/main/resources/python-flask" \
  --additional-properties=useConnexion3=false,serverPort=8082

java -jar "$OPENAPI_GENERATOR_DIR/modules/openapi-generator-cli/target/openapi-generator-cli.jar" generate \
  -g python-flask -i openapi.yaml -o target/connexion3 \
  -t "$OPENAPI_GENERATOR_DIR/modules/openapi-generator/src/main/resources/python-flask" \
  --additional-properties=useConnexion3=true,serverPort=8083
```

## Run

From this repository, start one application in each of two terminals:

```bash
./run.sh 2
```

```bash
./run.sh 3
```

The scripts run the generated `python -m openapi_server` entry point.
`demo_controller.py` is kept outside the generated directories and selected with
`x-openapi-router-controller`, so regeneration preserves the implemented handlers.
Each process imports only its own generated application and the shared handler.

| Variant | Example response | Swagger UI |
|---|---|---|
| Connexion 2 | http://127.0.0.1:8082/api/demo/model | http://127.0.0.1:8082/api/ui/ |
| Connexion 3 | http://127.0.0.1:8083/api/demo/model | http://127.0.0.1:8083/api/ui/ |

Use `Ctrl+C` to stop each process. The `/api` prefix also avoids an unrelated
Connexion 2 Swagger UI URL-building issue with the root `/` base path.

## Call from VS Code

Open [connexion2.http](connexion2.http) and [connexion3.http](connexion3.http) in
[REST Client](https://github.com/Huachao/vscode-restclient#usage), then click
**Send Request** above each request. Comments describe the expected output.
Complete expected bodies are in [expected/connexion2.json](expected/connexion2.json)
and [expected/connexion3.json](expected/connexion3.json).

| Route, relative to `/api` | Coverage |
|---|---|
| `GET /demo/runtime` | Actual versions, active adapter, and `includeNulls` setting |
| `GET /demo/model` | Generated model, `display_name` to `displayName`, nested models, lists, maps, datetime, date, Decimal, UUID, and Unicode |
| `GET /demo/list` | A list containing a generated model |
| `GET /demo/map` | A dictionary containing a generated model |
| `GET /demo/nulls` | Omitted/included None values; preservation of false, zero, and empty strings |
| `GET /openapi.json` | The specification loaded by the application |
| `GET /ui/` | Swagger UI smoke check |

Handlers return generated models directly. They do not pre-serialize responses
with `jsonify`, `json.dumps`, or `to_dict`, so requests exercise the actual
Connexion JSON response path.

## Verify automatically

With both servers running, in a third terminal:

```bash
python3 verify.py
```

Expected: **14/14 checks passed**. The verifier uses only Python's standard
library. It checks HTTP status, Content-Type, complete JSON bodies for the five
demo routes, the OpenAPI document, and Swagger UI. It ignores object key order
and whitespace. Failures produce a diff and exit code 1.

For a single variant:

```bash
python3 verify.py --mode 2
python3 verify.py --mode 3
```

The `.http` files support interactive calls and inspection in VS Code;
`verify.py` supplies the automated assertions against the expected snapshots.

## Verify `include_nulls=True`

Stop both servers, then restart each in its own terminal:

```bash
./run.sh 2 --include-nulls
```

```bash
./run.sh 3 --include-nulls
```

Run:

```bash
python3 verify.py --include-nulls
```

Expected: **14/14 checks passed**. Missing `note`, `optionalLabel`, and nested
`comment` attributes now appear as `null`. The same `.http` requests work;
compare against the `withNulls` snapshots instead of `withoutNulls`.
The launcher sets the adapter's class attribute before calling the generated
`main()`. The setting applies to the whole process; requests do not mutate it.
Restart without the flag to restore the default behavior.

## Preserved format differences

| Python value | Connexion 2 | Connexion 3 |
|---|---|---|
| UTC datetime | `2024-04-05T06:07:08+00:00` | `Fri, 05 Apr 2024 06:07:08 GMT` |
| date | `2024-04-05` | `Fri, 05 Apr 2024 00:00:00 GMT` |
| `Decimal('12.50')` | `12.5` (number) | `"12.50"` (string) |
| UUID | UUID string | UUID string |

The OpenAPI document uses `date`, `date-time`, and `number` to generate
representative model types. Connexion 3's preserved date and Decimal output
does **not** satisfy those strict schema declarations. Response validation stays
at the generated application's default, disabled. This kit verifies serializer
behavior and explicitly exposes that existing compatibility limitation.
