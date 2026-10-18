"""Recipe regressions. Optional upstream probes use OBT_TEST_STEAMAUDIO_SOURCE.

That variable points to an already fetched Steam Audio source tree; tests never
fetch dependencies, invoke their build, or modify that source tree.
"""
import ast
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name):
    spec = importlib.util.spec_from_file_location('review_' + name, ROOT / 'modules/dep' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AudioProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.core = self.root / 'source/core'
        (self.core / 'build').mkdir(parents=True)
        self.sa = load('steamaudio')
        for patch in (mock.patch.object(self.sa, '_core_dir', return_value=self.core),
                      mock.patch.object(self.sa, '_src_root', return_value=self.core.parent),
                      mock.patch.object(self.sa.host, 'IsLinux', True),
                      mock.patch.object(self.sa.host, 'IsOsx', False),
                      mock.patch.object(self.sa.host, 'IsAARCH64', True)):
            patch.start()
            self.addCleanup(patch.stop)
        self.original = self.core / 'build/get_dependencies.py'
        self.original.write_text("host_platform = 'linux-x64'\nselected = toolchain('linux_arm64')\n")

    def test_native_arm_driver_preserves_upstream_and_selects_native_tools(self):
        original = self.original.read_bytes()
        generated = self.sa._dependency_driver()
        self.assertEqual(self.original.read_bytes(), original)
        namespace = {'toolchain': lambda suffix: self.core / 'build' / ('toolchain_' + suffix + '.cmake')}
        exec(generated.read_text(), namespace)
        self.assertEqual(namespace['host_platform'], 'linux-arm64')
        toolchain = namespace['selected'].read_text()
        self.assertNotIn('CMAKE_SYSROOT', toolchain)
        self.assertNotIn('CMAKE_C_COMPILER', toolchain)
        flatc = self.sa._cmake_vars()['FlatBuffers_EXECUTABLE']
        self.assertEqual(flatc, str(self.core / 'deps/flatbuffers/bin/linux-arm64/flatc'))
        self.assertEqual(self.sa._dependency_driver().read_bytes(), generated.read_bytes())

    def test_x64_driver_is_unchanged_and_source_drift_fails_closed(self):
        with mock.patch.object(self.sa.host, 'IsAARCH64', False):
            self.assertEqual(self.sa._dependency_driver(), self.original)
        self.original.write_text('unexpected upstream change\n')
        with self.assertRaisesRegex(RuntimeError, 'upstream driver changed'):
            self.sa._dependency_driver()

    def prepare_stamps(self):
        files = []
        for dep in self.sa.REQUIRED_DEPS:
            for relative in (f'deps-build/{dep}/build/linux-arm64/CMakeCache.txt',
                             f'deps/{dep}/stamp/linux-arm64/.configureinfo'):
                p = self.core / relative
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('previous configuration')
                files.append(p)
        return files

    def test_settings_invalidate_output_stamps_and_cache_without_touching_sources(self):
        files = self.prepare_stamps()
        compiler_state = self.core / 'deps-build/zlib/build/linux-arm64/CMakeFiles/CMakeSystem.cmake'
        compiler_state.parent.mkdir(parents=True)
        compiler_state.write_text('old cross compiler settings')
        settings = self.sa._dependency_settings({'CXXFLAGS': '-O2'})
        marker = self.sa._invalidate_dependency_settings(settings)
        self.assertTrue(all(not p.exists() for p in files))
        self.assertTrue(self.original.exists())
        self.assertFalse(compiler_state.exists())
        self.assertFalse(marker.exists())  # not recorded until the builds succeed
        marker.write_text(json.dumps(settings))
        files = self.prepare_stamps()
        self.sa._invalidate_dependency_settings(settings)
        self.assertTrue(all(p.exists() for p in files))
        self.sa._invalidate_dependency_settings(self.sa._dependency_settings({'CXXFLAGS': '-O3'}))
        self.assertTrue(all(not p.exists() for p in files))

    def test_failed_fetch_does_not_mark_settings_successful(self):
        with mock.patch.object(self.sa, 'Command') as command:
            command.return_value.exec.side_effect = [0, 1]
            self.assertFalse(self.sa._fetch_sa_deps())
            self.assertFalse((self.core / '.obt-dependency-settings.json').exists())
            command.return_value.exec.side_effect = [0, 0, 0, 0]
            self.assertTrue(self.sa._fetch_sa_deps())
            self.assertTrue((self.core / '.obt-dependency-settings.json').exists())

    def test_notices_are_copied_exactly_and_missing_inputs_fail(self):
        for name, source in self.sa._license_sources().items():
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(('notice ' + name).encode())
        stage = self.root / 'stage'
        with mock.patch.object(self.sa.path, 'prefix', return_value=stage):
            self.sa._install_notices()
            for name, source in self.sa._license_sources().items():
                self.assertEqual((stage / 'share/doc/steamaudio' / name).read_bytes(), source.read_bytes())
            self.sa._license_sources()['zlib-LICENSE'].unlink()
            with self.assertRaises(FileNotFoundError):
                self.sa._install_notices()

    def test_ispc_install_retains_compiler_license(self):
        ispc = load('ispc')
        provider = ispc._ispc_from_wget.__new__(ispc._ispc_from_wget)
        provider.src_dir = self.root / 'ispc-source'
        (provider.src_dir / 'include/stdlib').mkdir(parents=True)
        (provider.src_dir / 'include/stdlib/amx.isph').write_text('// header')
        (provider.src_dir / 'LICENSE.txt').write_text('exact license bytes\n')
        provider._builder = SimpleNamespace(install=lambda _: True)
        stage = self.root / 'stage'
        with mock.patch.object(ispc.path, 'stage', return_value=stage), mock.patch.object(ispc.path, 'includes', return_value=stage/'include'):
            self.assertTrue(provider.install())
            self.assertEqual((stage/'share/doc/ispc/LICENSE.txt').read_bytes(), (provider.src_dir/'LICENSE.txt').read_bytes())


@unittest.skipUnless(os.environ.get('OBT_TEST_STEAMAUDIO_SOURCE'), 'optional fetched-upstream source probe')
class UpstreamDriverTests(unittest.TestCase):
    setUp = AudioProviderTests.setUp
    def upstream_namespace(self):
        upstream = Path(os.environ['OBT_TEST_STEAMAUDIO_SOURCE']) / 'core/build/get_dependencies.py'
        shutil.copy2(upstream, self.original)
        generated = self.sa._dependency_driver()
        tree = ast.parse(generated.read_text())
        # Import functions only: upstream's main program would fetch/build.
        nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.Import, ast.ImportFrom))]
        namespace = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(generated), 'exec'), namespace)
        return namespace

    def test_actual_upstream_native_arm_configure_avoids_cross_sysroot(self):
        ns = self.upstream_namespace()
        calls = []
        ns.update(make_dir=lambda _: None, stamp_configure=lambda *args: None,
                  run_command=lambda command: calls.append(command),
                  toolchain=lambda suffix: str(self.core/'build'/('toolchain_' + suffix + '.cmake')))
        ns['configure_cmake']('zlib', [], 'linux-arm64', 'cmake', 2019, None, None, False, False)
        option = next(a for a in calls[0] if a.startswith('-DCMAKE_TOOLCHAIN_FILE='))
        self.assertEqual(Path(option.split('=', 1)[1]).name, 'toolchain_obt_native_linux_arm64.cmake')
        self.assertNotIn('/sysroot', Path(option.split('=', 1)[1]).read_text())
        self.assertEqual(ns['filter_get_platform']({'tool': True}, 'linux-arm64', 'linux-arm64'), 'linux-arm64')

    def test_actual_upstream_rejects_completed_dependency_after_invalidation(self):
        ns = self.upstream_namespace()
        dep = {'check': {'headers': ['zlib.h']}, 'fetch': {'git': 'example', 'tag': 'v1'},
               'configure': {'cmake': [{'flags': []}]}}
        header = self.core / 'deps/zlib/include/zlib.h'
        header.parent.mkdir(parents=True)
        header.write_text('header')
        stamp = self.core / 'deps/zlib/stamp'
        (stamp/'linux-arm64').mkdir(parents=True)
        (stamp/'.fetchinfo').write_text('example;v1')
        (stamp/'linux-arm64/.configureinfo').write_text('')
        with mock.patch.object(ns['os'], 'getcwd', return_value=str(self.core)):
            self.assertTrue(ns['check_dependency']('zlib', dep, 'linux-arm64', False))
            self.sa._invalidate_dependency_settings(self.sa._dependency_settings({}))
            self.assertFalse(ns['check_dependency']('zlib', dep, 'linux-arm64', False))


if __name__ == '__main__':
    unittest.main()
