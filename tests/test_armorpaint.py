"""ArmorPaint recipe: host gating, make command line, install layout, presence check.

Never fetches or builds; the stage and the build output are temp-dir fakes.
"""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load():
    spec = importlib.util.spec_from_file_location('review_armorpaint', ROOT / 'modules/dep/armorpaint.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArmorPaintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'stage'
        self.ap = load()
        patch = mock.patch.object(self.ap.path, 'stage', return_value=self.stage)
        patch.start()
        self.addCleanup(patch.stop)

    def host(self, osx, arm):
        patches = [mock.patch.object(self.ap.host, 'IsOsx', osx),
                   mock.patch.object(self.ap.host, 'IsDarwin', osx),
                   mock.patch.object(self.ap.host, 'IsLinux', not osx),
                   mock.patch.object(self.ap.host, 'IsAARCH64', arm),
                   mock.patch.object(self.ap.host, 'IsX86_64', not arm)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def provider(self, source):
        prov = self.ap.armorpaint.__new__(self.ap.armorpaint)
        prov._oslist = ['Darwin', 'Linux']
        prov._archlist = ['x86_64', 'aarch64']
        prov.source_root = source
        return prov

    def fake_source(self, osx, arm):
        src = self.root / 'src'
        plat = 'macos' if osx else ('linux_arm64' if arm else 'linux_x64')
        for rel in ('base/make', 'paint/project.js', 'base/tools/bin/%s/amake' % plat):
            (src / rel).parent.mkdir(parents=True, exist_ok=True)
            (src / rel).write_text('')
        return src

    def test_host_gating(self):
        for osx, arm, ok in ((True, True, True), (True, False, False),
                             (False, True, True), (False, False, True)):
            with self.subTest(osx=osx, arm=arm):
                with mock.patch.object(self.ap.host, 'IsOsx', osx), \
                     mock.patch.object(self.ap.host, 'IsDarwin', osx), \
                     mock.patch.object(self.ap.host, 'IsLinux', not osx), \
                     mock.patch.object(self.ap.host, 'IsIrix', False, create=True), \
                     mock.patch.object(self.ap.host, 'IsAARCH64', arm), \
                     mock.patch.object(self.ap.host, 'IsX86_64', not arm):
                    self.assertEqual(self.provider(self.root).supports_host, ok)

    def run_build(self, osx, arm):
        self.host(osx, arm)
        src = self.fake_source(osx, arm)
        calls = []

        class FakeCommand:
            def __init__(self, args, working_dir=None, **kw):
                calls.append((args, working_dir))

            def exec(self):
                return 0

        with mock.patch.object(self.ap, 'Command', FakeCommand):
            self.assertTrue(self.provider(src).build())
        self.assertTrue(os.access(src / 'base/make', os.X_OK))
        return calls, src

    def test_make_command_per_platform(self):
        calls, src = self.run_build(True, True)
        self.assertEqual(calls, [(['../base/make', '--graphics', 'metal', '--compile'], src / 'paint')])
        self.assertTrue(os.access(src / 'base/tools/bin/macos/amake', os.X_OK))

    def test_make_command_linux(self):
        calls, src = self.run_build(False, False)
        self.assertEqual(calls, [(['../base/make', '--graphics', 'vulkan', '--compile'], src / 'paint')])
        self.assertTrue(os.access(src / 'base/tools/bin/linux_x64/amake', os.X_OK))

    def test_macos_install_layout_and_presence(self):
        self.host(True, True)
        src = self.fake_source(True, True)
        prov = self.provider(src)
        self.assertFalse(prov.areRequiredBinaryFilesPresent())
        exe = src / 'paint/build/build/Release/ArmorPaint.app/Contents/MacOS/ArmorPaint'
        exe.parent.mkdir(parents=True)
        exe.write_text('bin')
        stale = self.stage / 'apps/ArmorPaint.app/stale'
        stale.parent.mkdir(parents=True)
        stale.write_text('old')
        self.assertTrue(prov.install())
        installed = self.stage / 'apps/ArmorPaint.app/Contents/MacOS/ArmorPaint'
        self.assertTrue(installed.exists())
        self.assertFalse(stale.exists())
        launcher = self.stage / 'bin/armorpaint'
        self.assertTrue(os.access(launcher, os.X_OK))
        self.assertEqual(launcher.read_text(), '#!/bin/sh\nexec "%s" "$@"\n' % installed)
        self.assertTrue(prov.areRequiredBinaryFilesPresent())
        installed.unlink()
        self.assertFalse(prov.areRequiredBinaryFilesPresent())

    def test_linux_install_layout(self):
        self.host(False, True)
        src = self.fake_source(False, True)
        out = src / 'paint/build/out'
        (out / 'data').mkdir(parents=True)
        (out / 'data/x.arm').write_text('d')
        (out / 'ArmorPaint').write_text('bin')
        prov = self.provider(src)
        self.assertTrue(prov.install())
        self.assertTrue((self.stage / 'apps/armorpaint/ArmorPaint').exists())
        self.assertTrue((self.stage / 'apps/armorpaint/data/x.arm').exists())
        self.assertIn(str(self.stage / 'apps/armorpaint/ArmorPaint'), (self.stage / 'bin/armorpaint').read_text())
        self.assertTrue(prov.areRequiredBinaryFilesPresent())

    def test_missing_build_output_fails_install(self):
        self.host(True, True)
        self.assertFalse(self.provider(self.fake_source(True, True)).install())


if __name__ == '__main__':
    unittest.main()
