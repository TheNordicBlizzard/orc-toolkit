"""Asset-free packaging acceptance; no GPU or game installation required."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]

class ReleasePackageTests(unittest.TestCase):
    def test_exact_allowlist_excludes_unlisted_files(self):
        script = ROOT / 'tools' / 'package_source.py'
        self.assertTrue(script.is_file(), 'Explicit allowlist packager is missing')
        with tempfile.TemporaryDirectory(prefix='orc package ') as directory:
            root = Path(directory)
            (root / 'README.md').write_text('Synthetic public documentation')
            (root / 'private.json').write_text('Synthetic private state')
            (root / 'release-files.txt').write_text('README.md\n')
            output = root / 'output.zip'
            result = subprocess.run([sys.executable, str(script), '--root', str(root),
                                     '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ['README.md'])
                self.assertEqual(archive.read('README.md'), b'Synthetic public documentation')

    def test_reviewed_license_bundle_is_packaged(self):
        with tempfile.TemporaryDirectory(prefix='orc notices ') as directory:
            root = Path(directory)
            entries = ['asset_explorer/THIRD_PARTY_LICENSES/component/LICENSE',
                       'asset_explorer/THIRD_PARTY_LICENSES/component/license.terms',
                       'asset_explorer/native.spdx.json',
                       'asset_explorer/compliance_manifest.json']
            for entry in entries:
                target = root / entry
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('Audited synthetic test notice or inventory')
            (root / 'release-files.txt').write_text('\n'.join(entries))
            output = root / 'output.zip'
            result = subprocess.run([sys.executable, str(ROOT / 'tools/package_source.py'),
                                     '--root', str(root), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), entries)

    def test_game_or_binary_entry_is_refused_before_zip_write(self):
        with tempfile.TemporaryDirectory(prefix='orc refused ') as directory:
            root = Path(directory)
            (root / 'sample.ssg').write_bytes(b'synthetic')
            (root / 'release-files.txt').write_text('sample.ssg\n')
            output = root / 'output.zip'
            result = subprocess.run([sys.executable, str(ROOT / 'tools/package_source.py'),
                                     '--root', str(root), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

if __name__ == '__main__':
    unittest.main()
