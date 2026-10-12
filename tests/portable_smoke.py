"""Asset-free core/camera checks plus opt-in isolated real GUI/fixture smoke.
Private fixtures are input only; no game bytes or fixture paths enter reports.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest

RUNTIME = ('app archive audio batch_extract blender_export blender_worker containers '
           'core editor_style full_export_ui gpu_preview i18n media models modern_ui '
           'settings_ui ssg_parser').split()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'asset_explorer'))

class CoreSmoke(unittest.TestCase):
    def test_extract_roundtrip_no_overwrite(self):
        import core
        with tempfile.TemporaryDirectory(prefix='orc-core-') as directory:
            assets = [core.Asset('nested/sample.txt', b'public synthetic fixture')]
            paths = core.extract(assets, directory)
            self.assertEqual(paths[0].read_bytes(), assets[0].data)
            with self.assertRaises(ValueError):
                core.extract(assets, directory)
            self.assertEqual(paths[0].read_bytes(), assets[0].data)

    def test_unsafe_name_has_no_output(self):
        import core
        with tempfile.TemporaryDirectory(prefix='orc-safe-') as directory:
            with self.assertRaises(ValueError):
                core.extract([core.Asset('../escape', b'synthetic')], directory)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_invalid_model_is_rejected(self):
        import core
        with self.assertRaises(ValueError):
            core.parse_mesh(b'not a model')

class CameraSmoke(unittest.TestCase):
    def setUp(self):
        from app import Explorer
        self.explorer = Explorer.__new__(Explorer)
        a = self.explorer
        a.mesh = object()
        a.image = None
        a.drag = (100, 100)
        a.camera_pan = (0, 0)
        a.yaw, a.pitch, a.zoom = .4, .1, 1
        a.texture_zoom, a.pan = 1, (0, 0)
        a.request_draw = lambda: None

    def test_pan_preserves_orientation(self):
        a = self.explorer
        a.pan_camera(SimpleNamespace(x=140, y=125))
        self.assertEqual(a.camera_pan, (40, 25))
        self.assertEqual((a.yaw, a.pitch, a.zoom), (.4, .1, 1))

    def test_orbit_wheel_reset(self):
        a = self.explorer
        a.orbit(SimpleNamespace(x=135, y=120))
        self.assertAlmostEqual(a.yaw, .75)
        self.assertAlmostEqual(a.pitch, .3)
        a.wheel(SimpleNamespace(delta=120))
        self.assertAlmostEqual(a.zoom, 1.1)
        a.reset(draw=False)
        self.assertEqual((a.yaw, a.pitch, a.zoom, a.camera_pan), (.4, .1, 1, (0, 0)))

    def test_texture_pan_separate(self):
        a = self.explorer
        a.mesh, a.image = None, object()
        a.pan_camera(SimpleNamespace(x=120, y=112))
        self.assertEqual(a.pan, (20, 12))
        self.assertEqual(a.camera_pan, (0, 0))

def gui_worker(fixture):
    """Exercise ordinary app.main, not the unavailable internal QA hooks."""
    import app
    import numpy as np
    original = app.Explorer
    state = {'ordinary_main': True}
    fixture_hash = hashlib.sha256(fixture.read_bytes()).hexdigest() if fixture else None
    class ObservedExplorer(original):
        def __init__(self, root):
            super().__init__(root)
            start = time.monotonic()
            def check():
                try:
                    if self.busy or (fixture and self.detail is None):
                        if time.monotonic() - start > 90:
                            raise AssertionError('Model load timeout')
                        root.after(100, check)
                        return
                    assert self.gpu.ready, 'Hardware GPU context unavailable'
                    state['gpu_ready'] = True
                    if fixture:
                        assert len(self.detail['vertices']) > 0
                        before = np.array(self.gpu.snapshot())
                        vertices = self.detail['vertices'].copy()
                        uploads = self.gpu.upload_count
                        self.drag = (100, 100)
                        self.pan_camera(SimpleNamespace(x=140, y=125))
                        self.draw()
                        assert self.camera_pan == (40, 25)
                        assert not np.array_equal(before, np.array(self.gpu.snapshot()))
                        assert uploads == self.gpu.upload_count
                        np.testing.assert_array_equal(vertices, self.detail['vertices'])
                        self.reset()
                        np.testing.assert_array_equal(before, np.array(self.gpu.snapshot()))
                        state.update(real_fixture=True, frame_pan_reset=True,
                                     vertices=len(vertices), faces=len(self.detail['faces']))
                    state['success'] = True
                except Exception as error:
                    state.update(success=False, error_type=type(error).__name__)
                finally:
                    if 'success' in state:
                        self.close()
            root.after(800, check)
    app.Explorer = ObservedExplorer
    sys.argv = ['app.py'] + ([str(fixture)] if fixture else [])
    app.main()
    if fixture:
        state['fixture_unchanged'] = fixture_hash == hashlib.sha256(fixture.read_bytes()).hexdigest()
        state['success'] = state.get('success', False) and state['fixture_unchanged']
    print(json.dumps(state))
    return 0 if state.get('success') else 1

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=os.environ.get('ORC_MODEL_FIXTURE'),
                        help='Owned real model SSG; alternatively ORC_MODEL_FIXTURE')
    parser.add_argument('--scratch', type=Path, default=os.environ.get('TMPDIR'),
                        help='Writable isolated scratch; alternatively TMPDIR')
    parser.add_argument('--gui', action='store_true', help='Run ordinary GUI in a clean source copy')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    fixture = Path(args.fixture).resolve() if args.fixture else None
    if fixture and not fixture.is_file():
        parser.error('Fixture must be an existing owned file')
    if args.worker:
        return gui_worker(fixture)
    if args.scratch is None or not args.scratch.is_dir():
        parser.error('Provide an existing --scratch directory or TMPDIR')
    tempfile.tempdir = str(args.scratch.resolve())
    suite = unittest.TestSuite()
    for case in (CoreSmoke, CameraSmoke):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if args.gui:
        with tempfile.TemporaryDirectory(prefix='orc source smoke-', dir=args.scratch) as directory:
            isolated = Path(directory)
            source = isolated / 'asset_explorer'
            source.mkdir()
            for module in RUNTIME:
                shutil.copy2(ROOT / 'asset_explorer' / (module + '.py'), source)
            tests = isolated / 'tests'
            tests.mkdir()
            shutil.copy2(__file__, tests / 'portable_smoke.py')
            command = [sys.executable, '-B', str(tests / 'portable_smoke.py'), '--worker']
            if fixture:
                command += ['--fixture', str(fixture)]
            env = dict(os.environ, PYTHONPATH='', TMPDIR=str(args.scratch))
            completed = subprocess.run(command, cwd=isolated, env=env, timeout=120)
            return completed.returncode
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
