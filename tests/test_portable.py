"""Discoverable public tests; private fixtures are optional and never bundled."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from portable_smoke import CoreSmoke, CameraSmoke


class OptionalOwnedFixtureTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('ORC_MODEL_FIXTURE'),
                         'Optional owned game fixture not configured')
    def test_isolated_fixture_gui(self):
        command = [sys.executable, '-B', str(Path(__file__).with_name('portable_smoke.py')),
                   '--gui', '--fixture', os.environ['ORC_MODEL_FIXTURE']]
        result = subprocess.run(command, timeout=150)
        self.assertEqual(result.returncode, 0)
