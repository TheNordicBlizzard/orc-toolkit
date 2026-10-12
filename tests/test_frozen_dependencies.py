"""Opt-in artifact tests; no developer paths or private fixtures are required."""
import os
from pathlib import PureWindowsPath
import unittest

@unittest.skipUnless(os.environ.get('ORC_QA_EXE'), 'Set ORC_QA_EXE to test a built Windows artifact')
class FrozenDependencies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyInstaller.archive.readers import CArchiveReader
        cls.archive = CArchiveReader(os.environ['ORC_QA_EXE'])

    def test_unused_glut_gle_and_old_crt_are_absent(self):
        names = [n.lower().replace('\\', '/') for n in self.archive.toc]
        self.assertFalse([n for n in names if n.startswith('opengl/dlls/') or any(v in n for v in ('freeglut', 'gle32', 'gle64', 'msvcr100'))])

    def test_windows_inbox_and_vc_files_are_not_redistributed(self):
        names = [PureWindowsPath(n).name.lower() for n in self.archive.toc if n.lower().endswith('.dll')]
        self.assertFalse([n for n in names if n.startswith(('api-ms-win-', 'ext-ms-win-', 'vcruntime', 'msvcp')) or n == 'ucrtbase.dll'])

    def test_required_python_native_dependencies_are_retained(self):
        names = {PureWindowsPath(n).name.lower() for n in self.archive.toc}
        self.assertTrue({'python314.dll', 'libcrypto-3-x64.dll', 'libssl-3-x64.dll', 'libffi-8.dll', 'libtommath.dll', 'zlib1.dll', 'tcl90.dll', 'tcl9tk90.dll'} <= names)

    def test_blender_worker_and_notice_resources_are_bundled(self):
        names = {n.replace('\\', '/') for n in self.archive.toc}
        self.assertIn('blender_worker.py', names)
        self.assertIn('external_runtime_aliases.json', names)
        self.assertTrue(any(n.startswith('THIRD_PARTY_LICENSES/customtkinter/') for n in names))

    def test_no_remaining_native_import_requires_msvcr100(self):
        import pefile
        for name in self.archive.toc:
            if name.lower().endswith(('.dll', '.pyd')):
                pe = pefile.PE(data=self.archive.extract(name))
                imports = {x.dll.decode().lower() for x in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', [])}
                self.assertNotIn('msvcr100.dll', imports, name)

if __name__ == '__main__':
    unittest.main()
