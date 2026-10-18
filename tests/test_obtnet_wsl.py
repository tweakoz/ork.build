#!/usr/bin/env python3
"""Focused tests for SSH-routed WSL Windows command execution."""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

from obt.net import client  # noqa: E402


class WslSshRunTests(unittest.TestCase):
    @mock.patch.object(client, "_sshhosts", return_value={"fixture-wsl": "Fixture-WSL"})
    @mock.patch.object(client.subprocess, "run")
    def test_preserves_powershell_script_as_one_remote_argument(self, run, _hosts):
        run.return_value = subprocess.CompletedProcess([], 0, "ok\n", "")
        argv = ["powershell.exe", "-Command", "$x = 'a b'; Write-Output $x"]

        reply = client._wsl_ssh_run("Fixture-WSL", argv, {"K": "v v"}, "/mnt/c", 10)

        self.assertTrue(reply["ok"])
        ssh_argv = run.call_args.args[0]
        self.assertEqual(ssh_argv[:7], ["ssh", "-o", "BatchMode=yes", "-o",
                                        "ConnectTimeout=8", "Fixture-WSL", ssh_argv[6]])
        self.assertIn("'$x = '\"'\"'a b'\"'\"'; Write-Output $x'", ssh_argv[6])
        self.assertIn("'K=v v'", ssh_argv[6])

    @mock.patch.object(client, "_sshhosts", return_value={"fixture-wsl": "Fixture-WSL"})
    @mock.patch.object(client.subprocess, "run")
    def test_remote_255_is_not_mislabeled_as_transport_failure(self, run, _hosts):
        run.return_value = subprocess.CompletedProcess([], 255, "", "application failed\n")
        reply = client._wsl_ssh_run("fixture-wsl", ["cmd.exe"], {}, None, 10)
        self.assertTrue(reply["ok"])
        self.assertEqual(reply["rc"], 255)

    @mock.patch.object(client, "_sshhosts", return_value={"fixture-wsl": "Fixture-WSL"})
    @mock.patch.object(client.subprocess, "run")
    def test_ssh_255_diagnostic_is_transport_failure(self, run, _hosts):
        run.return_value = subprocess.CompletedProcess(
            [], 255, "", "ssh: connect to host Fixture-WSL port 22: Connection refused\n")
        reply = client._wsl_ssh_run("fixture-wsl", ["cmd.exe"], {}, None, 10)
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["error"], "ssh unreachable")


if __name__ == "__main__":
    unittest.main()
