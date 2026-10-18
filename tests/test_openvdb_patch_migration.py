"""Test the real provider migration without importing OBT or building OpenVDB.

Run: python3 -m unittest discover -s tests -p test_openvdb_patch_migration.py
Fixtures retain upstream hunk context from the legacy patch and fill untouched
lines with placeholders. This tests migration state and rollback, not C++ code.
"""
import ast
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class OpenVdbPatchMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        provider = Path(__file__).resolve().parents[1] / 'modules/dep/openvdb.py'
        cls.patches = provider.parent / 'patches'
        cls.legacy = cls.patches / 'openvdb-13.1.0-orkid-legacy.patch'
        cls.final = cls.patches / 'openvdb-13.1.0-orkid.patch'
        module = ast.parse(provider.read_text())
        klass = next(n for n in module.body if isinstance(n, ast.ClassDef))
        method = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == 'applyOrkidPatch')
        namespace = {'Path': Path, 'subprocess': subprocess, '__file__': str(provider)}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(provider), 'exec'), namespace)
        cls.apply_patch = staticmethod(namespace['applyOrkidPatch'])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='openvdb-patch-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        source = {}
        filename = None
        old_line = None
        for line in self.legacy.read_text().splitlines(True):
            if line.startswith('diff --git '):
                filename = line.rstrip().split(' b/')[1]
                source[filename] = []
                old_line = None
            elif line.startswith('@@ '):
                old_line = int(re.match(r'@@ -(\d+)', line).group(1)) - 1
            elif old_line is not None and line[:1] in (' ', '-'):
                contents = source[filename]
                while len(contents) <= old_line:
                    contents.append('// untouched upstream line %d\n' % len(contents))
                contents[old_line] = line[1:]
                old_line += 1
        self.files = sorted(source)
        for filename, lines in source.items():
            destination = self.root / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(''.join(lines))
        self.provider = SimpleNamespace(source_root=self.root)

    def digest(self):
        return hashlib.sha256(b''.join((self.root / name).read_bytes() for name in self.files)).digest()

    def install_legacy(self):
        subprocess.run(['git', 'apply', str(self.legacy)], cwd=self.root, check=True)

    def test_pristine_and_repeat(self):
        before = self.digest()
        self.apply_patch(self.provider)
        final = self.digest()
        self.assertNotEqual(before, final)
        self.apply_patch(self.provider)
        self.assertEqual(final, self.digest())

    def test_legacy_upgrade(self):
        self.install_legacy()
        self.apply_patch(self.provider)
        subprocess.run(['git', 'apply', '--check', '--reverse', str(self.final)], cwd=self.root, check=True)
        text = (self.root / 'openvdb/openvdb/tree/InternalNode.h').read_text()
        self.assertIn('Tile values are not child pointers', text)
        self.assertNotIn('t->mNodes[i].incVersion();', text)

    def test_conflict_refused_without_mutation(self):
        source = self.root / 'openvdb/openvdb/tree/InternalNode.h'
        source.write_text(source.read_text().replace('t->mNodes[i].setValue(b);', 't->mNodes[i].setValue(ValueType(42));'))
        before = self.digest()
        with self.assertRaises(subprocess.CalledProcessError):
            self.apply_patch(self.provider)
        self.assertEqual(before, self.digest())

    def test_legacy_restored_when_final_check_fails(self):
        self.install_legacy()
        before = self.digest()
        real_run = subprocess.run
        def fail_final_check(args, **kwargs):
            if args == ['git', 'apply', '--check', str(self.final)]:
                raise subprocess.CalledProcessError(1, args)
            return real_run(args, **kwargs)
        with patch.object(subprocess, 'run', side_effect=fail_final_check):
            with self.assertRaises(subprocess.CalledProcessError):
                self.apply_patch(self.provider)
        self.assertEqual(before, self.digest())


if __name__ == '__main__':
    unittest.main()
