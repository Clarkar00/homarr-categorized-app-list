#!/usr/bin/env python3
"""Small static public-manifest guardrail, not a complete secret scanner.

No network access or dependencies. Review provenance and content manually too.
Checks structure, public defaults, auth configuration, common private IPv4/hosts,
and obvious token prefixes. Does not decode obfuscated content, resolve DNS, or
cover IPv6, arbitrary credentials, or every sensitive identifier. Host-like
localhost references are rejected; explanatory prose may mention localhost.

Usage: python3 scripts/check_public.py [manifest.json] (default: repo/widget.json).
Optional CHECK_PUBLIC_PRIVATE_PATTERNS contains newline-separated, case-insensitive
literal substrings. CHECK_PUBLIC_PRIVATE_PATTERNS_FILE adds UTF-8 lines from a
file OUTSIDE this repository (resolved paths, including symlinks, are checked).
Blank lines are ignored; do not put deployment-specific patterns in this repo
or CI. Failures never echo input values, patterns, or file paths.
"""
import ipaddress
import json
import os
import re
from pathlib import Path
import sys


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'widget.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('$schema') != 'homarr-custom-widget-v2':
        return 1
    for key, kind in [('name', str), ('sources', dict), ('requests', dict),
                      ('options', dict), ('template', str)]:
        if not isinstance(data.get(key), kind):
            return 1
    if not data['template'].strip():
        return 1
    source = data['sources'].get('default')
    overrides = data['options'].get('containerOverrides')
    if not isinstance(source, dict) or source.get('baseUrl') != 'https://homarr.example.com':
        return 1
    if not isinstance(overrides, dict) or overrides.get('default') != '':
        return 1
    for source in data['sources'].values():
        if not isinstance(source, dict):
            return 1
        if 'auth' in source:
            auth = source['auth']
            if not isinstance(auth, dict) or set(auth) != {'type', 'name'}:
                return 1
            if not all(isinstance(value, str) and value.strip() for value in auth.values()):
                return 1
    text = json.dumps(data, ensure_ascii=False)
    networks = [ipaddress.IPv4Network(cidr) for cidr in (
        '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
        '127.0.0.0/8', '169.254.0.0/16', '100.64.0.0/10')]
    for match in re.finditer(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])', text):
        try:
            address = ipaddress.IPv4Address(match.group())
        except ValueError:
            continue
        if any(address in network for network in networks):
            return 1
    if re.search(r'(?<![\w.-])(?:[a-z0-9-]+\.)+'
                 r'(?:localhost|local|lan|internal)\.?(?![\w.-])'
                 r'|(?:://|["\'@])(?:localhost|local|lan|internal)\.?(?![\w.-])',
                 text, re.IGNORECASE):
        return 1
    if re.search(r'(?:ghp_|github_pat_|sk-)[A-Za-z0-9_-]+', text):
        return 1
    patterns = os.environ.get('CHECK_PUBLIC_PRIVATE_PATTERNS', '').splitlines()
    pattern_file = os.environ.get('CHECK_PUBLIC_PRIVATE_PATTERNS_FILE')
    if pattern_file:
        local_path = Path(pattern_file).resolve()
        if local_path.is_relative_to(Path(__file__).resolve().parents[1]):
            return 1
        patterns.extend(local_path.read_text(encoding='utf-8').splitlines())
    if any(pattern.strip().casefold() in text.casefold() for pattern in patterns if pattern.strip()):
        return 1
    print('Public manifest checks passed.')
    return 0


if __name__ == '__main__':
    try:
        result = main()
    except (OSError, ValueError):
        result = 1
    if result:
        print('Public manifest check failed; review structure, privacy rules, and configuration.', file=sys.stderr)
    sys.exit(result)
