"""SDK availability and configure-flow regression tests without building Python."""
import ast
import contextlib
import io
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1]/'modules/dep/python.py'


def functions():
    tree = ast.parse(SOURCE.read_text())
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'macos_function_cache')
    provider = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'python_from_source')
    build = next(n for n in provider.body if isinstance(n, ast.FunctionDef) and n.name == 'build')
    namespace = dict(os=os, shutil=shutil, shlex=shlex, subprocess=subprocess)
    exec(compile(ast.Module(body=[helper, build], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace


class AvailabilityTests(unittest.TestCase):
    def test_unavailable_functions_are_disabled_independently(self):
        check = functions()['macos_function_cache']
        for statuses, expected in [([0, 0, 0], []),
                ([0, 1, 0], ['ac_cv_func_dup3=no']),
                ([0, 0, 1], ['ac_cv_func_pipe2=no']),
                ([0, 1, 1], ['ac_cv_func_dup3=no', 'ac_cv_func_pipe2=no'])]:
            with self.subTest(statuses=statuses), patch.object(subprocess, 'run',
                    side_effect=[SimpleNamespace(returncode=n, stderr='probe diagnostic') for n in statuses]) as run:
                self.assertEqual(check({'SDKROOT':'/test-sdk', 'MACOSX_DEPLOYMENT_TARGET':'26.0'}), expected)
                inputs = [c.kwargs['input'] for c in run.call_args_list]
                self.assertIn('return 0;', inputs[0])
                self.assertIn('dup3(0, 1, O_CLOEXEC)', inputs[1])
                self.assertIn('pipe2(fds, O_CLOEXEC)', inputs[2])
                self.assertTrue(all('#include <unistd.h>' in text and '#include <fcntl.h>' in text for text in inputs))

    def test_broken_compiler_baseline_does_not_disable_every_function(self):
        with patch.object(subprocess, 'run', return_value=SimpleNamespace(returncode=1, stderr='bad SDK')) as run:
            with self.assertRaisesRegex(RuntimeError, 'bad SDK'):
                functions()['macos_function_cache']({'SDKROOT':'/missing-sdk'})
            self.assertEqual(run.call_count, 1)

    def test_compiler_and_flags_are_forwarded_without_shell_interpretation(self):
        inherited = {'CC':'compiler-wrapper clang', 'CFLAGS':'-O2 -DNAME="two words"',
                     'CPPFLAGS':'-I"/include with spaces"', 'SDKROOT':'/old-sdk'}
        with patch.dict(os.environ, inherited, clear=True), patch.object(subprocess, 'run',
                return_value=SimpleNamespace(returncode=0, stderr='')) as run:
            self.assertEqual(functions()['macos_function_cache'](
                {'SDKROOT':'/selected-sdk', 'MACOSX_DEPLOYMENT_TARGET':'26.0'},
                working_dir='/compile-directory'), [])
        for call in run.call_args_list:
            argv = call.args[0]
            self.assertEqual(argv[:5], ['compiler-wrapper','clang','-O2','-DNAME=two words','-I/include with spaces'])
            self.assertIn('-Werror=unguarded-availability', argv)
            self.assertIn('-Werror=unguarded-availability-new', argv)
            self.assertIn('-Werror=implicit-function-declaration', argv)
            self.assertEqual(argv[-4:], ['-x','c','-fsyntax-only','-'])
            self.assertEqual(call.kwargs['env']['SDKROOT'], '/selected-sdk')
            self.assertEqual(call.kwargs['env']['MACOSX_DEPLOYMENT_TARGET'], '26.0')
            self.assertEqual(call.kwargs['env']['CC'], 'compiler-wrapper clang')
            self.assertEqual(call.kwargs['cwd'], '/compile-directory')
            self.assertNotIn('shell', call.kwargs)


class BuildFlowTests(unittest.TestCase):
    def exercise(self, mac, configure_status, environment=None):
        temporary = tempfile.TemporaryDirectory(prefix='python-availability-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        commands = []
        def command(argv, **kwargs):
            commands.append((argv, kwargs))
            # Stop after make in successful-configure cases; do not enter install/venv setup.
            status = configure_status if argv[0] == '../configure' else 1
            return SimpleNamespace(exec=lambda:status)
        ns = functions()
        probe = Mock(return_value=['ac_cv_func_dup3=no','ac_cv_func_pipe2=no'])
        ns.update(host=SimpleNamespace(IsOsx=mac, NumCores=2), Command=command,
            dep=SimpleNamespace(require=Mock(return_value=True)),
            path=SimpleNamespace(builds=lambda:root/'builds', stage=lambda:root/'stage',
                                 osx_sdkdir=lambda:Path('/detected-sdk')),
            pathtools=SimpleNamespace(ensureDirectoryExists=lambda p:p.mkdir(parents=True,exist_ok=True)),
            env=SimpleNamespace(set=Mock(), prepend=Mock()), macos_function_cache=probe)
        subject = SimpleNamespace(source_dir=root/'source', home_dir=root/'pyvenv',
            download_and_extract=Mock(), _debug_build=False,
            _target=SimpleNamespace(architecture='test-arch'),
            openssl=SimpleNamespace(root=root/'stage',lib_dir=root/'stage/lib'),
            xz=SimpleNamespace(lib_dir=root/'stage/lib',include_dir=root/'stage/include'))
        obt = ModuleType('obt'); obt.macos = SimpleNamespace()
        with patch.dict(sys.modules, {'obt':obt}), patch.dict(os.environ, environment or {}, clear=True), \
                patch.object(subprocess, 'check_output', return_value='26.4\n') as swvers, \
                contextlib.redirect_stdout(io.StringIO()):
            result = ns['build'](subject)
        return result, commands, probe, swvers

    def test_linux_does_not_run_or_cache_macos_probes(self):
        result, commands, probe, swvers = self.exercise(False, 0)
        self.assertFalse(result)  # simulated make failure
        probe.assert_not_called(); swvers.assert_not_called()
        self.assertEqual([c[0][0] for c in commands], ['../configure','make'])
        for argv, kwargs in commands:
            self.assertEqual(kwargs['environment'], {})
            self.assertFalse(any(str(a).startswith('ac_cv_func_') for a in argv))

    def test_configure_failure_prevents_make_on_both_platforms(self):
        for mac in (False, True):
            with self.subTest(mac=mac):
                result, commands, _, _ = self.exercise(mac, 7)
                self.assertFalse(result)
                self.assertEqual([c[0][0] for c in commands], ['../configure'])

    def test_macos_configure_and_make_share_sdk_and_target(self):
        result, commands, probe, swvers = self.exercise(True, 0)
        self.assertFalse(result)
        expected = {'SDKROOT':'/detected-sdk', 'MACOSX_DEPLOYMENT_TARGET':'26.4'}
        probe.assert_called_once_with(expected, commands[0][1]['working_dir'])
        self.assertEqual(commands[0][1]['working_dir'], commands[1][1]['working_dir'])
        self.assertEqual([c[1]['environment'] for c in commands], [expected, expected])
        self.assertIn('ac_cv_func_dup3=no', commands[0][0])
        self.assertIn('ac_cv_func_pipe2=no', commands[0][0])
        self.assertEqual(swvers.call_args.args[0], ['sw_vers','-productVersion'])

    def test_explicit_sdk_and_target_are_preserved(self):
        expected = {'SDKROOT':'/chosen-sdk', 'MACOSX_DEPLOYMENT_TARGET':'25.0'}
        _, commands, probe, swvers = self.exercise(True, 7, expected)
        probe.assert_called_once_with(expected, commands[0][1]['working_dir'])
        swvers.assert_not_called()
        self.assertEqual(commands[0][1]['environment'], expected)


@unittest.skipUnless(sys.platform == 'darwin', 'requires native macOS SDK availability annotations')
class NativeSDKTests(unittest.TestCase):
    def test_sdk27_checks_both_deployment_targets(self):
        try:
            sdk = subprocess.check_output(['xcrun','--sdk','macosx','--show-sdk-path'], text=True).strip()
            version = subprocess.check_output(['xcrun','--sdk','macosx','--show-sdk-version'], text=True).strip()
            compiler = subprocess.check_output(['xcrun','--sdk','macosx','--find','clang'], text=True).strip()
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest('Native SDK unavailable: '+str(error))
        if int(version.split('.')[0]) < 27:
            self.skipTest('SDK 27 or newer is required for the positive availability check')
        check = functions()['macos_function_cache']
        with patch.dict(os.environ, {'PATH':os.environ.get('PATH','/usr/bin:/bin')}, clear=True):
            base = {'SDKROOT':sdk, 'CC':shlex.quote(compiler)}
            self.assertEqual(check(dict(base, MACOSX_DEPLOYMENT_TARGET='26.0')),
                             ['ac_cv_func_dup3=no','ac_cv_func_pipe2=no'])
            self.assertEqual(check(dict(base, MACOSX_DEPLOYMENT_TARGET='27.0')), [])


if __name__ == '__main__':
    unittest.main()
