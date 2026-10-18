"""MaterialX recipe: cmake vars, pinned-version freshness, presence check.

Never fetches or builds; the stage and the python interpreter are fakes.
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
    spec = importlib.util.spec_from_file_location('review_materialx', ROOT / 'modules/dep/materialx.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBuilder:
    def __init__(self):
        self.vars = {}
        self.deps = []

    def setCmVar(self, key, value):
        self.vars[key] = value

    def setCmVars(self, values):
        self.vars.update(values)

    def requires(self, deps):
        self.deps += deps


class FakePython:
    def __init__(self, stage):
        self.home_dir = stage / 'pyvenv'
        self.executable = self.home_dir / 'bin/python3'
        self.include_dir = self.home_dir / 'include/python3.14t'
        self.site_packages_dir = self.home_dir / 'lib/python3.14t/site-packages'


class MaterialXTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name) / 'stage'
        self.mx = load()
        self.python = FakePython(self.stage)
        mx = self.mx
        patches = [
            mock.patch.object(mx.path, 'stage', return_value=self.stage),
            mock.patch.object(mx.path, 'builds', return_value=self.stage / 'builds'),
            mock.patch.object(mx.path, 'libs', return_value=self.stage / 'lib'),
            mock.patch.object(mx.path, 'includes', return_value=self.stage / 'include'),
            mock.patch.object(mx.dep, 'instance', return_value=self.python),
            mock.patch.object(mx, 'python_extension_suffix', return_value='.cpython-314t-darwin.so'),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def host(self, osx):
        for name, value in (('IsOsx', osx), ('IsDarwin', osx), ('IsLinux', not osx), ('IsIx', not osx)):
            p = mock.patch.object(self.mx.host, name, value, create=True)
            p.start()
            self.addCleanup(p.stop)

    def provider(self):
        mx = self.mx
        declared = []

        def fake_init(prov, name):
            prov._name = name

        def set_source_root(prov, root):
            prov.source_root = root

        with mock.patch.object(mx.dep.StdProvider, '__init__', fake_init), \
             mock.patch.object(mx.dep.StdProvider, 'setSourceRoot', set_source_root, create=True), \
             mock.patch.object(mx.dep.StdProvider, 'declareDep', lambda prov, n: declared.append(n), create=True), \
             mock.patch.object(mx.dep.StdProvider, 'createBuilder', lambda prov, cls: FakeBuilder(), create=True):
            prov = mx.materialx()
        prov.declared = declared
        return prov

    def test_cmake_vars_per_platform(self):
        for osx, ext in ((True, 'dylib'), (False, 'so')):
            with self.subTest(osx=osx):
                self.host(osx)
                prov = self.provider()
                v = prov._builder.vars
                for key in ('MATERIALX_BUILD_SHARED_LIBS', 'MATERIALX_BUILD_GEN_GLSL', 'MATERIALX_BUILD_GEN_MSL',
                            'MATERIALX_BUILD_GEN_OSL', 'MATERIALX_BUILD_PYTHON', 'MATERIALX_INSTALL_PYTHON'):
                    self.assertEqual(v[key], 'ON', key)
                for key in ('MATERIALX_BUILD_VIEWER', 'MATERIALX_BUILD_GRAPH_EDITOR', 'MATERIALX_BUILD_TESTS',
                            'MATERIALX_BUILD_OIIO', 'MATERIALX_INSTALL_RESOURCES'):
                    self.assertEqual(v[key], 'OFF', key)
                self.assertEqual(v['MATERIALX_PYTHON_EXECUTABLE'], self.python.executable)
                self.assertEqual(v['PYTHON_EXECUTABLE'], self.python.executable)
                self.assertTrue(v['MATERIALX_PYTHON_PYBIND11_DIR'].endswith('External/PyBind11'))
                self.assertEqual(prov.source_root, self.stage / 'builds/materialx' / ('materialx-' + self.mx.VERSION))
                self.assertIn('python', prov.declared)
                self.assertEqual(prov.shlib_extension, ext)

    def test_python_off_drops_interpreter_vars(self):
        self.host(True)
        with mock.patch.object(self.mx, 'BUILD_PYTHON', False):
            prov = self.provider()
        self.assertEqual(prov._builder.vars['MATERIALX_BUILD_PYTHON'], 'OFF')
        self.assertNotIn('PYTHON_EXECUTABLE', prov._builder.vars)
        self.assertNotIn('python', prov.declared)

    def install_fake(self, build='5'):
        lib = self.stage / 'lib'
        lib.mkdir(parents=True, exist_ok=True)
        for name in ('Core', 'Format', 'GenShader', 'GenGlsl', 'GenMsl', 'GenOsl'):
            (lib / ('libMaterialX%s.dylib' % name)).write_text('')
        inc = self.stage / 'include/MaterialXCore'
        inc.mkdir(parents=True, exist_ok=True)
        (inc / 'Document.h').write_text('')
        (inc / 'Generated.h').write_text('#define MATERIALX_MAJOR_VERSION 1\n#define MATERIALX_MINOR_VERSION 39\n'
                                         '#define MATERIALX_BUILD_VERSION %s\n' % build)
        cfg = lib / 'cmake/MaterialX'
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / 'MaterialXConfigVersion.cmake').write_text('set(PACKAGE_VERSION "1.39.%s")\n' % build)
        (self.stage / 'libraries/targets').mkdir(parents=True, exist_ok=True)
        pkg = self.python.site_packages_dir / 'MaterialX'
        pkg.mkdir(parents=True, exist_ok=True)
        (pkg / 'PyMaterialXCore.cpython-314t-darwin.so').write_text('')

    def test_presence_check(self):
        self.host(True)
        prov = self.provider()
        self.assertFalse(prov.areRequiredBinaryFilesPresent())
        self.install_fake()
        self.assertTrue(prov.areRequiredBinaryFilesPresent())
        (self.python.site_packages_dir / 'MaterialX/PyMaterialXCore.cpython-314t-darwin.so').unlink()
        self.assertFalse(prov.areRequiredBinaryFilesPresent())
        with mock.patch.object(self.mx, 'BUILD_PYTHON', False):
            self.assertTrue(prov.areRequiredBinaryFilesPresent())
        (self.stage / 'lib/libMaterialXGenMsl.dylib').unlink()
        with mock.patch.object(self.mx, 'BUILD_PYTHON', False):
            self.assertFalse(prov.areRequiredBinaryFilesPresent())

    def test_stale_version_flagged(self):
        self.host(True)
        prov = self.provider()
        self.install_fake(build='4')
        self.assertFalse(prov.areRequiredBinaryFilesPresent())
        # Header stale alone (config current) is still flagged.
        (self.stage / 'lib/cmake/MaterialX/MaterialXConfigVersion.cmake').write_text(
            'set(PACKAGE_VERSION "%s")\n' % self.mx.VERSION)
        self.assertFalse(prov.areRequiredBinaryFilesPresent())
        self.install_fake(build='5')
        self.assertTrue(prov.areRequiredBinaryFilesPresent())


if __name__ == '__main__':
    unittest.main()
