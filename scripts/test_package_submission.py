"""Meaningful archive failure/integrity regressions; no dependency on live data."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from package_submission import INDEX, MANIFEST, digest, sources, validate_name, verify


class PackagingTests(unittest.TestCase):
    def test_missing_required_source_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/MANIFEST).write_text(json.dumps({'files': [{'path': 'missing.py'}]}))
            with self.assertRaisesRegex(ValueError, 'Missing'):
                sources(root)

    def test_archive_hash_and_complete_inventory(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder)/'submission.zip'
            manifest = json.dumps({'files': [{'path': MANIFEST}, {'path': 'app.py'}]}).encode()
            files = {MANIFEST: manifest, 'app.py': b'original'}
            index = {name: dict(bytes=len(data), sha256=digest(data)) for name, data in files.items()}
            def write(content):
                with zipfile.ZipFile(archive, 'w') as target:
                    for name, data in content.items():
                        target.writestr(name, data)
                    target.writestr(INDEX, json.dumps(index))
            write(files)
            self.assertEqual(verify(archive)['content_hashes_verified'], 2)
            write({**files, 'app.py': b'tampered'})
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                verify(archive)
            write({MANIFEST: manifest})
            with self.assertRaisesRegex(ValueError, 'disagree'):
                verify(archive)

    def test_local_or_unsafe_paths_rejected(self):
        for name in ['../escape.py', '/absolute.py', 'C:/secret', '.env', 'data/undo.db',
                     'node_modules/test.js', 'dist/archive.zip', '.runtime/before.db']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_name(name)


if __name__ == '__main__':
    unittest.main()
