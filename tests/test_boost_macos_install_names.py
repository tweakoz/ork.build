"""Run directly to test the proposed Boost install-name normalization helper."""
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

HELPER_SOURCE = Path(os.environ.get(
    'OBT_BOOST_TEST_SOURCE',
    Path(__file__).resolve().parents[1] / 'modules/dep/boost.py'))


def load_helper(runner=subprocess):
    tree = ast.parse(HELPER_SOURCE.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'normalize_macos_boost_libraries')
    namespace = {'Path':Path, 'subprocess':runner}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(HELPER_SOURCE), 'exec'), namespace)
    return namespace[function.name]


class ToolFixture:
    """Model Mach-O inspection and edits while retaining every tool invocation."""
    def __init__(self, metadata):
        self.metadata = metadata
        self.calls = []
        self.CalledProcessError = subprocess.CalledProcessError
        self.PIPE = subprocess.PIPE
        self.STDOUT = subprocess.STDOUT
        self.DEVNULL = subprocess.DEVNULL

    def run(self, argv, **kwargs):
        args = [str(a) for a in argv]
        self.calls.append(args)
        command = Path(args[0]).name
        stdout = ''
        if command == 'otool':
            name = Path(args[-1]).name
            info = self.metadata[name]
            if '-l' in args:
                stdout = args[-1]+':\n'
                for index, (kind, ref) in enumerate([('LC_ID_DYLIB', info['id'])]+
                                                   [('LC_LOAD_DYLIB', r) for r in info['deps']]):
                    stdout += f'Load command {index}\n          cmd {kind}\n      cmdsize 128\n         name {ref} (offset 24)\n'
            elif '-D' in args:
                stdout = args[-1]+':\n'+info['id']+'\n'
            else:
                raise AssertionError('Unexpected otool mode')
        elif command == 'install_name_tool':
            info = self.metadata[Path(args[-1]).name]
            if '-id' in args:
                info['id'] = args[args.index('-id')+1]
            for i, arg in enumerate(args):
                if arg == '-change':
                    info['deps'] = [args[i+2] if item == args[i+1] else item for item in info['deps']]
        elif command != 'codesign':
            raise AssertionError('Unexpected tool: '+repr(args))
        return SimpleNamespace(returncode=0, stdout=stdout, stderr='')

    def check_output(self, argv, **kwargs):
        return self.run(argv, **kwargs).stdout


class NormalizationTests(unittest.TestCase):
    def test_ids_peer_references_signatures_and_idempotence(self):
        with tempfile.TemporaryDirectory(prefix='boost-names-') as directory:
            root = Path(directory)/'libraries with spaces'
            root.mkdir()
            names = ['libboost_leaf.dylib','libboost_middle.dylib','libboost_outer.dylib']
            for name in names:(root/name).write_text('fixture')
            (root/'libboost_alias.dylib').symlink_to(names[0])
            unrelated = '/usr/lib/libSystem.B.dylib'
            metadata = {
                names[0]:dict(id=names[0], deps=[unrelated]),
                names[1]:dict(id=str(root/names[1]), deps=[names[0], unrelated]),
                names[2]:dict(id='@rpath/'+names[2], deps=[str(root/names[1]), unrelated]),
            }
            tools = ToolFixture(metadata)
            normalize = load_helper(tools)
            normalize(root)
            for name in names:self.assertEqual(metadata[name]['id'], '@rpath/'+name)
            self.assertEqual(metadata[names[1]]['deps'], ['@loader_path/'+names[0],unrelated])
            self.assertEqual(metadata[names[2]]['deps'], ['@loader_path/'+names[1],unrelated])
            self.assertFalse(any('libboost_alias.dylib' in call[-1] for call in tools.calls))
            signed = {Path(call[-1]).name for call in tools.calls
                      if Path(call[0]).name == 'codesign' and '--sign' in call}
            verified = {Path(call[-1]).name for call in tools.calls
                        if Path(call[0]).name == 'codesign' and '--verify' in call}
            self.assertEqual(signed,set(names)); self.assertEqual(verified,set(names))
            for call in tools.calls:
                if Path(call[0]).name == 'codesign' and '--sign' in call:
                    self.assertIn('--force',call)
                    self.assertEqual(call[call.index('--sign')+1],'-')
            tools.calls.clear()
            normalize(root)
            self.assertFalse(any(Path(call[0]).name == 'install_name_tool' or
                                 (Path(call[0]).name == 'codesign' and '--sign' in call)
                                 for call in tools.calls))

    def test_check_only_is_read_only_and_tracks_repair(self):
        with tempfile.TemporaryDirectory(prefix='boost-check-') as directory:
            root = Path(directory)
            name = 'libboost_leaf.dylib'
            (root/name).write_text('fixture')
            tools = ToolFixture({name:dict(id=name, deps=[])})
            normalize = load_helper(tools)
            self.assertFalse(normalize(root, check_only=True))
            self.assertTrue(all(call[0] == 'otool' or
                                (call[0] == 'codesign' and '--verify' in call)
                                for call in tools.calls))
            self.assertEqual(tools.metadata[name]['id'], name)
            normalize(root)
            tools.calls.clear()
            self.assertTrue(normalize(root, check_only=True))
            self.assertTrue(all(call[0] == 'otool' or
                                (call[0] == 'codesign' and '--verify' in call)
                                for call in tools.calls))

    def test_missing_peer_is_an_error(self):
        with tempfile.TemporaryDirectory(prefix='boost-missing-') as directory:
            root=Path(directory);name='libboost_middle.dylib';(root/name).write_text('fixture')
            tools=ToolFixture({name:dict(id='@rpath/'+name,deps=['libboost_missing.dylib'])})
            with self.assertRaises((RuntimeError, FileNotFoundError)):
                load_helper(tools)(root)

    def test_non_boost_libraries_are_untouched(self):
        with tempfile.TemporaryDirectory(prefix='boost-unrelated-') as directory:
            root=Path(directory);(root/'libother.dylib').write_text('fixture')
            name='libboost_leaf.dylib'; (root/name).write_text('fixture')
            tools=ToolFixture({name:dict(id='@rpath/'+name,deps=[])})
            load_helper(tools)(root)
            self.assertFalse(any('libother.dylib' in call[-1] for call in tools.calls))


class ProviderRepairTests(unittest.TestCase):
    def provider(self, directory, normalize):
        # Execute the real provider methods without importing the OBT runtime.
        tree = ast.parse(HELPER_SOURCE.read_text())
        definition = next(node for node in tree.body
                          if isinstance(node, ast.ClassDef) and node.name == 'boost')
        class BaseProvider:
            should_build = False
        root = Path(directory)
        namespace = {
            'dep':SimpleNamespace(Provider=BaseProvider),
            'path':SimpleNamespace(libs=lambda:root/'lib',
                                   includes=lambda:root/'include', stage=lambda:root),
            'VERSION':['1','82','0'], 'subprocess':subprocess,
            'normalize_macos_boost_libraries':normalize,
        }
        exec(compile(ast.Module(body=[definition], type_ignores=[]),
                     str(HELPER_SOURCE), 'exec'), namespace)
        provider = object.__new__(namespace['boost'])
        provider._target = SimpleNamespace(os='macos')
        provider.architecture_suffix = 'a64'
        provider.supports_host = True
        provider.should_wipe = False
        provider.manifest = Mock()
        provider.manifest.exists.return_value = True
        provider.areRequiredBinaryFilesPresent = Mock(return_value=True)
        provider.areRequiredSourceFilesPresent = Mock(return_value=False)
        provider.download_and_extract = Mock()
        provider.build = Mock()
        return provider

    def test_stale_install_repairs_without_build_or_fetch(self):
        with tempfile.TemporaryDirectory(prefix='boost-provider-') as directory:
            events = []
            repaired = False
            def normalize(library, check_only=False):
                nonlocal repaired
                self.assertEqual(library, Path(directory)/'lib')
                if check_only:
                    return repaired
                events.append('normalize')
                repaired = True
            normalizer = Mock(side_effect=normalize)
            provider = self.provider(directory, normalizer)
            provider.manifest.touch.side_effect = lambda:events.append('manifest')
            self.assertTrue(provider.should_build)
            self.assertTrue(provider.provide())
            self.assertFalse(provider.should_build)
            self.assertEqual(events, ['normalize', 'manifest'])
            provider.build.assert_not_called()
            provider.download_and_extract.assert_not_called()
            provider.areRequiredSourceFilesPresent.assert_not_called()
            provider.manifest.touch.assert_called_once_with()

    def test_normalization_failure_never_marks_manifest(self):
        with tempfile.TemporaryDirectory(prefix='boost-provider-') as directory:
            normalize = Mock(side_effect=RuntimeError('broken dependency'))
            provider = self.provider(directory, normalize)
            self.assertTrue(provider.should_build)
            with self.assertRaisesRegex(RuntimeError, 'broken dependency'):
                provider.provide()
            provider.manifest.touch.assert_not_called()
            provider.build.assert_not_called()
            provider.download_and_extract.assert_not_called()


@unittest.skipUnless(sys.platform == 'darwin', 'requires native Mach-O tools')
class NativeLoaderTests(unittest.TestCase):
    def test_bare_peer_fails_then_loads_without_dyld_environment(self):
        normalize=load_helper()
        with tempfile.TemporaryDirectory(prefix='boost-native-') as directory:
            root=Path(directory);lib=root/'lib';lib.mkdir();other=root/'other';other.mkdir()
            leaf=lib/'libboost_leaf.dylib';middle=lib/'libboost_middle.dylib'
            (root/'leaf.c').write_text('int leaf(void) { return 41; }\n')
            (root/'middle.c').write_text('extern int leaf(void); int answer(void) { return leaf()+1; }\n')
            (root/'main.c').write_text('''#include <dlfcn.h>
#include <stdio.h>
int main(int argc, char** argv) {
  if (argc != 2) return 3;
  void* lib = dlopen(argv[1], RTLD_NOW);
  if (!lib) { fprintf(stderr, "%s\\n", dlerror()); return 2; }
  int (*answer)(void) = (int (*)(void))dlsym(lib, "answer");
  int ok = answer && answer() == 42;
  dlclose(lib);
  return ok ? 0 : 4;
}
''')
            environment={k:v for k,v in os.environ.items() if not k.startswith('DYLD_')}
            compiler=subprocess.check_output(['xcrun','--find','clang'],text=True).strip()
            sdk=subprocess.check_output(['xcrun','--sdk','macosx','--show-sdk-path'],text=True).strip()
            environment['SDKROOT']=sdk
            commands=[
                [compiler,'-isysroot',sdk,'-dynamiclib',str(root/'leaf.c'),'-Wl,-headerpad_max_install_names',
                 '-Wl,-install_name,libboost_leaf.dylib','-o',str(leaf)],
                [compiler,'-isysroot',sdk,'-dynamiclib',str(root/'middle.c'),str(leaf),'-Wl,-headerpad_max_install_names',
                 '-Wl,-install_name,libboost_middle.dylib','-o',str(middle)],
                [compiler,'-isysroot',sdk,str(root/'main.c'),'-o',str(root/'probe')],
            ]
            for command in commands:
                compiled=subprocess.run(command,capture_output=True,text=True,env=environment)
                self.assertEqual(compiled.returncode,0,compiled.stderr)
            command=[str(root/'probe'),str(middle)]
            failure=subprocess.run(command,cwd=other,env=environment,capture_output=True,text=True)
            self.assertNotEqual(failure.returncode,0)
            self.assertIn('libboost_leaf.dylib',failure.stderr)
            self.assertFalse(normalize(lib, check_only=True))
            normalize(lib)
            self.assertTrue(normalize(lib, check_only=True))
            for file in (leaf,middle):
                identity=subprocess.check_output(['otool','-D',str(file)],text=True)
                self.assertIn('@rpath/'+file.name,identity)
                subprocess.run(['codesign','--verify',str(file)],check=True,capture_output=True)
            dependencies=subprocess.check_output(['otool','-L',str(middle)],text=True)
            self.assertIn('@loader_path/'+leaf.name,dependencies)
            subprocess.run(command,cwd=other,env=environment,check=True,capture_output=True,text=True)
            before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (leaf,middle)}
            normalize(lib)
            self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (leaf,middle)})


if __name__ == '__main__':
    unittest.main(verbosity=2)
