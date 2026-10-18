"""Shared download cache: atomic wget writes and pinned tag-tarball checksums."""
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from obt import wget as wget_mod


def load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCommand:
    """Stands in for obt.command.Command(["wget","-O",out,url])."""
    behavior = None  # callable(out_path) -> rc
    seen = []

    def __init__(self, argv, **kwargs):
        self.out = Path(argv[2])

    def exec(self):
        FakeCommand.seen.append(self.out)
        return FakeCommand.behavior(self.out)


def run_once(invoke, **kwargs):
    return invoke()


class AtomicWgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dl = Path(self.tmp.name)
        FakeCommand.seen = []
        patches = [mock.patch.object(wget_mod.obt.path, 'downloads', return_value=self.dl),
                   mock.patch.object(wget_mod, 'Command', FakeCommand),
                   mock.patch.object(wget_mod, 'retry_until_rc_zero', run_once)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_success_writes_temp_then_renames(self):
        def ok(out):
            self.assertFalse((self.dl / 'x.tar.gz').exists())
            out.write_bytes(b'payload')
            return 0
        FakeCommand.behavior = ok
        result = wget_mod.wget(urls=['u'], output_name='x.tar.gz')
        self.assertEqual(result, self.dl / 'x.tar.gz')
        self.assertEqual(result.read_bytes(), b'payload')
        self.assertNotEqual(FakeCommand.seen[0], result)
        self.assertEqual(FakeCommand.seen[0].parent, self.dl)
        self.assertEqual(sorted(p.name for p in self.dl.iterdir()), ['x.tar.gz'])

    def test_failed_download_leaves_no_partial_final_or_temp(self):
        def partial_then_fail(out):
            out.write_bytes(b'trunc')
            return 1
        FakeCommand.behavior = partial_then_fail
        self.assertIsNone(wget_mod.wget(urls=['u'], output_name='x.tar.gz'))
        self.assertEqual(list(self.dl.iterdir()), [])

    def test_failed_download_preserves_existing_cached_file(self):
        (self.dl / 'x.tar.gz').write_bytes(b'good')
        FakeCommand.behavior = lambda out: (out.write_bytes(b'trunc'), 1)[1]
        self.assertIsNone(wget_mod.wget(urls=['u'], output_name='x.tar.gz'))
        self.assertEqual((self.dl / 'x.tar.gz').read_bytes(), b'good')
        self.assertEqual([p.name for p in self.dl.iterdir()], ['x.tar.gz'])

    def test_md5_mismatch_never_reaches_final_path(self):
        FakeCommand.behavior = lambda out: (out.write_bytes(b'wrong'), 0)[1]
        want = hashlib.md5(b'right').hexdigest()
        self.assertIsNone(wget_mod.wget(urls=['u'], output_name='x.tar.gz', md5val=want))
        self.assertEqual(list(self.dl.iterdir()), [])

    def test_md5_mismatch_falls_through_to_next_url(self):
        bodies = {'bad': b'rerolled', 'good': b'right'}
        urls = []
        class ByUrl(FakeCommand):
            def __init__(self, argv, **kwargs):
                super().__init__(argv); urls.append(argv[3])
        FakeCommand.behavior = lambda out: (out.write_bytes(bodies[urls[-1]]), 0)[1]
        want = hashlib.md5(b'right').hexdigest()
        with mock.patch.object(wget_mod, 'Command', ByUrl):
            result = wget_mod.wget(urls=['bad', 'good'], output_name='x.tar.gz', md5val=want)
        self.assertEqual(urls, ['bad', 'good'])
        self.assertEqual(result.read_bytes(), b'right')
        self.assertEqual([p.name for p in self.dl.iterdir()], ['x.tar.gz'])

    def test_all_urls_mismatch_prints_repin_hint(self):
        FakeCommand.behavior = lambda out: (out.write_bytes(b'wrong'), 0)[1]
        want = hashlib.md5(b'right').hexdigest()
        with mock.patch('builtins.print') as printed:
            self.assertIsNone(wget_mod.wget(urls=['a', 'b'], output_name='x.tar.gz', md5val=want))
        text = '\n'.join(' '.join(map(str, c.args)) for c in printed.call_args_list)
        self.assertEqual(len(FakeCommand.seen), 2)
        self.assertIn(want, text)
        self.assertIn(hashlib.md5(b'wrong').hexdigest(), text)
        self.assertIn('re-pin md5val', text)
        self.assertEqual(list(self.dl.iterdir()), [])

    def test_stale_part_files_are_reaped(self):
        old = self.dl / 'x.tar.gz.part.111'
        fresh = self.dl / 'x.tar.gz.part.222'
        other = self.dl / 'y.tar.gz.part.333'
        for p in (old, fresh, other):
            p.write_bytes(b'partial')
        aged = wget_mod.time.time() - 7 * 3600
        os.utime(old, (aged, aged)); os.utime(other, (aged, aged))
        FakeCommand.behavior = lambda out: 1
        wget_mod.wget(urls=['u'], output_name='x.tar.gz')
        self.assertFalse(old.exists())
        self.assertTrue(fresh.exists())   # may belong to a live concurrent download
        self.assertTrue(other.exists())   # another artifact's parts are not ours

    def test_md5_hit_skips_download(self):
        (self.dl / 'x.tar.gz').write_bytes(b'right')
        FakeCommand.behavior = lambda out: self.fail('should not download')
        want = hashlib.md5(b'right').hexdigest()
        self.assertEqual(wget_mod.wget(urls=['u'], output_name='x.tar.gz', md5val=want), self.dl / 'x.tar.gz')


class PinnedTarballTests(unittest.TestCase):
    def test_llvm_fetcher_has_md5(self):
        llvm = load('llvm_dep_dlcache', 'modules/dep/llvm.py')
        cls = llvm._llvm_from_source
        fetcher = cls._fetcher.fget(cls.__new__(cls))
        self.assertEqual(fetcher._md5val, '6a8a4e9a04fe419251e8386358c8051e')

    def test_openvdb_fetcher_has_md5(self):
        vdb = load('openvdb_dep_dlcache', 'modules/dep/openvdb.py')
        cls = vdb.openvdb
        fetcher = cls._fetcher.fget(cls.__new__(cls))
        self.assertEqual(fetcher._md5val, '38db693867593b4731ea8dbf566708f5')


if __name__ == '__main__':
    unittest.main()
