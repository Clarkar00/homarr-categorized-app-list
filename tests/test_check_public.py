"""Synthetic fixtures only; never add deployment-specific private values."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'check_public.py'
VALID = {
    '$schema': 'homarr-custom-widget-v2', 'name': 'Example',
    'sources': {'default': {'baseUrl': 'https://homarr.example.com',
                            'auth': {'type': 'apiKeyHeader', 'name': 'ApiKey'}}},
    'requests': {}, 'options': {'containerOverrides': {'default': ''}},
    'template': '<p>Example</p>',
}


class PublicCheckTests(unittest.TestCase):
    def run_check(self, data=None, raw=None, env=None):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp:
            manifest = Path(tmp) / 'manifest.json'
            manifest.write_text(raw if raw is not None else json.dumps(data), encoding='utf-8')
            clean_env = {k: v for k, v in os.environ.items()
                         if k not in ('CHECK_PUBLIC_PRIVATE_PATTERNS', 'CHECK_PUBLIC_PRIVATE_PATTERNS_FILE')}
            clean_env.update(env or {})
            return subprocess.run([sys.executable, str(SCRIPT), str(manifest)],
                                  text=True, capture_output=True, env=clean_env)

    def test_structure_and_required_types(self):
        invalid = [[], None, {}, {**VALID, '$schema': 'other'}]
        for key, bad in [('name', 1), ('sources', []), ('requests', []),
                         ('options', []), ('template', 1), ('template', '  ')]:
            invalid.extend([{**VALID, key: bad}, {k: v for k, v in VALID.items() if k != key}])
        for data in invalid:
            with self.subTest(data=data):
                self.assertNotEqual(self.run_check(data).returncode, 0)

    def test_public_defaults(self):
        for source in [{}, None, {'baseUrl': 'https://public.example.org'},
                       {'baseURL': 'https://homarr.example.com'}]:
            data = copy.deepcopy(VALID)
            data['sources']['default'] = source
            self.assertNotEqual(self.run_check(data).returncode, 0)
        for override in [{}, None, {'default': 'example=container'}, {'default': []}]:
            data = copy.deepcopy(VALID)
            data['options']['containerOverrides'] = override
            self.assertNotEqual(self.run_check(data).returncode, 0)

    def test_auth_allows_config_but_no_credential_fields(self):
        for auth in [None, [], {'type': 1, 'name': 'ApiKey'},
                     {'type': 'apiKeyHeader'},
                     *[{'type': 'apiKeyHeader', 'name': 'ApiKey', key: 'synthetic'}
                       for key in ['value', 'token', 'password', 'apiKey', 'headers']]]:
            data = copy.deepcopy(VALID)
            data['sources']['additional'] = {'auth': auth}
            with self.subTest(auth=auth):
                self.assertNotEqual(self.run_check(data).returncode, 0)

    def test_private_ipv4_anywhere_including_keys(self):
        for address in ['10.23.45.67', '172.16.2.3', '172.31.255.254',
                        '192.168.2.3', '127.0.0.2', '169.254.3.4',
                        '100.64.0.1', '100.127.255.254']:
            with self.subTest(address=address):
                data = copy.deepcopy(VALID)
                data['extra'] = {address: ['https://' + address + ':8080/a']}
                result = self.run_check(data)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn(address, result.stdout + result.stderr)
        data = {**VALID, 'extra': '8.8.8.8 172.15.0.1 172.32.0.1 100.63.0.1 100.128.0.1'}
        self.assertEqual(self.run_check(data).returncode, 0)

    def test_private_hosts(self):
        for host in ['localhost', 'LOCALHOST.', 'api.localhost', 'server.local',
                     'example.lan', 'api.example.INTERNAL.', 'local', 'lan', 'internal']:
            with self.subTest(host=host):
                result = self.run_check({**VALID, 'extra': 'https://' + host + ':8080/path'})
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn(host, result.stdout + result.stderr)
        self.assertEqual(self.run_check({**VALID, 'extra': 'localStorage internalName example.locality'}).returncode, 0)

    def test_localhost_warning_is_not_a_host(self):
        result = self.run_check({**VALID, 'description': 'Use your Homarr URL, not localhost.'})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_obvious_token_prefixes(self):
        for token in ['ghp_syntheticExample123', 'github_pat_syntheticExample123', 'sk-syntheticExample123']:
            result = self.run_check({**VALID, 'extra': token})
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(token, result.stdout + result.stderr)

    def test_local_patterns_environment(self):
        data = {**VALID, 'extra': 'https://synthetic-private.example.org'}
        env = {'CHECK_PUBLIC_PRIVATE_PATTERNS': '\nsynthetic-private.example.org\nother-synthetic\n'}
        result = self.run_check(data, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('synthetic-private', result.stdout + result.stderr)
        self.assertEqual(self.run_check(VALID, env=env).returncode, 0)

    def test_local_patterns_file_must_be_outside_repo(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp:
            patterns = Path(tmp) / 'private-patterns.txt'
            patterns.write_text('synthetic-private.example.org\n', encoding='utf-8')
            env = {'CHECK_PUBLIC_PRIVATE_PATTERNS_FILE': str(patterns)}
            self.assertNotEqual(self.run_check({**VALID, 'extra': 'SYNTHETIC-PRIVATE.EXAMPLE.ORG'}, env=env).returncode, 0)
            self.assertEqual(self.run_check(VALID, env=env).returncode, 0)
        self.assertNotEqual(self.run_check(VALID, env={'CHECK_PUBLIC_PRIVATE_PATTERNS_FILE': str(SCRIPT)}).returncode, 0)

    def test_malformed_json_fails_without_traceback_or_values(self):
        result = self.run_check(raw='{"synthetic-sensitive": INVALID}')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stderr)
        self.assertNotIn('synthetic-sensitive', result.stdout + result.stderr)
        self.assertTrue(result.stderr.strip())

    def test_valid_manifest(self):
        result = self.run_check(VALID)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
