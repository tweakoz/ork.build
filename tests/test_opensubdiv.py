"""OpenSubdiv recipe: cmake vars per platform, pinned-version freshness, presence check.

Never fetches or builds; the stage is a temp dir.
"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load():
    spec = importlib.util.spec_from_file_location('review_opensubdiv', ROOT / 'modules/dep/opensubdiv.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBuilder:
    def __init__(self):
        self.vars = {}

    def setCmVars(self, values):
        self.vars.update(values)

    def useMold(self):
        return self


class OpenSubdivTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name) / 'stage'
        self.osd = load()
        m = self.osd
        for p in (mock.patch.object(m.path, 'stage', return_value=self.stage),
                  mock.patch.object(m.path, 'builds', return_value=self.stage / 'builds'),
                  mock.patch.object(m.path, 'libs', return_value=self.stage / 'lib'),
                  mock.patch.object(m.path, 'includes', return_value=self.stage / 'include')):
            p.start()
            self.addCleanup(p.stop)

    def host(self, osx):
        for name, value in (('IsOsx', osx), ('IsDarwin', osx), ('IsLinux', not osx), ('IsIx', not osx)):
            p = mock.patch.object(self.osd.host, name, value, create=True)
            p.start()
            self.addCleanup(p.stop)

    def provider(self):
        m = self.osd
        declared = []

        def fake_init(prov, name):
            prov._name = name

        def set_source_root(prov, root):
            prov.source_root = root

        with mock.patch.object(m.dep.StdProvider, '__init__', fake_init), \
             mock.patch.object(m.dep.StdProvider, 'setSourceRoot', set_source_root, create=True), \
             mock.patch.object(m.dep.StdProvider, 'declareDep', lambda prov, n: declared.append(n), create=True), \
             mock.patch.object(m.dep.StdProvider, 'createBuilder', lambda prov, cls: FakeBuilder(), create=True):
            prov = m.opensubdiv()
        prov.declared = declared
        return prov

    def test_cmake_vars_per_platform(self):
        for osx in (True, False):
            with self.subTest(osx=osx):
                self.host(osx)
                prov = self.provider()
                v = prov._builder.vars
                self.assertEqual(v['BUILD_SHARED_LIBS'], 'ON')
                self.assertEqual(v['NO_TBB'], 'OFF')
                for key in ('NO_CUDA', 'NO_OPENCL', 'NO_DX', 'NO_OMP', 'NO_PTEX', 'NO_EXAMPLES',
                            'NO_TUTORIALS', 'NO_REGRESSION', 'NO_DOC', 'NO_TESTS', 'NO_GLFW', 'NO_GLEW'):
                    self.assertEqual(v[key], 'ON', key)
                self.assertEqual(v['NO_METAL'], 'OFF' if osx else 'ON')
                self.assertEqual(v['NO_OPENGL'], 'ON' if osx else 'OFF')
                self.assertFalse(any('CUDA' in k and k != 'NO_CUDA' for k in v))
                self.assertNotIn('CMAKE_CXX_COMPILER', v)
                self.assertEqual(v['TBB_DIR'], str(self.stage / 'lib/cmake/TBB'))
                self.assertEqual(prov.declared, ['cmake', 'tbb'])
                self.assertNotIn('cuda', prov.declared)
                self.assertEqual(prov._fetcher._revision, 'v3_6_1')
                self.assertEqual(prov._fetcher._repospec, 'PixarAnimationStudios/OpenSubdiv')

    def install_fake(self, patch='1', ext='dylib'):
        lib = self.stage / 'lib'
        lib.mkdir(parents=True, exist_ok=True)
        for name in ('CPU', 'GPU'):
            (lib / ('libosd%s.%s' % (name, ext))).write_text('')
        inc = self.stage / 'include/opensubdiv'
        inc.mkdir(parents=True, exist_ok=True)
        (inc / 'version.h').write_text('#define OPENSUBDIV_VERSION_MAJOR 3\n#define OPENSUBDIV_VERSION_MINOR 6\n'
                                       '#define OPENSUBDIV_VERSION_PATCH %s\n' % patch)

    def test_presence_check(self):
        for osx, ext in ((True, 'dylib'), (False, 'so')):
            with self.subTest(osx=osx):
                self.host(osx)
                prov = self.provider()
                self.assertFalse(prov.areRequiredBinaryFilesPresent())
                self.install_fake(ext=ext)
                self.assertTrue(prov.areRequiredBinaryFilesPresent())
                (self.stage / ('lib/libosdGPU.' + ext)).unlink()
                self.assertFalse(prov.areRequiredBinaryFilesPresent())
                (self.stage / ('lib/libosdCPU.' + ext)).unlink()

    def test_stale_version_flagged(self):
        self.host(True)
        prov = self.provider()
        self.install_fake(patch='0')
        self.assertFalse(prov.areRequiredBinaryFilesPresent())
        self.install_fake(patch='1')
        self.assertTrue(prov.areRequiredBinaryFilesPresent())


if __name__ == '__main__':
    unittest.main()
