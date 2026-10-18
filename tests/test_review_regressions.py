"""Regression coverage for commit-review fixes; native Mach-O cases need macOS."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from obt import macos
from obt.net import client


def load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildEnvironmentTests(unittest.TestCase):
    def test_h5py_removes_conflicting_inherited_settings(self):
        h5 = load('h5py_dep_review', 'modules/dep/h5py.py')
        hdf = SimpleNamespace(include_dir='/stage/include/hdf5', lib_dir='/stage/lib', VERSION='2.1.1')
        with mock.patch.dict(os.environ, {'HDF5_DIR': '/old/hdf5', 'HDF5_PKGCONFIG_NAME': 'other-hdf5'}), mock.patch.object(h5.dep, 'instance', return_value=hdf), mock.patch.object(h5.path, 'libs', return_value=Path('/stage/lib')):
            environment = h5.Command(['unused'], environment=h5._build_env()).env
        self.assertNotIn('HDF5_DIR', environment)
        self.assertNotIn('HDF5_PKGCONFIG_NAME', environment)
        self.assertEqual(environment['HDF5_INCLUDEDIR'], hdf.include_dir)
        self.assertEqual(environment['HDF5_LIBDIR'], hdf.lib_dir)

    def test_bootstrap_rejects_relative_paths_before_any_work(self):
        c = client.Client.__new__(client.Client)
        with mock.patch.object(c, '_local_git') as local, mock.patch.object(c, 'run') as remote:
            for path in ('repo', './repo', '../repo', '~/repo', 'C:repo'):
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'absolute remote'):
                    c.gitbootstrap('node', '/unused', path)
            local.assert_not_called()
            remote.assert_not_called()

    def test_bootstrap_accepts_posix_and_windows_absolute_paths(self):
        c = client.Client.__new__(client.Client)
        with mock.patch.object(c, '_local_git', return_value=(1, '')) as local:
            for path in ('/tmp/repo', 'C:\\repos\\test', '\\\\server\\share\\test'):
                with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'not a git repo'):
                    c.gitbootstrap('node', '/unused', path)
            self.assertEqual(local.call_count, 3)


class MachOParsingTests(unittest.TestCase):
    def test_all_dependency_commands_and_paths_with_spaces(self):
        commands = ['LC_LOAD_DYLIB', 'LC_LOAD_WEAK_DYLIB', 'LC_REEXPORT_DYLIB', 'LC_LOAD_UPWARD_DYLIB', 'LC_LAZY_LOAD_DYLIB']
        output = '\n'.join(f'Load command {i}\n cmd {cmd}\n name /stage with spaces/lib{i}.dylib (offset 24)' for i, cmd in enumerate(commands))
        output += '\nLoad command 5\n cmd LC_ID_DYLIB\n name /own/id (offset 24)\n'
        output += 'Load command 6\n cmd LC_RPATH\n path /stage with spaces/lib (offset 12)\n'
        with mock.patch.object(macos.host, 'IsOsx', True), mock.patch.object(macos.subprocess, 'run', return_value=SimpleNamespace(stdout=output)):
            self.assertEqual(macos.macho_enumerate_dylibs('unused'), [f'/stage with spaces/lib{i}.dylib' for i in range(5)])
            self.assertEqual(macos.macho_enumerate_rpaths('unused'), ['/stage with spaces/lib'])


@unittest.skipUnless(sys.platform == 'darwin', 'requires macOS linker and signing tools')
class MachOCloneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='obt-clone-review-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / 'source stage'
        self.dest = self.root / 'destination stage'
        (self.source / 'lib').mkdir(parents=True)
        (self.source / 'obt-launch-env').write_text('#!/bin/sh\n')
        self.a = self.root / 'a.c'; self.a.write_text('int foo(void) { return 7; }')
        self.b = self.root / 'b.c'; self.b.write_text('extern int foo(void); int bar(void) { return foo(); }')
        self.clone = load('stage_clone_review', 'bin_pub/obt.stage.clone.py')

    def run_command(self, argv):
        return subprocess.run(list(map(str, argv)), check=True, capture_output=True, text=True)

    def library(self, name, source, *flags):
        dest = self.source / 'lib' / name
        self.run_command(['clang', '-dynamiclib', source, '-o', dest, '-Wl,-headerpad_max_install_names', '-Wl,-install_name,' + str(dest), *flags])
        return dest

    def clone_stage(self, fixup):
        with mock.patch.object(self.clone, 'run_existing_fixup', side_effect=fixup), mock.patch.object(sys, 'argv', ['clone', '--source', str(self.source), '--dest', str(self.dest), '--full-copy']):
            self.clone.main()

    def test_weak_and_reexport_dependencies_relocate(self):
        a = self.library('liba.dylib', self.a)
        self.library('libweak.dylib', self.b, '-Wl,-weak_library,' + str(a))
        self.library('libreexport.dylib', self.b, '-Wl,-reexport_library,' + str(a))
        self.clone_stage(lambda *_: None)
        for name in ('libweak.dylib', 'libreexport.dylib'):
            deps = macos.macho_enumerate_dylibs(self.dest / 'lib' / name)
            self.assertNotIn(str(a), deps)
            self.assertIn(str(self.dest / 'lib/liba.dylib'), deps)
            self.run_command(['codesign', '--verify', self.dest / 'lib' / name])

    def test_final_fixup_is_resigned(self):
        a = self.library('liba.dylib', self.a)
        self.run_command(['install_name_tool', '-id', '@executable_path/../lib/liba.dylib', a])
        self.library('libb.dylib', self.b, str(a))
        def fixup(stage, _):
            self.run_command(['install_name_tool', '-change', '@executable_path/../lib/liba.dylib', '@rpath/liba.dylib', stage / 'lib/libb.dylib'])
        self.clone_stage(fixup)
        self.run_command(['codesign', '--verify', self.dest / 'lib/libb.dylib'])
        manifest = json.loads((self.dest / 'obt-stage-clone.json').read_text())
        self.assertIn('lib/libb.dylib', manifest['macho_files_resigned'])
        self.assertTrue(manifest['verification']['passed'])

    def test_final_fixup_cannot_reintroduce_source_dependencies(self):
        a = self.library('liba.dylib', self.a)
        self.library('libb.dylib', self.b, str(a))
        def fixup(stage, _):
            self.run_command(['install_name_tool', '-change', str(stage / 'lib/liba.dylib'), str(a), stage / 'lib/libb.dylib'])
        with self.assertRaisesRegex(RuntimeError, 'source-stage references remain'):
            self.clone_stage(fixup)
        self.assertFalse(self.dest.exists())
        self.assertTrue(a.exists())


if __name__ == '__main__':
    unittest.main()
