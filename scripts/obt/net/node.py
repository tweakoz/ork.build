"""obt.net.node — the obtnet node daemon (runs inside an OBT environment).

O1: async jobs + events + fetch, on top of the v0 sync path.
  control (REP, ephemeral)  — node_info / run_command (sync) / job_* / upload_*
  events  (PUB, ephemeral)  — one JSON event per console line (watch verb)
  fetch   (REP, ephemeral)  — chunked reads of content-addressed blobs
                              (bulk NEVER rides the control socket)
All three ports are reported to the controller at Connect.

Jobs: kind registry (O1 ships "command"; O2 adds project.build/scene.run/...),
FSM queued->running->done|failed|timeout|cancelled, run by a small worker pool.
Per-job on-disk record at <root>/jobs/<id>/ (job.json, status.json, stdout.log,
stderr.log) — the durable truth; PUB is best-effort. Job outputs always go to
the content-addressed cache and travel via chunked fetch (no inline caps).

Threading: each zmq socket is owned by exactly one thread — control by the
main loop, PUB by the publisher thread (fed by a python Queue; it also prints
the console line — the node terminal is a first-class UI, owner-watched),
fetch by the fetch thread, one-shot controller REQs by the heartbeat thread.
Workers touch no sockets; they update the locked registry + enqueue events.
"""

import base64
import glob as _glob
import os
import queue
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import zmq

from obt.net import proto
from obt.net.upload_cache import UploadCache, sha256_hex


class Job:
    def __init__(self, spec):
        self.id = proto.new_job_id()
        self.spec = spec                     # kind/argv/env/cwd/timeout_s/inputs/output_globs
        self.state = proto.JOB_QUEUED
        self.queued_at = proto.now()
        self.started_at = None
        self.ended_at = None
        self.rc = None
        self.detail = ""                     # failure detail / timeout note
        self.outputs = []                    # [{name, bytes, sha256}]
        self.workdir = None                  # Path, set at start
        self.popen = None
        self.cancel_requested = False

    def to_dict(self):
        argv = self.spec.get("argv", [])
        d = {"job": self.id, "kind": self.spec.get("kind", "command"),
             "state": self.state,
             "argv_head": " ".join(str(a) for a in argv)[:70],
             "queued_at": self.queued_at, "started_at": self.started_at,
             "ended_at": self.ended_at, "rc": self.rc, "outputs": self.outputs}
        if self.detail:
            d["detail"] = self.detail
        if self.started_at:
            end = self.ended_at or proto.now()
            d["dur_s"] = round(end - self.started_at, 2)
        if self.workdir:  # live log sizes — the frugal "how much output so far"
            for stream in ("stdout", "stderr"):
                p = Path(self.workdir) / f"{stream}.log"
                if p.exists():
                    d[f"{stream}_bytes"] = p.stat().st_size
        return d


def default_node_name():
    """Hostname, short form. On macOS uname nodename is network-flaky
    ('Mac', 'Mac-2.lan'...) — scutil LocalHostName is the stable identity."""
    n = os.uname().nodename.split(".")[0]
    if os.uname().sysname == "Darwin":
        try:
            r = subprocess.run(["scutil", "--get", "LocalHostName"],
                               capture_output=True, timeout=3)
            if r.returncode == 0 and r.stdout.strip():
                n = r.stdout.decode().strip()
        except Exception:
            pass
    return n


class Node:
    def __init__(self, controller_addr: str, name: str = None, root: Path = None,
                 workers: int = 2):
        self.controller_addr = proto.normalize_controller_addr(controller_addr)
        self.name = name or default_node_name()
        self.uuid = proto.new_uuid64()
        self.root = Path(root or (Path.home() / ".obtnet" / self.name))
        self.uploads = UploadCache(self.root / "upload_cache")
        self.ctx = zmq.Context.instance()
        self._stop = threading.Event()
        self._connected = False
        self.clock = proto.ClockSync()
        # sockets: ephemeral binds, ports reported at Connect. Each is bound here
        # (before threads start) but USED by exactly one thread.
        self.control = self.ctx.socket(zmq.REP)
        self.control.setsockopt(zmq.LINGER, 0)
        self.control_port = self.control.bind_to_random_port("tcp://0.0.0.0")
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.setsockopt(zmq.LINGER, 0)
        self.pub_port = self.pub.bind_to_random_port("tcp://0.0.0.0")
        self.fetch = self.ctx.socket(zmq.REP)
        self.fetch.setsockopt(zmq.LINGER, 0)
        self.fetch_port = self.fetch.bind_to_random_port("tcp://0.0.0.0")
        # jobs
        self.jobs = {}                       # id -> Job
        self.jobs_lock = threading.Lock()
        self.job_q = queue.Queue()
        self.n_workers = max(1, workers)
        self.event_q = queue.Queue()
        self.kinds = {"command": self._kind_command}   # O2 registers more

    # -- controller client side (heartbeat thread owns these one-shot sockets) ----
    def _ctl_request(self, payload: bytes, timeout_ms=5000):
        s = self.ctx.socket(zmq.REQ)
        s.setsockopt(zmq.LINGER, 0)
        s.setsockopt(zmq.RCVTIMEO, timeout_ms)
        s.setsockopt(zmq.SNDTIMEO, timeout_ms)
        try:
            s.connect(self.controller_addr)
            s.send(payload)
            return proto.parse_message(s.recv())
        finally:
            s.close()

    def _advertise_ip(self):
        """The ip THIS node uses to reach the controller == the ip the controller (and
        clients on its network) can reach us back on. UDP connect trick —
        no packets sent, just routing-table resolution."""
        import socket as _s
        host = self.controller_addr.split("//")[-1].split(":")[0]
        try:
            u = _s.socket(_s.AF_INET, _s.SOCK_DGRAM)
            u.connect((host, 1))
            ip = u.getsockname()[0]
            u.close()
            return ip
        except OSError:
            return "127.0.0.1"

    def _connect_to_controller(self):
        rep = self._ctl_request(proto.make_request(
            proto.OP_CONNECT,
            name=self.name, uuid=self.uuid,
            control_port=self.control_port,
            pub_port=self.pub_port,
            fetch_port=self.fetch_port,
            advertise_ip=self._advertise_ip(),
            capabilities=proto.probe_capabilities()))
        self._connected = bool(rep.get("ok"))
        return self._connected

    def _heartbeat_loop(self):
        backoff = 0.5
        while not self._stop.is_set():
            try:
                if not self._connected:
                    if self._connect_to_controller():
                        self._emit("connect", f"connected to controller {self.controller_addr} "
                                   f"(control {self.control_port} pub {self.pub_port} "
                                   f"fetch {self.fetch_port})")
                        backoff = 0.5
                    else:
                        time.sleep(min(backoff, 8.0)); backoff *= 2; continue
                t0 = proto.now()
                offset, rtt = self.clock.best()
                rep = self._ctl_request(proto.make_request(
                    proto.OP_PING, uuid=self.uuid, name=self.name, t0=t0,
                    load=os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0,
                    n_jobs=len([j for j in self._jobs_snapshot()
                                if j["state"] in (proto.JOB_QUEUED, proto.JOB_RUNNING)]),
                    clock_offset_ms=(None if offset is None else round(offset * 1000, 3)),
                    rtt_ms=(None if rtt is None else round(rtt * 1000, 3))))
                t3 = proto.now()
                if not rep.get("ok"):        # registry lost us (controller
                    self._connected = False  # restart) -> re-Connect next tick
                    self._emit("disconnect", "controller forgot us; re-registering")
                    continue
                if "t1" in rep:
                    self.clock.update(rep["t0"], rep["t1"], rep["t2"], t3)
            except Exception as e:
                if self._connected:
                    self._emit("disconnect", f"controller lost ({e}); reconnecting")
                self._connected = False
            self._stop.wait(0.5)

    # -- events / console -----------------------------------------------------
    def _emit(self, ev, line, **fields):
        """One compact line per event — printed on the node terminal (first-class
        UI, owner-watched) AND published for the fleet watch verb."""
        self.event_q.put((ev, line, fields))

    def _publisher_loop(self):
        while not self._stop.is_set():
            try:
                ev, line, fields = self.event_q.get(timeout=0.25)
            except queue.Empty:
                continue
            print(f"[{time.strftime('%H:%M:%S')}] {self.name}: {line}", flush=True)
            try:
                self.pub.send(proto.make_event(self.name, ev, line, **fields))
            except Exception:
                pass  # PUB is best-effort; the console line + disk record are truth

    # -- fetch socket (bulk lane: chunked reads/writes + tree.sync; never on
    # control) -------------------------------------------------------------
    def _fetch_loop(self):
        handlers = {
            proto.OP_FETCH_CHUNK: self._h_fetch_chunk,
            proto.OP_BLOB_PUT: self._h_blob_put,
            proto.OP_TREE_MANIFEST: self._h_tree_manifest,
            proto.OP_TREE_APPLY: self._h_tree_apply,
        }
        poller = zmq.Poller()
        poller.register(self.fetch, zmq.POLLIN)
        while not self._stop.is_set():
            if not dict(poller.poll(timeout=250)):
                continue
            data = self.fetch.recv()
            try:
                msg = proto.parse_message(data)
                h = handlers.get(msg.get("op"))
                reply = h(msg) if h else proto.make_reply_err(
                    proto.ERR_UNKNOWN_OP, op=msg.get("op"))
            except Exception as e:
                reply = proto.make_reply_err(proto.ERR_EXEC_FAILED, detail=repr(e))
            self.fetch.send(reply)

    def _h_fetch_chunk(self, msg):
        if not self.uploads.has(msg["sha256"]):
            return proto.make_reply_err(proto.ERR_UNKNOWN_SHA, sha256=msg["sha256"])
        p = self.uploads.path_for(msg["sha256"])
        total = p.stat().st_size
        off = int(msg.get("offset", 0))
        n = min(int(msg.get("size", proto.FETCH_CHUNK_BYTES)), proto.FETCH_CHUNK_BYTES)
        with open(p, "rb") as f:
            f.seek(off)
            chunk = f.read(n)
        return proto.make_reply_ok(total=total, offset=off,
                                   bytes_b64=base64.b64encode(chunk).decode(),
                                   eof=(off + len(chunk) >= total))

    def _h_blob_put(self, msg):
        """Chunked, resumable upload into the cache. Writes land at offset in
        <sha>.part; the final chunk verifies the sha and publishes atomically.
        Stateless (no session) — a retried or resumed sync just re-sends."""
        sha = msg["sha256"]
        if self.uploads.has(sha):
            return proto.make_reply_ok(done=True, dedup=True)
        part = self.uploads.path_for(sha).with_suffix(".part")
        data = base64.b64decode(msg["bytes_b64"])
        off = int(msg["offset"])
        total = int(msg["total"])
        with open(part, "r+b" if part.exists() else "wb") as f:
            f.seek(off)
            f.write(data)
        if off + len(data) < total:
            return proto.make_reply_ok(done=False)
        whole = part.read_bytes()
        got = sha256_hex(whole)
        if got != sha:
            part.unlink(missing_ok=True)
            return proto.make_reply_err("sha_mismatch", expected=sha, got=got)
        self.uploads.put(whole, tag=msg.get("tag", ""))
        part.unlink(missing_ok=True)
        return proto.make_reply_ok(done=True)

    def _h_tree_manifest(self, msg):
        from obt.net import tree_sync
        root = Path(msg["root"]).expanduser()
        m = tree_sync.build_manifest(root, msg.get("excludes"))
        # pull support: stage requested tree blobs into the cache so the
        # client's fetch_chunk loop can read them (fetch serves cache only)
        want = set(msg.get("cache_blobs") or [])
        if want:
            staged = 0
            for rel, e in m.items():
                if e["t"] == "f" and e["sha256"] in want:
                    want.discard(e["sha256"])
                    if not self.uploads.has(e["sha256"]):
                        self.uploads.put((root / rel).read_bytes(), tag=rel)
                        staged += 1
            self._emit("sync", f"staged {staged} blobs for pull of {root}")
        return proto.make_reply_ok(manifest=m, tree=tree_sync.tree_hash(m))

    def _h_tree_apply(self, msg):
        from obt.net import tree_sync
        root = Path(msg["root"]).expanduser()
        entries = msg["entries"]
        missing = [e["sha256"] for e in entries.values()
                   if e["t"] == "f" and not self.uploads.has(e["sha256"])]
        if missing:
            return proto.make_reply_err(proto.ERR_UNKNOWN_SHA, missing=missing[:5],
                                        n_missing=len(missing))
        nf, nl, nd = tree_sync.materialize_tree(
            root, entries, lambda sha: self.uploads.get(sha),
            deletes=msg.get("deletes") or [])
        m = tree_sync.build_manifest(root, msg.get("excludes"))
        self._emit("sync", f"tree_apply {root} files={nf} links={nl} del={nd}")
        return proto.make_reply_ok(files=nf, links=nl, deleted=nd,
                                   tree=tree_sync.tree_hash(m))

    # -- job machinery ----------------------------------------------------------
    def _jobs_snapshot(self):
        with self.jobs_lock:
            return [j.to_dict() for j in self.jobs.values()]

    def _worker_loop(self, widx):
        while not self._stop.is_set():
            try:
                job = self.job_q.get(timeout=0.25)
            except queue.Empty:
                continue
            with self.jobs_lock:
                if job.cancel_requested:
                    job.state = proto.JOB_CANCELLED
                    job.ended_at = proto.now()
                    self._emit("job_done", f"job {job.id} cancelled (never started)",
                               job=job.id, state=job.state)
                    continue
                job.state = proto.JOB_RUNNING
                job.started_at = proto.now()
            self._emit("job_start",
                       f"job {job.id} start: {job.to_dict()['argv_head']}", job=job.id)
            kind = self.kinds.get(job.spec.get("kind", "command"))
            try:
                kind(job)
            except Exception as e:
                with self.jobs_lock:
                    job.state = proto.JOB_FAILED
                    job.detail = repr(e)
                    job.ended_at = proto.now()
            d = job.to_dict()
            self._emit("job_done",
                       f"job {job.id} {d['state']} rc={d['rc']} {d.get('dur_s', 0)}s "
                       f"out={d.get('stdout_bytes', 0)}B err={d.get('stderr_bytes', 0)}B "
                       f"files={len(d['outputs'])}",
                       job=job.id, state=d["state"], rc=d["rc"],
                       dur_s=d.get("dur_s"), outputs=d["outputs"])

    def _kind_command(self, job):
        """The `command` JobKind: argv exec with inputs materialization + output
        globs -> content-addressed cache. Logs stream to files (live-tailable
        via job_log while running)."""
        import json as _json
        spec = job.spec
        workdir = self.root / "jobs" / job.id
        workdir.mkdir(parents=True, exist_ok=True)
        job.workdir = workdir
        (workdir / "job.json").write_text(_json.dumps(spec, indent=1))
        cwd = spec.get("cwd") or str(workdir)
        env = os.environ.copy()
        env.update(spec.get("env") or {})
        for inp in (spec.get("inputs") or []):
            self.uploads.materialize(inp["sha256"], Path(cwd) / inp["as"])
        timeout_s = float(spec.get("timeout_s", 3600))
        out_f = open(workdir / "stdout.log", "wb")
        err_f = open(workdir / "stderr.log", "wb")
        try:
            p = subprocess.Popen(spec["argv"], cwd=cwd, env=env,
                                 stdout=out_f, stderr=err_f, stdin=subprocess.DEVNULL,
                                 start_new_session=True)
        except Exception as e:
            out_f.close(); err_f.close()
            with self.jobs_lock:
                job.state = proto.JOB_FAILED
                job.detail = f"exec failed: {e}"
                job.ended_at = proto.now()
            self._write_status(job)
            return
        with self.jobs_lock:
            job.popen = p
        try:
            rc = p.wait(timeout=timeout_s)
            end_state = proto.JOB_DONE
        except subprocess.TimeoutExpired:
            self._killpg(p, signal.SIGKILL)
            p.wait()
            rc = None
            end_state = proto.JOB_TIMEOUT
            job.detail = f"killed after {timeout_s}s"
        finally:
            out_f.close(); err_f.close()
        # collect outputs into the content-addressed cache (fetch pulls them)
        outputs = []
        for pat in (spec.get("output_globs") or []):
            for f in sorted(_glob.glob(str(Path(cwd) / pat))):
                if not Path(f).is_file():
                    continue
                data = Path(f).read_bytes()
                sha = self.uploads.put(data, tag=os.path.relpath(f, cwd))
                outputs.append({"name": os.path.relpath(f, cwd),
                                "bytes": len(data), "sha256": sha})
        with self.jobs_lock:
            if job.cancel_requested and end_state == proto.JOB_DONE and rc and rc < 0:
                end_state = proto.JOB_CANCELLED   # died from our SIGTERM
            job.state = end_state
            job.rc = rc
            job.outputs = outputs
            job.ended_at = proto.now()
        self._write_status(job)

    def _write_status(self, job):
        import json as _json
        if job.workdir:
            (Path(job.workdir) / "status.json").write_text(_json.dumps(job.to_dict(), indent=1))

    @staticmethod
    def _killpg(p, sig):
        try:
            os.killpg(os.getpgid(p.pid), sig)
        except (ProcessLookupError, PermissionError):
            pass

    # -- control handlers ---------------------------------------------------
    def _h_node_info(self, msg):
        return proto.make_reply_ok(name=self.name, uuid=self.uuid,
                                   capabilities=proto.probe_capabilities(),
                                   jobs=self._jobs_snapshot()[-8:])

    def _h_upload_query(self, msg):
        return proto.make_reply_ok(present=self.uploads.has(msg["sha256"]))

    def _h_upload_file(self, msg):
        data = base64.b64decode(msg["bytes_b64"])
        sha = sha256_hex(data)
        if sha != msg["sha256"]:
            return proto.make_reply_err("sha_mismatch", expected=msg["sha256"], got=sha)
        hit = self.uploads.has(sha)
        self.uploads.put(data, tag=msg.get("tag", ""))
        self._emit("upload", f"upload <- {sha[:12]} {len(data)}B tag={msg.get('tag','')}"
                   f"{' (dedup-hit)' if hit else ' (stored)'}")
        return proto.make_reply_ok(sha256=sha)

    def _h_job_submit(self, msg):
        kind = msg.get("kind", "command")
        if kind not in self.kinds:
            return proto.make_reply_err(proto.ERR_UNKNOWN_KIND, kind=kind,
                                        known=sorted(self.kinds))
        spec = {k: msg.get(k) for k in
                ("kind", "argv", "env", "cwd", "timeout_s", "inputs", "output_globs")}
        spec["kind"] = kind
        if not spec.get("argv"):
            return proto.make_reply_err(proto.ERR_EXEC_FAILED, detail="empty argv")
        job = Job(spec)
        with self.jobs_lock:
            self.jobs[job.id] = job
        self._emit("job_queued", f"job {job.id} queued: "
                   f"{' '.join(str(a) for a in spec['argv'])[:70]}", job=job.id)
        self.job_q.put(job)
        return proto.make_reply_ok(job=job.id)

    def _get_job(self, msg):
        with self.jobs_lock:
            return self.jobs.get(msg.get("job"))

    def _h_job_status(self, msg):
        job = self._get_job(msg)
        if job is None:
            return proto.make_reply_err(proto.ERR_UNKNOWN_JOB, job=msg.get("job"))
        with self.jobs_lock:
            return proto.make_reply_ok(**job.to_dict())

    def _h_job_list(self, msg):
        jobs = self._jobs_snapshot()
        jobs.sort(key=lambda d: d["queued_at"])
        return proto.make_reply_ok(jobs=jobs[-int(msg.get("limit", 20)):])

    def _h_job_cancel(self, msg):
        job = self._get_job(msg)
        if job is None:
            return proto.make_reply_err(proto.ERR_UNKNOWN_JOB, job=msg.get("job"))
        with self.jobs_lock:
            job.cancel_requested = True
            p = job.popen
        if p is not None:
            self._killpg(p, signal.SIGTERM)
        self._emit("job_cancel", f"job {job.id} cancel requested", job=job.id)
        return proto.make_reply_ok(job=job.id, state=job.state)

    def _h_job_log(self, msg):
        """Bounded log read — LLM frugality law: logs stay remote; this returns
        a capped tail (or grep matches), never the full file."""
        job = self._get_job(msg)
        if job is None or job.workdir is None:
            return proto.make_reply_err(proto.ERR_UNKNOWN_JOB, job=msg.get("job"))
        stream = msg.get("stream", "stdout")
        p = Path(job.workdir) / f"{stream}.log"
        if not p.exists():
            return proto.make_reply_ok(lines=[], bytes=0)
        size = p.stat().st_size
        with open(p, "rb") as f:
            f.seek(max(0, size - proto.LOG_TAIL_MAX_BYTES))
            text = f.read().decode(errors="replace")
        lines = text.splitlines()
        if size > proto.LOG_TAIL_MAX_BYTES and lines:
            lines = lines[1:]   # drop the partial first line of the window
        pat = msg.get("grep")
        if pat:
            import re
            rx = re.compile(pat)
            lines = [ln for ln in lines if rx.search(ln)]
        n = int(msg.get("tail", 30))
        return proto.make_reply_ok(lines=lines[-n:], bytes=size,
                                   truncated=size > proto.LOG_TAIL_MAX_BYTES)

    def _h_run_command(self, msg):
        """v0 SYNC path, kept for short commands (the controller relays it off
        its main loop now, so this no longer stalls anyone's heartbeat)."""
        argv = msg["argv"]
        t_start = time.time()
        self._emit("run", f"run -> {' '.join(str(a) for a in argv)[:70]}")
        timeout_s = float(msg.get("timeout_s", 300))
        env = os.environ.copy()
        env.update(msg.get("env") or {})
        workdir = Path(tempfile.mkdtemp(prefix="cmd_", dir=str(self.root / "scratch")))
        cwd = msg.get("cwd") or str(workdir)
        for inp in (msg.get("inputs") or []):
            self.uploads.materialize(inp["sha256"], workdir / inp["as"])
        try:
            r = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                               timeout=timeout_s, start_new_session=True)
        except subprocess.TimeoutExpired:
            self._emit("run", f"run TIMEOUT after {timeout_s}s")
            return proto.make_reply_err(proto.ERR_TIMEOUT, timeout_s=timeout_s)
        except Exception as e:
            self._emit("run", f"run FAILED: {e}")
            return proto.make_reply_err(proto.ERR_EXEC_FAILED, detail=str(e))
        outputs = []
        for pat in (msg.get("output_globs") or []):
            for f in _glob.glob(str(Path(cwd) / pat)):
                data = Path(f).read_bytes()
                entry = {"name": os.path.relpath(f, cwd), "bytes": len(data),
                         "sha256": sha256_hex(data)}
                if len(data) <= proto.MAX_INLINE_OUTPUT:
                    entry["bytes_b64"] = base64.b64encode(data).decode()
                else:  # cache it — retrievable via the fetch socket
                    self.uploads.put(data, tag=entry["name"])
                    entry["cached"] = True
                outputs.append(entry)
        self._emit("run", f"run done rc={r.returncode} {time.time()-t_start:.1f}s "
                   f"out={len(r.stdout)}B err={len(r.stderr)}B files={len(outputs)}")
        return proto.make_reply_ok(
            rc=r.returncode,
            stdout_b64=base64.b64encode(r.stdout[-proto.MAX_STDOUT_BYTES:]).decode(),
            stderr_b64=base64.b64encode(r.stderr[-proto.MAX_STDERR_BYTES:]).decode(),
            outputs=outputs)

    # -- main loop ----------------------------------------------------------
    def run(self):
        (self.root / "scratch").mkdir(parents=True, exist_ok=True)
        (self.root / "jobs").mkdir(parents=True, exist_ok=True)
        threads = [threading.Thread(target=self._publisher_loop, daemon=True),
                   threading.Thread(target=self._fetch_loop, daemon=True),
                   threading.Thread(target=self._heartbeat_loop, daemon=True)]
        threads += [threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
                    for i in range(self.n_workers)]
        for t in threads:
            t.start()
        handlers = {
            proto.OP_NODE_INFO: self._h_node_info,
            proto.OP_RUN_COMMAND: self._h_run_command,
            proto.OP_UPLOAD_QUERY: self._h_upload_query,
            proto.OP_UPLOAD_FILE: self._h_upload_file,
            proto.OP_JOB_SUBMIT: self._h_job_submit,
            proto.OP_JOB_STATUS: self._h_job_status,
            proto.OP_JOB_LIST: self._h_job_list,
            proto.OP_JOB_CANCEL: self._h_job_cancel,
            proto.OP_JOB_LOG: self._h_job_log,
        }
        print(f"[obtnet.node:{self.name}] control tcp://*:{self.control_port} "
              f"pub tcp://*:{self.pub_port} fetch tcp://*:{self.fetch_port} "
              f"workers={self.n_workers} root={self.root}", flush=True)
        poller = zmq.Poller()
        poller.register(self.control, zmq.POLLIN)
        while not self._stop.is_set():
            if not dict(poller.poll(timeout=250)):
                continue
            data = self.control.recv()
            try:
                msg = proto.parse_message(data)
                h = handlers.get(msg.get("op"))
                reply = h(msg) if h else proto.make_reply_err(
                    proto.ERR_UNKNOWN_OP, op=msg.get("op"))
            except Exception as e:
                reply = proto.make_reply_err(proto.ERR_EXEC_FAILED, detail=repr(e))
            self.control.send(reply)

    def stop(self):
        self._stop.set()


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="obtnet node daemon")
    ap.add_argument("--controller", default=os.environ.get("OBTNET_CONTROLLER", "tcp://127.0.0.1:%d" % proto.CONTROLLER_PORT))
    ap.add_argument("--name", default=None)
    ap.add_argument("--root", default=None)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args(argv)
    node = Node(args.controller, name=args.name, root=args.root, workers=args.workers)
    signal.signal(signal.SIGTERM, lambda *a: node.stop())
    try:
        node.run()
    except KeyboardInterrupt:
        node.stop()


if __name__ == "__main__":
    main()
