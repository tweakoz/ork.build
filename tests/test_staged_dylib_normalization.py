"""Staging dylib normalization (macOS), Linux cmake rpath defaults, openexr pins."""
import importlib.util
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
from obt import dep, macos, _dep_provider, _dep_build_cmake

MACHO = bytes.fromhex('cffaedfe') + b'fixture'
EXE = '@executable_path/../lib/'


def load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MachoTools:
    """Models otool -l / install_name_tool / codesign over a metadata dict
    keyed by real path; records every invocation."""
    def __init__(self, metadata, unsignable=()):
        self.metadata = metadata
        self.unsignable = set(unsignable)
        self.calls = []

    def run(self, argv, **kwargs):
        args = [str(a) for a in argv]
        self.calls.append(args)
        tool, target = args[0], args[-1]
        if tool == 'otool':
            info = self.metadata[target]
            out = target + ':\n'
            cmds = ([('LC_ID_DYLIB', 'name', info['id'])] if info['id'] else [])
            cmds += [(kind, 'name', ref) for kind, ref in info['deps']]
            cmds += [('LC_RPATH', 'path', r) for r in info['rpaths']]
            for i, (kind, field, value) in enumerate(cmds):
                out += 'Load command %d\n      cmd %s\n  cmdsize 56\n   %s %s (offset 24)\n' % (
                    i, kind, field, value)
            return SimpleNamespace(returncode=0, stdout=out, stderr='')
        if tool == 'install_name_tool':
            info = self.metadata[target]
            if args[1] == '-add_rpath':
                if args[2] in info['rpaths']:
                    return SimpleNamespace(returncode=1, stdout='', stderr='would duplicate path')
                info['rpaths'].append(args[2])
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            i = 1
            while i < len(args) - 1:
                if args[i] == '-id':
                    info['id'] = args[i + 1]; i += 2
                elif args[i] == '-change':
                    info['deps'] = [(k, args[i + 2] if r == args[i + 1] else r) for k, r in info['deps']]
                    i += 3
                else:
                    raise AssertionError('unexpected install_name_tool arg ' + args[i])
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        if tool == 'codesign':
            assert args[1:4] == ['-s', '-', '-f'], args
            rc = 1 if target in self.unsignable else 0
            return SimpleNamespace(returncode=rc, stdout='', stderr='sign failed' if rc else '')
        raise AssertionError('unexpected tool ' + repr(args))

    def mutating(self):
        return [c for c in self.calls if c[0] in ('install_name_tool', 'codesign')]


class NormalizeStagedDylibsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='stage norm-')
        self.addCleanup(tmp.cleanup)
        self.lib = Path(os.path.realpath(tmp.name)) / 'lib'
        self.lib.mkdir()

    def dylib(self, rel, id, deps=(), rpaths=()):
        p = self.lib / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(MACHO)
        self.meta[str(p)] = dict(id=id, deps=list(deps), rpaths=list(rpaths))
        return str(p)

    def run_norm(self, tools, **kw):
        with mock.patch.object(macos.subprocess, 'run', tools.run):
            return macos.normalize_staged_dylibs(self.lib, **kw)

    def test_ids_all_load_kinds_rpath_resign_and_idempotence(self):
        self.meta = {}
        lib = str(self.lib)
        imath = self.dylib('libImath.dylib', EXE + 'libImath.dylib')
        exr = self.dylib('libOpenEXR.dylib', lib + '/libOpenEXR.dylib',
                         deps=[('LC_LOAD_DYLIB', EXE + 'libImath.dylib'),
                               ('LC_LOAD_WEAK_DYLIB', lib + '/libImath.dylib'),
                               ('LC_LOAD_DYLIB', '/usr/lib/libSystem.B.dylib')],
                         rpaths=[lib])
        ssl = self.dylib('libssl.dylib', '/opt/local/lib/libssl.dylib',
                         deps=[('LC_REEXPORT_DYLIB', EXE + 'libcrypto.dylib')])
        auto = self.dylib('libgmp.dylib', '/somewhere/else/lib/libgmp.dylib')
        (self.lib / 'libImath.3.dylib').symlink_to('libImath.dylib')
        (self.lib / 'notmacho.dylib').write_text('INPUT(-lfoo)')
        tools = MachoTools(self.meta)
        counts = self.run_norm(tools)
        self.assertEqual(self.meta[imath]['id'], '@rpath/libImath.dylib')
        self.assertEqual(self.meta[exr]['id'], lib + '/libOpenEXR.dylib')  # staging-absolute ID kept
        self.assertEqual([r for _, r in self.meta[exr]['deps']],   # staging-absolute load kept
                         ['@rpath/libImath.dylib', lib + '/libImath.dylib', '/usr/lib/libSystem.B.dylib'])
        self.assertEqual(self.meta[exr]['rpaths'], [lib])          # already present: not re-added
        self.assertEqual(self.meta[ssl]['id'], '/opt/local/lib/libssl.dylib')  # foreign absolute ID kept
        self.assertEqual(self.meta[ssl]['deps'], [('LC_REEXPORT_DYLIB', '@rpath/libcrypto.dylib')])
        self.assertEqual(self.meta[ssl]['rpaths'], [lib])          # gained an @rpath load -> rpath added
        self.assertEqual(self.meta[auto]['id'], '/somewhere/else/lib/libgmp.dylib')
        self.assertEqual(self.meta[imath]['rpaths'], [])           # no @rpath loads -> no rpath needed
        signed = {c[-1] for c in tools.calls if c[0] == 'codesign'}
        self.assertEqual(signed, {imath, exr, ssl})
        self.assertEqual(counts['scanned'], 4)                     # symlink once, text file skipped
        self.assertEqual((counts['ids'], counts['loads'], counts['rpaths'], counts['resigned']),
                         (1, 2, 1, 3))
        self.assertFalse(any(auto in c for c in tools.mutating()))
        tools.calls.clear()
        again = self.run_norm(tools)
        self.assertEqual(tools.mutating(), [])
        self.assertEqual(again['nonconforming'], 0)

    def test_check_only_reports_and_never_edits(self):
        self.meta = {}
        self.dylib('libfmt.dylib', EXE + 'libfmt.dylib')
        self.dylib('libok.dylib', '@rpath/libok.dylib')
        tools = MachoTools(self.meta)
        counts = self.run_norm(tools, check_only=True)
        self.assertEqual(tools.mutating(), [])
        self.assertEqual((counts['scanned'], counts['nonconforming'], counts['ids']), (2, 1, 1))
        self.assertEqual(self.meta[str(self.lib / 'libfmt.dylib')]['id'], EXE + 'libfmt.dylib')

    def test_framework_binaries_keep_framework_relative_path(self):
        self.meta = {}
        inner = 'png.framework/Versions/1.6/png'
        png = self.dylib(inner, EXE + inner, rpaths=['@loader_path/../../..'])
        (self.lib / 'png.framework/Versions/Current').symlink_to('1.6')
        (self.lib / 'png.framework/png').symlink_to('Versions/Current/png')
        (self.lib / 'png.framework/Versions/1.6/Info.plist').write_text('<plist/>')
        oiio = self.dylib('libOpenImageIO.dylib', '@rpath/libOpenImageIO.dylib',
                          deps=[('LC_LOAD_DYLIB', EXE + inner)])
        tools = MachoTools(self.meta)
        counts = self.run_norm(tools)
        self.assertEqual(self.meta[png]['id'], '@rpath/' + inner)
        self.assertEqual(self.meta[png]['rpaths'], ['@loader_path/../../..'])
        self.assertEqual(self.meta[oiio]['deps'], [('LC_LOAD_DYLIB', '@rpath/' + inner)])
        self.assertEqual(self.meta[oiio]['rpaths'], [str(self.lib)])
        self.assertEqual(counts['scanned'], 2)
        self.assertEqual({c[-1] for c in tools.calls if c[0] == 'codesign'}, {png, oiio})

    def test_signing_failure_warns_and_continues(self):
        self.meta = {}
        a = self.dylib('liba.dylib', EXE + 'liba.dylib')
        b = self.dylib('libb.dylib', EXE + 'libb.dylib')
        tools = MachoTools(self.meta, unsignable={a})
        counts = self.run_norm(tools)
        self.assertEqual(self.meta[b]['id'], '@rpath/libb.dylib')
        self.assertEqual((counts['resigned'], counts['failed']), (1, 1))

    def test_double_rpath_load_collapses_and_is_idempotent(self):
        self.meta = {}
        lib = str(self.lib)
        vdb = self.dylib('libopenvdb.dylib', '@rpath/libopenvdb.13.1.dylib',
                         deps=[('LC_LOAD_DYLIB', '@rpath/@rpath/libboost_iostreams-mt-a64.dylib'),
                               ('LC_LOAD_DYLIB', '@rpath/libblosc.dylib')],
                         rpaths=[lib])
        tools = MachoTools(self.meta)
        counts = self.run_norm(tools)
        self.assertEqual([r for _, r in self.meta[vdb]['deps']],
                         ['@rpath/libboost_iostreams-mt-a64.dylib', '@rpath/libblosc.dylib'])
        self.assertEqual((counts['ids'], counts['loads'], counts['resigned'], counts['failed']),
                         (0, 1, 1, 0))
        tools.calls.clear()
        self.assertEqual(self.run_norm(tools)['nonconforming'], 0)
        self.assertEqual(tools.mutating(), [])

    def test_replace_loadpaths_never_yields_double_rpath(self):
        io = 'libboost_iostreams-mt-a64.dylib'
        deps = ['@rpath/' + io, io]
        calls = []
        with mock.patch.object(macos.host, 'IsOsx', True), \
             mock.patch.object(macos, 'macho_enumerate_dylibs', return_value=deps), \
             mock.patch.object(macos, 'run', lambda argv, **kw: calls.append(argv)):
            macos.macho_replace_loadpaths('/x.dylib', io, '@rpath/' + io)
        self.assertEqual(calls, [['install_name_tool', '-change', io, '@rpath/' + io, '/x.dylib']])


class OpenvdbLoadRewriteTests(unittest.TestCase):
    IO = 'libboost_iostreams-mt-a64.dylib'

    def rewrite(self, vdb, loads):
        calls = []
        def fake_run(argv, **kw):
            args = [str(a) for a in argv]
            calls.append(args)
            if args[0] == 'install_name_tool':
                i = 1
                while i < len(args) - 1:
                    assert args[i] == '-change', args
                    loads[:] = [args[i + 2] if l == args[i + 1] else l for l in loads]
                    i += 3
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        with mock.patch.object(vdb.macos, 'macho_enumerate_dylibs', lambda p: list(loads)), \
             mock.patch.object(vdb.subprocess, 'run', fake_run):
            changes = vdb.rpath_openvdb_loads('/stage/lib/libopenvdb.dylib', self.IO)
        return changes, calls

    def test_exact_rewrite_and_idempotence(self):
        vdb = load('openvdb_dep_rewrite', 'modules/dep/openvdb.py')
        io = self.IO
        for start in ([io, '@rpath/libblosc.dylib', '/usr/lib/libc++.1.dylib'],
                      [EXE + io, EXE + 'libtbb.dylib', '@rpath/libblosc.dylib'],
                      ['@rpath/' + io, '@rpath/libblosc.dylib'],
                      ['@rpath/@rpath/' + io, '@rpath/libblosc.dylib']):
            loads = list(start)
            changes, calls = self.rewrite(vdb, loads)
            self.assertIn('@rpath/' + io, loads, start)
            self.assertFalse(any(l.startswith('@rpath/@rpath/') for l in loads), loads)
            self.assertFalse(any(l.startswith('@executable_path') for l in loads), loads)
            self.assertIn('/usr/lib/libc++.1.dylib' in start, ['/usr/lib/libc++.1.dylib' in loads])
            if start[0] == '@rpath/' + io:
                self.assertEqual((changes, calls), ([], []))   # already @rpath: untouched
            else:
                self.assertEqual(calls[-1][:4], ['codesign', '-s', '-', '-f'])
            settled = list(loads)
            changes, calls = self.rewrite(vdb, loads)          # second run changes nothing
            self.assertEqual((changes, calls, loads), ([], [], settled))


class ProviderHookTests(unittest.TestCase):
    def provider(self):
        p = _dep_provider.Provider.__new__(_dep_provider.Provider)
        p._name = 'x'
        return p

    def test_hook_runs_on_darwin_and_never_raises(self):
        with mock.patch.object(_dep_provider.host, 'IsDarwin', True), \
             mock.patch.object(_dep_provider.path, 'libs', return_value=Path('/stage/lib')), \
             mock.patch.object(macos, 'normalize_staged_dylibs', side_effect=RuntimeError('boom')) as norm:
            self.provider().normalizeStagedLibs()
        norm.assert_called_once_with(Path('/stage/lib'))

    def test_hook_is_noop_off_darwin(self):
        with mock.patch.object(_dep_provider.host, 'IsDarwin', False), \
             mock.patch.object(macos, 'normalize_staged_dylibs') as norm:
            self.provider().normalizeStagedLibs()
        norm.assert_not_called()


class LinuxCmakeRpathTests(unittest.TestCase):
    def test_linux_builder_emits_origin_rpaths(self):
        host = _dep_build_cmake.obt.host
        with mock.patch.object(host, 'IsOsx', False), mock.patch.object(host, 'IsLinux', True), \
             mock.patch.object(_dep_build_cmake.path, 'libs', return_value=Path('/stage/lib')):
            builder = _dep_build_cmake.CMakeBuilder('somedep')
        args = builder.cmakeEnvAsStringList
        self.assertIn('-DCMAKE_INSTALL_RPATH=$ORIGIN;$ORIGIN/../lib;/stage/lib', args)
        self.assertIn('-DCMAKE_INSTALL_RPATH_USE_LINK_PATH:BOOL=ON', args)
        self.assertIn('-DCMAKE_SKIP_INSTALL_RPATH:BOOL=NO', args)
        self.assertIn('-DCMAKE_BUILD_RPATH_USE_ORIGIN:BOOL=ON', args)
        self.assertFalse(any('CMAKE_INSTALL_NAME_DIR' in a for a in args))

    def test_dep_override_still_wins(self):
        host = _dep_build_cmake.obt.host
        with mock.patch.object(host, 'IsOsx', False), mock.patch.object(host, 'IsLinux', True), \
             mock.patch.object(_dep_build_cmake.path, 'libs', return_value=Path('/stage/lib')):
            builder = _dep_build_cmake.CMakeBuilder('somedep')
        builder.setCmVar('CMAKE_INSTALL_RPATH', '/custom')
        self.assertIn('-DCMAKE_INSTALL_RPATH=/custom', builder.cmakeEnvAsStringList)


class OpenexrPinsTests(unittest.TestCase):
    def test_staged_libdeflate_wins_over_homebrew(self):
        exr = load('openexr_dep_pins', 'modules/dep/openexr.py')
        cmvars = {}
        fake = SimpleNamespace(setCmVar=lambda k, v: cmvars.__setitem__(k, v))
        cls = exr.openexr
        with mock.patch.object(exr.dep.StdProvider, '__init__', lambda self, name: None), \
             mock.patch.object(cls, 'declareDep', lambda self, n: None, create=True), \
             mock.patch.object(cls, 'createBuilder', lambda self, c: fake, create=True), \
             mock.patch.object(cls, 'source_root', Path('/src'), create=True), \
             mock.patch.object(exr.path, 'prefix', return_value=Path('/stage')), \
             mock.patch.object(exr.path, 'libs', return_value=Path('/stage/lib')):
            cls()
        self.assertEqual(cmvars['CMAKE_PREFIX_PATH'], '/stage')
        self.assertIn('/opt/homebrew', cmvars['CMAKE_IGNORE_PATH'].split(';'))
        self.assertEqual(cmvars['libdeflate_DIR'], '/stage/lib/cmake/libdeflate')


if __name__ == '__main__':
    unittest.main()
