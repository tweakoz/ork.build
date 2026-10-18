import ast
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from obt import dep

class BootstrapTests(unittest.TestCase):
    def run_bootstrap(self, fail=None):
        calls = []
        def provider(name, children=()):
            def provide():
                calls.append(name)
                return name != fail
            return SimpleNamespace(_name=name, _required_deps={p._name:p for p in children}, supports_host=True, should_build=True, provide=provide)
        cmake = provider('cmake')
        moltenvk = provider('moltenvk')
        vulkan = provider('vulkan', [moltenvk, cmake])
        nodes = {p._name:SimpleNamespace(instance=p) for p in (cmake,moltenvk,vulkan)}
        tree = ast.parse((ROOT/'bin_pub/obt.env.create.py').read_text())
        branch = tree.body[-1]
        code = compile(ast.Module(body=branch.orelse, type_ignores=[]), '<serial bootstrap>', 'exec')
        with patch('obt._dep_node.DepNode.nodeForName', side_effect=nodes.get):
            try:
                exec(code, {'MANDATORY_DEPS':['cmake','vulkan'], 'sys':sys})
            except SystemExit as e:
                return calls, e.code
        return calls, 0

    def test_prerequisites_built_before_vulkan(self):
        calls, rc = self.run_bootstrap()
        self.assertEqual(rc, 0)
        self.assertEqual(calls.count('cmake'), 1)
        self.assertLess(calls.index('moltenvk'), calls.index('vulkan'))
        self.assertLess(calls.index('cmake'), calls.index('vulkan'))

    def test_failure_stops_before_vulkan(self):
        calls, rc = self.run_bootstrap('moltenvk')
        self.assertEqual(rc, 1)
        self.assertNotIn('vulkan', calls)

if __name__ == '__main__':
    unittest.main()
