"""The actual pipeline seeding function must honor provider freshness."""
import ast
from enum import Enum
from pathlib import Path
import sys
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


class PipelineFreshnessTests(unittest.TestCase):
    def test_plan_seeds_upgrade_and_explicit_rebuilds(self):
        source = Path(__file__).resolve().parents[1]/'bin_priv/obt.dep.pipeline.py'
        tree = ast.parse(source.read_text())
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.ClassDef) and n.name == 'State') or
                 (isinstance(n, ast.FunctionDef) and n.name == 'phase1_plan')]
        cases = [('current', True, False, True),
                 ('old_version', True, True, True),
                 ('missing_artifact', True, True, True),
                 ('missing_manifest', False, True, True),
                 ('incremental', True, True, True),
                 ('forced', True, True, True),
                 ('wipe', True, True, True),
                 ('unsupported', False, True, False)]
        providers = [SimpleNamespace(_name=name, OK=manifest, should_build=build,
                     should_force_build=name=='forced', should_wipe=name=='wipe',
                     should_incremental_build=name=='incremental', supports_host=supported)
                     for name,manifest,build,supported in cases]
        fake_obt = ModuleType('obt')
        fake_obt.dep = SimpleNamespace(Chain=lambda _:SimpleNamespace(_list=providers))
        ns = dict(Enum=Enum, _cond=threading.Condition(), _fetch_only_set=set(),
                  _providers={}, _state={})
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), ns)
        with patch.dict(sys.modules, {'obt':fake_obt}):
            ns['phase1_plan']('target')
        for name, manifest, build, supported in cases:
            with self.subTest(name=name):
                expected = 'DONE' if not supported or (manifest and not build) else 'PENDING'
                self.assertEqual(ns['_state'][name].name, expected)
        self.assertEqual(set(ns['_providers']), {p._name for p in providers})


if __name__ == '__main__':
    unittest.main()
