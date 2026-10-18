#!/usr/bin/env python3
"""Regressions for streamed uploads and SSH forwarding acknowledgment."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from obt.net import client, proto
from obt.net.node import Node
from obt.net.upload_cache import UploadCache


class BlobUploadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="obtnet-upload-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.node = Node.__new__(Node)
        self.node.uploads = UploadCache(self.root / "cache")
        self.client = client.Client.__new__(client.Client)
        self.requests = []

        def fetch(addr, payload):
            msg = proto.parse_message(payload)
            self.requests.append(msg)
            return proto.parse_message(self.node._h_blob_put(msg))

        self.client._fetch_req = fetch

    def upload(self, data, partial=None):
        path = self.root / "source"
        path.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        if partial is not None:
            self.node.uploads.path_for(sha).with_suffix(".part").write_bytes(partial)
        with mock.patch.object(proto, "FETCH_CHUNK_BYTES", 4):
            self.client._blob_put_file("unused", path, sha)
        self.assertTrue(self.node.uploads.has(sha))
        self.assertEqual(self.node.uploads.get(sha), data)
        self.assertFalse(self.node.uploads.path_for(sha).with_suffix(".part").exists())
        return sha

    def test_empty_file_is_published(self):
        self.upload(b"")
        self.assertEqual(len(self.requests), 2)
        self.assertNotIn("probe", self.requests[-1])

    def test_complete_partial_is_verified_and_published(self):
        self.upload(b"complete", partial=b"complete")
        self.assertEqual(self.requests[-1]["offset"], 8)
        self.assertEqual(self.requests[-1]["bytes_b64"], "")

    def test_incomplete_partial_resumes_at_saved_offset(self):
        self.upload(b"partial contents", partial=b"par")
        self.assertEqual(self.requests[1]["offset"], 3)

    def test_new_file_streams_multiple_chunks(self):
        self.upload(b"multiple chunks")
        self.assertGreater(len(self.requests), 3)

    def test_dedup_only_probes(self):
        data = b"cached"
        self.node.uploads.put(data)
        self.upload(data)
        self.assertEqual(len(self.requests), 1)

    def test_corrupt_complete_partial_is_rejected_then_retry_succeeds(self):
        with self.assertRaisesRegex(RuntimeError, "sha_mismatch"):
            self.upload(b"correct", partial=b"corrupt")
        self.upload(b"correct")

    def test_missing_completion_acknowledgment_is_an_error(self):
        self.client._fetch_req = lambda *args: {"ok": True, "done": False, "next_offset": 0}
        with self.assertRaisesRegex(RuntimeError, "completion or make progress"):
            self.upload(b"")


class TunnelStartupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="obtnet-tunnel-test-")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "node.json"
        self.proc = mock.Mock(pid=12345)
        self.proc.poll.return_value = None
        self.state_path = self.enterContext(mock.patch.object(
            client, "_tunnel_state_path", return_value=self.path))
        # All local ports already accept connections: this must not override
        # SSH's own forwarding verdict.
        self.enterContext(mock.patch.object(client, "_port_open", return_value=True))

        def launch(argv, **kwargs):
            control = Path(argv[argv.index("-S") + 1])
            control.touch()
            self.addCleanup(lambda: client._remove_tunnel_control({"control_path": str(control)}))
            return self.proc

        self.launch = self.enterContext(mock.patch.object(
            client.subprocess, "Popen", side_effect=launch))
        self.forward = self.enterContext(mock.patch.object(client.subprocess, "run"))

    def test_occupied_ports_do_not_mask_forwarding_failure(self):
        self.forward.return_value = subprocess.CompletedProcess([], 255, "", "Port forwarding failed")
        with self.assertRaisesRegex(RuntimeError, "Port forwarding failed"):
            client.tunnel_connect("test", ssh_target="test-host")
        self.assertFalse(self.path.exists())
        self.proc.terminate.assert_called_once()
        self.proc.wait.assert_called_once()

    def test_success_requires_forward_ack_and_saves_master_pid(self):
        self.forward.return_value = subprocess.CompletedProcess([], 0, "", "")
        result = client.tunnel_connect("test", ssh_target="test-host")
        argv = self.forward.call_args.args[0]
        self.assertEqual(argv[argv.index("-O") + 1], "forward")
        for port in (63101, 63102, 63103):
            self.assertIn(f"127.0.0.1:{port}:127.0.0.1:{port}", argv)
        self.assertEqual(result["action"], "connected")
        self.assertEqual(json.loads(self.path.read_text())["pid"], self.proc.pid)
        self.proc.terminate.assert_not_called()

    def test_forward_timeout_terminates_master_without_saving_success(self):
        self.forward.side_effect = subprocess.TimeoutExpired("ssh", 10)
        with self.assertRaises(subprocess.TimeoutExpired):
            client.tunnel_connect("test", ssh_target="test-host")
        self.assertFalse(self.path.exists())
        self.proc.terminate.assert_called_once()

    def test_master_exit_after_forward_ack_is_not_success(self):
        self.forward.return_value = subprocess.CompletedProcess([], 0, "", "")
        self.proc.poll.side_effect = [None, 255, 255]
        with self.assertRaisesRegex(RuntimeError, "failed to become healthy"):
            client.tunnel_connect("test", ssh_target="test-host")
        self.assertFalse(self.path.exists())

    def saved_tunnel(self, **changes):
        state = {"pid": 12345, "ports": [63101, 63102, 63103],
                 "ssh_target": "test-host", "bind_address": None,
                 "control_path": str(Path(self.tmp.name) / "ctl-dir" / "ctl")}
        state.update(changes)
        control = Path(state["control_path"])
        control.parent.mkdir(exist_ok=True)
        control.touch()
        self.path.write_text(json.dumps(state))
        self.forward.return_value = subprocess.CompletedProcess([], 0, "", "Master running (pid=12345)\n")
        return state

    def test_existing_healthy_tunnel_is_idempotent(self):
        self.saved_tunnel()
        with mock.patch.object(client.os, "kill"):
            result = client.tunnel_connect("test", ssh_target="test-host")
        self.assertEqual(result["action"], "already-connected")
        self.launch.assert_not_called()
        self.assertIn("check", self.forward.call_args.args[0])

    def test_changed_connection_settings_require_explicit_disconnect(self):
        for changed in ({"ssh_target": "different-host"},
                        {"bind_address": "192.0.2.1"}, {"control_port": 63201}):
            with self.subTest(changed=changed):
                state = self.saved_tunnel()
                args = {"ssh_target": "test-host", **changed}
                with mock.patch.object(client.os, "kill"):
                    with self.assertRaisesRegex(RuntimeError, "different connection settings"):
                        client.tunnel_connect("test", **args)
                self.assertEqual(json.loads(self.path.read_text()), state)
        self.launch.assert_not_called()

    def test_recycled_pid_or_unrelated_listener_does_not_prove_ownership(self):
        self.saved_tunnel()
        for result in (subprocess.CompletedProcess([], 0, "", "Master running (pid=999)"),
                       subprocess.CompletedProcess([], 255, "", "Control socket connect failed")):
            with self.subTest(result=result), mock.patch.object(client.os, "kill") as kill:
                self.forward.return_value = result
                with self.assertRaises(RuntimeError):
                    client.tunnel_connect("test", ssh_target="test-host")
                with self.assertRaises(RuntimeError):
                    client.tunnel_disconnect("test")
                self.assertTrue(self.path.exists())
                self.assertTrue(all(call.args[1] == 0 for call in kill.call_args_list))
                self.assertFalse(client.tunnel_status("test")["healthy"])
        self.launch.assert_not_called()

    def test_legacy_live_state_is_not_reused_or_signalled(self):
        self.path.write_text(json.dumps({"pid": 12345, "ports": [63101, 63102, 63103]}))
        with mock.patch.object(client.os, "kill") as kill:
            with self.assertRaisesRegex(RuntimeError, "legacy state"):
                client.tunnel_connect("test", ssh_target="test-host")
            with self.assertRaisesRegex(RuntimeError, "legacy state"):
                client.tunnel_disconnect("test")
            self.assertTrue(all(call.args[1] == 0 for call in kill.call_args_list))
        self.launch.assert_not_called()

    def test_disconnect_addresses_owned_master_and_cleans_control_socket(self):
        state = self.saved_tunnel()
        with mock.patch.object(client.os, "kill") as kill:
            result = client.tunnel_disconnect("test")
            kill.assert_called_once_with(12345, 0)
        self.assertEqual(result["action"], "disconnected")
        operations = [call.args[0][call.args[0].index("-O") + 1]
                      for call in self.forward.call_args_list]
        self.assertEqual(operations, ["check", "exit"])
        self.assertFalse(self.path.exists())
        self.assertFalse(Path(state["control_path"]).parent.exists())

    def test_dead_master_can_be_replaced(self):
        state = self.saved_tunnel()
        self.forward.return_value = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(client.os, "kill", side_effect=ProcessLookupError):
            result = client.tunnel_connect("test", ssh_target="new-host")
        self.assertEqual(result["action"], "connected")
        self.assertEqual(result["ssh_target"], "new-host")
        self.assertFalse(Path(state["control_path"]).exists())


if __name__ == "__main__":
    unittest.main()
