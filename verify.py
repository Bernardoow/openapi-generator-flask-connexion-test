#!/usr/bin/env python3
"""Verify real HTTP responses using only the Python standard library."""

import argparse
import difflib
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


KIT_DIR = Path(__file__).resolve().parent


def fetch(base_url, path, content_type='application/json'):
    with urlopen(base_url.rstrip('/') + path, timeout=5) as response:
        if response.status != 200:
            raise AssertionError(f'HTTP {response.status}, expected 200')
        actual_type = response.headers.get_content_type()
        if actual_type != content_type:
            raise AssertionError(f'Content-Type {actual_type}, expected {content_type}')
        body = response.read().decode('utf-8')
        return json.loads(body) if content_type == 'application/json' else body


def assert_equal(actual, expected):
    expected_lines = json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False).splitlines()
    actual_lines = json.dumps(actual, indent=2, sort_keys=True, ensure_ascii=False).splitlines()
    if actual_lines != expected_lines:
        difference = '\n'.join(difflib.unified_diff(
            expected_lines, actual_lines, fromfile='expected', tofile='actual', lineterm='',
        ))
        raise AssertionError(difference)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['2', '3', 'both'], default='both')
    parser.add_argument('--include-nulls', action='store_true')
    parser.add_argument('--url2', default='http://127.0.0.1:8082/api')
    parser.add_argument('--url3', default='http://127.0.0.1:8083/api')
    args = parser.parse_args()
    modes = ['2', '3'] if args.mode == 'both' else [args.mode]
    failures = 0
    checks = 0
    for mode in modes:
        base_url = getattr(args, f'url{mode}')
        snapshots = json.loads((KIT_DIR / 'expected' / f'connexion{mode}.json').read_text())
        expected = snapshots['withNulls' if args.include_nulls else 'withoutNulls']
        runtime = {
            'connexionVersion': '2.15.1' if mode == '2' else '3.3.0',
            'flaskVersion': '2.3.3' if mode == '2' else '3.1.3',
            'adapter': 'JSONProvider' if mode == '2' else 'JSONEncoder',
            'includeNulls': args.include_nulls,
        }
        routes = {
            '/demo/runtime': runtime,
            '/demo/model': expected['model'],
            '/demo/list': [expected['model']],
            '/demo/map': {'primary': expected['model']},
            '/demo/nulls': expected['nulls'],
        }
        for path, body in routes.items():
            checks += 1
            try:
                assert_equal(fetch(base_url, path), body)
                print(f'PASS C{mode} GET {path}')
            except (AssertionError, HTTPError, URLError, OSError, ValueError) as error:
                failures += 1
                print(f'FAIL C{mode} GET {path}: {error}', file=sys.stderr)
                if path == '/demo/runtime':
                    print(f'Check ./run.sh {mode} and the --include-nulls mode.', file=sys.stderr)
                    break
        else:
            for path, content_type in [('/openapi.json', 'application/json'), ('/ui/', 'text/html')]:
                checks += 1
                try:
                    body = fetch(base_url, path, content_type)
                    if path == '/openapi.json':
                        if not body.get('openapi', '').startswith('3.0.') or '/demo/model' not in body.get('paths', {}):
                            raise AssertionError('The loaded OpenAPI document does not match this kit')
                    elif 'swagger-ui' not in body:
                        raise AssertionError('The HTML does not contain Swagger UI')
                    print(f'PASS C{mode} GET {path}')
                except (AssertionError, HTTPError, URLError, OSError, ValueError) as error:
                    failures += 1
                    print(f'FAIL C{mode} GET {path}: {error}', file=sys.stderr)
    print(f'{checks - failures}/{checks} checks passed; include_nulls={args.include_nulls}.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
