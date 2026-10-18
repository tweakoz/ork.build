"""Upgrade regressions without downloading or compiling dependencies."""
import ast
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('artifacts', ROOT/'scripts/obt/dependency_artifacts.py')
artifacts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(artifacts)


class InstalledProvider:
    # Simulate an existing unversioned manifest and no explicit --force.
    @property
    def should_build(self):
        return False


def provider(name, stage, suffix='.cpython-314t-aarch64-linux-gnu.so'):
    tree = ast.parse((ROOT/'modules/dep'/f'{name}.py').read_text())
    class_name = '_llvm_from_source' if name == 'llvm' else name
    original = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == class_name)
    wanted = {'areRequiredBinaryFilesPresent', 'areRequiredSourceFilesPresent',
              'should_build', '_python_module_path', 'onPostInstall'}
    methods = [x for x in original.body if isinstance(x, ast.FunctionDef) and x.name in wanted]
    constants = [x for x in original.body if isinstance(x, ast.Assign)]
    cls = ast.ClassDef(name='Subject', bases=[ast.Name(id='InstalledProvider', ctx=ast.Load())],
                      keywords=[], body=constants+methods, decorator_list=[])
    python = types.SimpleNamespace(executable=stage/'pyvenv/bin/python3',
                                   pylib_dir=stage/'pyvenv/lib/python3.14t')
    namespace = dict(vars(artifacts))
    namespace.update(InstalledProvider=InstalledProvider,
        path=types.SimpleNamespace(libs=lambda:stage/'lib', includes=lambda:stage/'include',
                                  bin=lambda:stage/'bin', stage=lambda:stage, prefix=lambda:stage),
        host=types.SimpleNamespace(IsDarwin=False), subprocess=subprocess,
        dep=types.SimpleNamespace(instance=lambda _:python),
        python_extension_suffix=lambda executable:suffix)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 str(ROOT/'modules/dep'/f'{name}.py'), 'exec'), namespace)
    obj = namespace['Subject']()
    obj.shlib_extension = 'so'
    obj.llvm = types.SimpleNamespace(version='21.1.8')
    obj.bitcode_compiler = stage/'bin/ork.clang++-21'
    return obj, namespace


def put(root, name, contents='artifact'):
    p = root/name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(contents)
    return p


class UpgradeTests(unittest.TestCase):
    def test_old_manifest_does_not_hide_missing_new_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ('llvm', 'clang', 'embree', 'igl', 'openvdb', 'osl'):
                with self.subTest(provider=name):
                    obj, _ = provider(name, Path(d))
                    self.assertTrue(obj.should_build)

    def test_versions_and_complete_artifacts_satisfy_existing_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            # Stale version metadata must not satisfy the upgraded dependency.
            fixtures = {
                'embree': ('include/embree4/rtcore_config.h', 'RTC_VERSION_', '4.4.1', ['lib/libembree4.so']),
                'osl': ('include/OSL/oslversion.h', 'OSL_LIBRARY_VERSION_', '1.15.7.0',
                        ['bin/oslc', 'lib/liboslexec.so', 'lib/liboslcomp.so', 'lib/liboslquery.so']),
                'openvdb': ('include/openvdb/version.h', 'OPENVDB_LIBRARY_', '13.1.0',
                            ['lib/libopenvdb.so', 'lib/libopenvdb_ax.so',
                             'pyvenv/lib/python3.14t/site-packages/openvdb.cpython-314t-aarch64-linux-gnu.so']),
            }
            put(root, 'include/openvdb/tree/InternalNode.h',
                '// Tile values are not child pointers and have no node version.')
            for name, (header, prefix, version, files) in fixtures.items():
                with self.subTest(provider=name):
                    obj, _ = provider(name, root)
                    for f in files: put(root, f)
                    put(root, header, '#define '+prefix+'MAJOR 0\n')
                    self.assertTrue(obj.should_build)
                    put(root, header, '\n'.join('#define '+prefix+part+('_VERSION_NUMBER' if name == 'openvdb' else '')+' '+n for part,n in
                                               zip(('MAJOR','MINOR','PATCH','TWEAK'),version.split('.'))))
                    self.assertFalse(obj.should_build)
                    (root/files[-1]).unlink()
                    self.assertTrue(obj.should_build)
            put(root, 'include/igl/embree/EmbreeIntersector.h')
            put(root, 'lib/libtriangle.a')
            obj, _ = provider('igl', root)
            put(root, 'lib/cmake/igl/libigl-config-version.cmake', 'set(PACKAGE_VERSION "2.5.0")')
            self.assertTrue(obj.should_build)
            put(root, 'lib/cmake/igl/libigl-config-version.cmake', 'set(PACKAGE_VERSION "2.6.0")')
            self.assertFalse(obj.should_build)

    def test_compiler_versions_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for f in ('lib/libLLVM.so', 'include/llvm/Config/llvm-config.h',
                      'bin/ork.clang++-21', 'lib/libclang-cpp.so',
                      'include/clang/Frontend/CompilerInstance.h'):put(root,f)
            for name in ('llvm','clang'):
                obj, _ = provider(name, root)
                with patch.object(artifacts.subprocess, 'check_output', return_value='version 18.1.8'):
                    self.assertTrue(obj.should_build)
                with patch.object(artifacts.subprocess, 'check_output', return_value='version 21.1.8'):
                    self.assertFalse(obj.should_build)
                with patch.object(artifacts.subprocess, 'check_output', side_effect=OSError):
                    self.assertTrue(obj.should_build)

    def test_linux_versioned_clang_library_is_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for f in ('bin/ork.clang++-21', 'lib/libclang-cpp.so.21.1',
                      'include/clang/Frontend/CompilerInstance.h'):put(root, f)
            obj, _ = provider('clang', root)
            with patch.object(artifacts.subprocess, 'check_output', return_value='clang version 21.1.8'):
                self.assertFalse(obj.should_build)

    def test_vdb_postinstall_does_not_copy_stale_extension(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for suffix in ('.cpython-314t-x86_64-linux-gnu.so', '.cpython-314t-aarch64-linux-gnu.so'):
                obj, _ = provider('openvdb', root, suffix)
                old = put(root, 'lib/python3.14t/site-packages/openvdb'+suffix, 'old ABI')
                new = put(root, 'pyvenv/lib/python3.14t/site-packages/openvdb'+suffix, 'new ABI')
                self.assertTrue(obj.onPostInstall())
                self.assertEqual(new.read_text(), 'new ABI')
                self.assertEqual(old.read_text(), 'old ABI')
                new.unlink()
                with self.assertRaises(RuntimeError):obj.onPostInstall()

    def test_slang_cached_tag_does_not_override_head(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            obj, ns = provider('slang', root)
            obj.source_root = root
            put(root, 'CMakeLists.txt')
            ns.update(MODULES=[], VERSION='2026.18', REVISION='expected')
            with patch.object(subprocess, 'check_output', side_effect=['expected\n','different\n']):
                self.assertFalse(obj.areRequiredSourceFilesPresent())
            with patch.object(subprocess, 'check_output', side_effect=['expected\n','expected\n']):
                self.assertTrue(obj.areRequiredSourceFilesPresent())

    def test_target_python_is_isolated_and_suffix_validated(self):
        with patch.object(artifacts.subprocess, 'check_output', return_value='.cpython-314t-darwin.so\n') as p:
            self.assertEqual(artifacts.python_extension_suffix('/target/python'), '.cpython-314t-darwin.so')
            self.assertEqual(p.call_args.args[0][:3], ['/target/python','-I','-c'])
        with patch.object(artifacts.subprocess, 'check_output', return_value='../wrong.so'):
            with self.assertRaises(RuntimeError):artifacts.python_extension_suffix('/target/python')


if __name__ == '__main__':
    unittest.main()
