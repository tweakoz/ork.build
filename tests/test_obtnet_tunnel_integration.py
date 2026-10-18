#!/usr/bin/env python3
"""Opt-in real OpenSSH tunnel lifecycle test (no controller or node required).

Run with OBTNET_TEST_SSH_TARGET set to an existing noninteractive SSH alias.
The account must permit TCP forwarding. Uses ephemeral loopback listeners and
private temporary state; does not inspect or change the user's tunnel records.
No commands or files are created on the SSH server. Port probes may produce
remote connection-refused messages because no remote payload service is needed.
"""
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from obt.net import client


@unittest.skipUnless(os.environ.get("OBTNET_TEST_SSH_TARGET"),
                     "set OBTNET_TEST_SSH_TARGET for real SSH integration")
class RealTunnelLifecycle(unittest.TestCase):
    def test_owned_master_lifecycle(self):
        target = os.environ["OBTNET_TEST_SSH_TARGET"]
        # Reserve three distinct unused ports together, release immediately
        # before SSH binds them. A collision fails loudly; no existing listener
        # can satisfy SSH's own forwarding acknowledgment.
        reservations = []
        try:
            for _ in range(3):
                sock = socket.socket()
                reservations.append(sock)
                sock.bind(("127.0.0.1", 0))
            ports = [sock.getsockname()[1] for sock in reservations]
        finally:
            for sock in reservations:
                sock.close()
        arguments = dict(ssh_target=target, control_port=ports[0],
                         pub_port=ports[1], fetch_port=ports[2])
        with tempfile.TemporaryDirectory(prefix="obtnet-real-tunnel-") as td:
            state_path = Path(td) / "fixture.json"
            with mock.patch.object(client, "_tunnel_state_path", return_value=state_path):
                try:
                    created = client.tunnel_connect("fixture", **arguments)
                    self.assertEqual(created["action"], "connected")
                    pid = created["pid"]
                    control = Path(created["control_path"])
                    self.assertTrue(control.exists())
                    self.assertTrue(client.tunnel_status("fixture")["healthy"])
                    repeated = client.tunnel_connect("fixture", **arguments)
                    self.assertEqual(repeated["action"], "already-connected")
                    self.assertEqual(repeated["pid"], pid)
                    before = state_path.read_bytes()
                    for changes in ({"ssh_target": "nonexistent-fixture-target.invalid"},
                                    {"bind_address": "192.0.2.1"}):
                        with self.subTest(changes=changes):
                            with self.assertRaisesRegex(RuntimeError, "different connection settings"):
                                client.tunnel_connect("fixture", **{**arguments, **changes})
                            self.assertEqual(state_path.read_bytes(), before)
                            self.assertTrue(client.tunnel_status("fixture")["healthy"])
                    stopped = client.tunnel_disconnect("fixture")
                    self.assertEqual(stopped["pid"], pid)
                    self.assertFalse(state_path.exists())
                    self.assertFalse(control.exists())
                    self.assertFalse(control.parent.exists())
                    self.assertFalse(client.tunnel_status("fixture")["healthy"])
                    deadline = time.monotonic() + 10
                    exit_code = None
                    while True:
                        try:
                            exited, status = os.waitpid(pid, os.WNOHANG)
                        except ChildProcessError:
                            # subprocess may already have reaped its child.
                            try:
                                os.kill(pid, 0)
                            except ProcessLookupError:
                                break
                        else:
                            if exited == pid:
                                # OpenSSH may exit 255 on a successful mux
                                # `-O exit`; the control command acknowledged it.
                                exit_code = os.waitstatus_to_exitcode(status)
                                break
                        if time.monotonic() >= deadline:
                            self.fail(f"owned SSH master {pid} remained alive after disconnect")
                        time.sleep(.05)
                    print(json.dumps({"real_ssh_lifecycle": "passed", "master_pid": pid,
                                      "ports": ports, "master_exited": True,
                                      "master_exit_code": exit_code}))
                finally:
                    if state_path.exists():
                        client.tunnel_disconnect("fixture")


if __name__ == "__main__":
    unittest.main()
