"""obt.net.client — the obtnet controller client (LLM/human/script side).

Controller-only topology for CONTROL: one connection to the controller; ops
carrying "node" are relayed. Fresh one-shot REQ per request (LINGER=0,
RCVTIMEO) — the proven pattern; blocking-sync API by design (tool callers
prefer sync). Two deliberate exceptions to controller-only:
  fetch — bulk chunks pull DIRECTLY from the node's fetch socket (the
          registry hands out the address; bulk never relays through control)
  watch — subscribes to the controller's aggregated event PUB (:7462)

Every verb ends with ONE greppable verdict line (LLM token frugality law);
--json swaps the human output for single-line JSON.
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

import zmq

from obt.net import proto
from obt.net.upload_cache import sha256_hex


CONFIG_PATH = Path.home() / ".obt-global" / "obtnet.json"


def resolve_controller(explicit=None):
    """Resolution order: --controller > OBTNET_CONTROLLER > ~/.obt-global/
    obtnet.json > localhost. Returns (addr, source)."""
    if explicit:
        return proto.normalize_controller_addr(explicit), "arg"
    env = os.environ.get("OBTNET_CONTROLLER")
    if env:
        return proto.normalize_controller_addr(env), "env"
    try:
        addr = json.loads(CONFIG_PATH.read_text())["controller"]
        return proto.normalize_controller_addr(addr), str(CONFIG_PATH)
    except Exception:
        pass
    return f"tcp://127.0.0.1:{proto.CONTROLLER_PORT}", "default"


class Client:
    def __init__(self, controller_addr: str = None):
        self.controller_addr, _ = resolve_controller(controller_addr)
        self.ctx = zmq.Context.instance()

    # -- capability-query routing ------------------------------------------
    def resolve_node(self, spec: str) -> str:
        """Literal node name, or a '@' selector routed by capability:
          @any            any live node
          @linux / @mac   by OS
          @gpu            has a GPU
          @key=val        capability substring match (@gpu=5090, @arch=x86_64)
          @<word>         substring across name/hostname/os/arch/gpu (@5090)
        Terms compose with commas (@linux,gpu). Ties break to the least busy
        node (fewest active jobs, then load)."""
        if not spec.startswith("@"):
            return spec
        nodes = self.list_nodes().get("nodes", [])
        live = [n for n in nodes if n.get("last_ping_age_s", 1e9) < 5.0]

        def matches(n, term):
            caps = n.get("capabilities", {})
            if term in ("", "any"):
                return True
            if term == "linux":
                return caps.get("os") == "Linux"
            if term in ("mac", "darwin"):
                return caps.get("os") == "Darwin"
            if term == "gpu":
                return bool(caps.get("gpu"))
            if "=" in term:
                k, v = term.split("=", 1)
                return v.lower() in str(caps.get(k, "")).lower()
            hay = " ".join(str(x) for x in
                           [n.get("name")] + [caps.get(k) for k in
                            ("hostname", "os", "arch", "gpu")] if x)
            return term.lower() in hay.lower()

        terms = spec[1:].split(",")
        picked = [n for n in live if all(matches(n, t) for t in terms)]
        if not picked:
            raise KeyError(f"no live node matches {spec!r} "
                           f"(live: {sorted(n['name'] for n in live)})")
        picked.sort(key=lambda n: (n.get("n_jobs", 0), n.get("load", 0.0)))
        return picked[0]["name"]

    def _request_to(self, addr, payload: bytes, timeout_ms=10000):
        s = self.ctx.socket(zmq.REQ)
        s.setsockopt(zmq.LINGER, 0)
        s.setsockopt(zmq.RCVTIMEO, timeout_ms)
        s.setsockopt(zmq.SNDTIMEO, 5000)
        try:
            s.connect(addr)
            s.send(payload)
            return proto.parse_message(s.recv())
        finally:
            s.close()

    def _request(self, payload: bytes, timeout_ms=10000):
        return self._request_to(self.controller_addr, payload, timeout_ms)

    # -- registry ---------------------------------------------------------
    def list_nodes(self):
        return self._request(proto.make_request(proto.OP_LIST_NODES))

    def node_record(self, node: str):
        for rec in self.list_nodes().get("nodes", []):
            if rec["name"] == node:
                return rec
        raise KeyError(f"unknown node {node!r}")

    def node_info(self, node: str):
        return self._request(proto.make_request(proto.OP_NODE_INFO, node=node))

    def controller_info(self):
        return self._request(proto.make_request(proto.OP_CONTROLLER_INFO))

    # -- sync run (short commands) ------------------------------------------
    def run(self, node: str, argv, env=None, cwd=None, timeout_s=300,
            inputs=None, output_globs=None):
        rep = self._request(
            proto.make_request(proto.OP_RUN_COMMAND, node=node, argv=list(argv),
                               env=env or {}, cwd=cwd, timeout_s=timeout_s,
                               inputs=inputs or [], output_globs=output_globs or []),
            timeout_ms=int((timeout_s + 15) * 1000))
        if rep.get("ok"):
            rep["stdout"] = base64.b64decode(rep.pop("stdout_b64", "")).decode(errors="replace")
            rep["stderr"] = base64.b64decode(rep.pop("stderr_b64", "")).decode(errors="replace")
        return rep

    # -- async jobs ---------------------------------------------------------
    def job_submit(self, node: str, argv, kind="command", env=None, cwd=None,
                   timeout_s=3600, inputs=None, output_globs=None, **extra):
        return self._request(proto.make_request(
            proto.OP_JOB_SUBMIT, node=node, kind=kind, argv=list(argv),
            env=env or {}, cwd=cwd, timeout_s=timeout_s,
            inputs=inputs or [], output_globs=output_globs or [], **extra))

    def job_status(self, node: str, job: str):
        return self._request(proto.make_request(proto.OP_JOB_STATUS, node=node, job=job))

    def job_list(self, node: str, limit=20):
        return self._request(proto.make_request(proto.OP_JOB_LIST, node=node, limit=limit))

    def job_cancel(self, node: str, job: str):
        return self._request(proto.make_request(proto.OP_JOB_CANCEL, node=node, job=job))

    def job_log(self, node: str, job: str, stream="stdout", tail=30, grep=None):
        return self._request(proto.make_request(
            proto.OP_JOB_LOG, node=node, job=job, stream=stream, tail=tail, grep=grep))

    def job_wait(self, node: str, job: str, timeout_s=3600, poll_cb=None):
        """Poll until terminal. Returns the final status reply."""
        deadline = time.time() + timeout_s
        interval = 0.5
        while True:
            rep = self.job_status(node, job)
            if not rep.get("ok"):
                return rep
            if rep.get("state") in proto.JOB_TERMINAL:
                return rep
            if poll_cb:
                poll_cb(rep)
            if time.time() > deadline:
                rep["ok"] = False
                rep["error"] = "wait_timeout"
                return rep
            time.sleep(interval)
            interval = min(interval * 1.5, 3.0)

    # -- artifacts ------------------------------------------------------------
    def upload(self, node: str, path, tag=""):
        data = Path(path).read_bytes()
        if len(data) > proto.MAX_INLINE_UPLOAD:
            raise ValueError(f"upload > {proto.MAX_INLINE_UPLOAD} bytes — chunked upload lands in O5")
        sha = sha256_hex(data)
        q = self._request(proto.make_request(proto.OP_UPLOAD_QUERY, node=node, sha256=sha))
        if q.get("ok") and q.get("present"):
            return sha  # dedup hit
        r = self._request(
            proto.make_request(proto.OP_UPLOAD_FILE, node=node, sha256=sha,
                               tag=tag or Path(path).name,
                               bytes_b64=base64.b64encode(data).decode()),
            timeout_ms=60000)
        if not r.get("ok"):
            raise RuntimeError(f"upload failed: {r}")
        return sha

    def fetch(self, node: str, sha: str, dest):
        """download_artifacts: chunked pull DIRECT from the node's fetch socket,
        sha-verified, atomic publish at dest. Returns bytes fetched."""
        rec = self.node_record(node)
        addr = rec["fetch_addr"]
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        got = 0
        with open(tmp, "wb") as f:
            while True:
                rep = self._request_to(addr, proto.make_request(
                    proto.OP_FETCH_CHUNK, sha256=sha, offset=got), timeout_ms=30000)
                if not rep.get("ok"):
                    tmp.unlink(missing_ok=True)
                    raise RuntimeError(f"fetch failed: {rep.get('error')}")
                chunk = base64.b64decode(rep["bytes_b64"])
                f.write(chunk)
                got += len(chunk)
                if rep.get("eof"):
                    break
        if sha256_hex(tmp.read_bytes()) != sha:
            tmp.unlink(missing_ok=True)
            raise RuntimeError("fetch sha mismatch")
        os.replace(tmp, dest)
        return got

    # -- tree.sync (git-free working-tree transport) -----------------------------
    def _fetch_addr(self, node):
        return self.node_record(node)["fetch_addr"]

    def _fetch_req(self, addr, payload, timeout_ms=120000):
        return self._request_to(addr, payload, timeout_ms)

    def _blob_put(self, addr, data: bytes, sha, tag=""):
        off = 0
        total = len(data)
        while True:
            chunk = data[off:off + proto.FETCH_CHUNK_BYTES]
            rep = self._fetch_req(addr, proto.make_request(
                proto.OP_BLOB_PUT, sha256=sha, offset=off, total=total,
                bytes_b64=base64.b64encode(chunk).decode(), tag=tag))
            if not rep.get("ok"):
                raise RuntimeError(f"blob_put failed: {rep.get('error')}")
            if rep.get("dedup") or rep.get("done"):
                return
            off += len(chunk)

    def _blob_get(self, addr, sha) -> bytes:
        buf = bytearray()
        while True:
            rep = self._fetch_req(addr, proto.make_request(
                proto.OP_FETCH_CHUNK, sha256=sha, offset=len(buf)))
            if not rep.get("ok"):
                raise RuntimeError(f"fetch failed: {rep.get('error')}")
            buf += base64.b64decode(rep["bytes_b64"])
            if rep.get("eof"):
                break
        if sha256_hex(bytes(buf)) != sha:
            raise RuntimeError("fetch sha mismatch")
        return bytes(buf)

    def sync(self, node, local_dir, remote_dir, pull=False, delete=False,
             excludes=None, dry=False, progress=None):
        """Make the destination tree equal the source tree (push: local->node,
        pull: node->local). Only changed blobs travel (content-addressed,
        dedup'd, sha-verified); returns a result dict whose 'tree' hashes
        match on both sides when the sync is faithful."""
        from obt.net import tree_sync
        addr = self._fetch_addr(node)
        local = tree_sync.build_manifest(local_dir, excludes)
        rep = self._fetch_req(addr, proto.make_request(
            proto.OP_TREE_MANIFEST, root=str(remote_dir), excludes=excludes or []))
        if not rep.get("ok"):
            raise RuntimeError(f"remote manifest failed: {rep.get('error')}")
        remote = rep["manifest"]
        src, dst = (remote, local) if pull else (local, remote)
        to_send, to_link, to_delete = tree_sync.diff_manifests(src, dst)
        if not delete:
            to_delete = []
        # the honest success criterion: dest must equal src PLUS any dest-only
        # extras we were not asked to delete
        expected = {r: e for r, e in dst.items()
                    if r not in src and r not in set(to_delete)}
        expected.update(src)
        send_bytes = sum(src[r]["size"] for r in to_send)
        changed = sorted(to_send + to_link)
        result = {"files": len(to_send), "links": len(to_link),
                  "deletes": len(to_delete), "bytes": send_bytes,
                  "total_files": len(src),
                  "changed": changed[:200],
                  "changed_truncated": len(changed) > 200,
                  "want_tree": tree_sync.tree_hash(expected)}
        if dry:
            result["tree"] = tree_sync.tree_hash(src)
            return result
        entries = {r: src[r] for r in to_send + to_link}
        if pull:
            # blobs live in the remote TREE; fetch serves the CACHE — so ask
            # the node to stage the needed tree blobs into its cache first.
            need = sorted({src[r]["sha256"] for r in to_send})
            if need:
                rep = self._fetch_req(addr, proto.make_request(
                    proto.OP_TREE_MANIFEST, root=str(remote_dir),
                    excludes=excludes or [], cache_blobs=need), timeout_ms=600000)
                if not rep.get("ok"):
                    raise RuntimeError(f"blob staging failed: {rep.get('error')}")
            nf, nl, nd = tree_sync.materialize_tree(
                Path(local_dir).expanduser(), entries,
                lambda sha: self._blob_get(addr, sha), deletes=to_delete)
            m = tree_sync.build_manifest(local_dir, excludes)
            result.update(files=nf, links=nl, deleted=nd,
                          tree=tree_sync.tree_hash(m))
        else:
            local_root = Path(local_dir).expanduser()
            done = 0
            for r in to_send:
                data = (local_root / r).read_bytes()
                self._blob_put(addr, data, src[r]["sha256"], tag=r)
                done += 1
                if progress and (done % 200 == 0):
                    progress(done, len(to_send))
            rep = self._fetch_req(addr, proto.make_request(
                proto.OP_TREE_APPLY, root=str(remote_dir), entries=entries,
                deletes=to_delete, excludes=excludes or []),
                timeout_ms=600000)
            if not rep.get("ok"):
                raise RuntimeError(f"tree_apply failed: {rep.get('error')} {rep}")
            result.update(files=rep["files"], links=rep["links"],
                          deleted=rep["deleted"], tree=rep["tree"])
        return result

    def diff(self, node, local_dir, remote_dir, excludes=None):
        """Symmetric tree diff, local vs node. Returns
        {entries: [(tag, rel)...], local_files, remote_files, equal}."""
        from obt.net import tree_sync
        addr = self._fetch_addr(node)
        local = tree_sync.build_manifest(local_dir, excludes)
        rep = self._fetch_req(addr, proto.make_request(
            proto.OP_TREE_MANIFEST, root=str(remote_dir), excludes=excludes or []))
        if not rep.get("ok"):
            raise RuntimeError(f"remote manifest failed: {rep.get('error')}")
        remote = rep["manifest"]
        entries = tree_sync.classify_diff(local, remote)
        return {"entries": entries, "local_files": len(local),
                "remote_files": len(remote), "equal": not entries,
                "local_tree": tree_sync.tree_hash(local), "remote_tree": rep["tree"]}

    # -- watch ------------------------------------------------------------------
    def watch(self, node_filter=None, grep=None, out=sys.stdout):
        """Subscribe to the controller's aggregated event stream; print lines
        until interrupted. Blocking by design (a human/LLM tail)."""
        info = self.controller_info()
        host = self.controller_addr.split("//")[-1].split(":")[0]
        addr = f"tcp://{host}:{info['pub_port']}"
        sub = self.ctx.socket(zmq.SUB)
        sub.setsockopt(zmq.LINGER, 0)
        sub.setsockopt_string(zmq.SUBSCRIBE, "")
        sub.connect(addr)
        rx = None
        if grep:
            import re
            rx = re.compile(grep)
        print(f"[obtnet] watching {addr} (ctrl-c to stop)", file=out, flush=True)
        try:
            while True:
                ev = proto.parse_message(sub.recv())
                if node_filter and ev.get("node") != node_filter:
                    continue
                line = f"[{ev.get('node','?')} {time.strftime('%H:%M:%S', time.localtime(ev.get('t', 0)))}] {ev.get('line','')}"
                if rx and not rx.search(line):
                    continue
                print(line, file=out, flush=True)
        except KeyboardInterrupt:
            pass
        finally:
            sub.close()


# ---------------------------------------------------------------------------
# CLI — every verb ends with ONE verdict line on stderr; --json for tools.
# obt.net.py list | info <node> | run <node> -- argv... | submit <node> -- argv...
#          | status <node> <job> | wait <node> <job> | jobs <node>
#          | cancel <node> <job> | log <node> <job> [--stderr --tail N --grep P]
#          | fetch <node> <sha> <dest> | upload <node> <path> | watch [--node N]
# ---------------------------------------------------------------------------

def _verdict(ok, verb, node, rest="", json_mode=False, payload=None):
    if json_mode:
        print(json.dumps({"ok": ok, "verb": verb, "node": node, **(payload or {})}))
    else:
        print(f"[obtnet] {'ok' if ok else 'FAIL'} {verb} {node} {rest}".rstrip(),
              file=sys.stderr)


def _print_job_fail_tail(c, node, job, n=30):
    for stream in ("stderr", "stdout"):
        rep = c.job_log(node, job, stream=stream, tail=n)
        lines = rep.get("lines") or []
        if lines:
            print(f"--- {stream} tail ({len(lines)} lines) ---", file=sys.stderr)
            for ln in lines:
                print(ln, file=sys.stderr)
            break


def main(argv=None):
    import argparse
    raw = list(sys.argv[1:] if argv is None else argv)
    cmd_argv = []
    if "--" in raw:                      # everything after `--` = the remote argv
        i = raw.index("--"); cmd_argv = raw[i + 1:]; raw = raw[:i]
    ap = argparse.ArgumentParser(description="obtnet controller CLI")
    ap.add_argument("--controller", default=None)
    ap.add_argument("--json", action="store_true", help="single-line JSON verdicts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("info"); p.add_argument("node")
    for verb in ("run", "submit"):
        p = sub.add_parser(verb)
        p.add_argument("node")
        p.add_argument("--timeout", type=float, default=300 if verb == "run" else 3600)
        p.add_argument("--cwd", default=None)
        p.add_argument("--out", action="append", default=[], help="output glob (repeatable)")
        p.add_argument("--env", action="append", default=[], help="KEY=VAL (repeatable)")
    for verb in ("build", "test", "scene"):        # the O2 kit (submit+wait)
        p = sub.add_parser(verb)
        p.add_argument("node")
        p.add_argument("--timeout", type=float, default=3600)
        p.add_argument("--cwd", default=None)
        p.add_argument("--env", action="append", default=[], help="KEY=VAL (repeatable)")
        p.add_argument("--out", action="append", default=[], help="output glob (repeatable)")
        p.add_argument("--async", dest="asy", action="store_true",
                       help="submit only; poll with wait/status")
        if verb == "scene":
            p.add_argument("--windowed", action="store_true",
                           help="allow a visible window on the node (owner consent)")
            p.add_argument("--markers", default=None,
                           help="regex for summary marker lines (default cook|settle|fps)")
    p = sub.add_parser("status"); p.add_argument("node"); p.add_argument("job")
    p = sub.add_parser("wait"); p.add_argument("node"); p.add_argument("job")
    p.add_argument("--timeout", type=float, default=3600)
    p = sub.add_parser("jobs")
    p.add_argument("node", nargs="?", default=None, help="omit for fleet-wide view")
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("cancel"); p.add_argument("node"); p.add_argument("job")
    p = sub.add_parser("log"); p.add_argument("node"); p.add_argument("job")
    p.add_argument("--stderr", action="store_true")
    p.add_argument("--tail", type=int, default=30)
    p.add_argument("--grep", default=None)
    p = sub.add_parser("fetch"); p.add_argument("node"); p.add_argument("sha")
    p.add_argument("dest")
    p = sub.add_parser("upload"); p.add_argument("node"); p.add_argument("path")
    p = sub.add_parser("watch")
    p.add_argument("--node", default=None)
    p.add_argument("--grep", default=None)
    p = sub.add_parser("config", help="show or set the default controller address")
    p.add_argument("addr", nargs="?", default=None)
    p = sub.add_parser("diff", help="symmetric tree diff: local vs node dir")
    p.add_argument("node")
    p.add_argument("local_dir")
    p.add_argument("remote_dir")
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--limit", type=int, default=200, help="max listed paths")
    p = sub.add_parser("sync",
                       help="make dest tree == src tree (git-free; only changed files travel)")
    p.add_argument("node")
    p.add_argument("local_dir")
    p.add_argument("remote_dir")
    p.add_argument("--pull", action="store_true", help="node -> local (default: push)")
    p.add_argument("--delete", action="store_true", help="remove dest-only files")
    p.add_argument("--dry", action="store_true", help="report the diff, change nothing")
    p.add_argument("--exclude", action="append", default=[], help="extra exclude pattern")
    p.add_argument("-v", action="store_true", help="list changed paths (first 50)")
    args = ap.parse_args(raw)

    c = Client(args.controller)
    jm = args.json

    if args.cmd == "config":
        if args.addr:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            addr = proto.normalize_controller_addr(args.addr)
            CONFIG_PATH.write_text(json.dumps({"controller": addr}, indent=1))
            _verdict(True, "config", addr, f"written {CONFIG_PATH}", jm,
                     {"controller": addr, "path": str(CONFIG_PATH)})
        else:
            addr, src = resolve_controller(args.controller)
            if jm:
                print(json.dumps({"controller": addr, "source": src}))
            else:
                print(f"controller: {addr}   (from {src})")
        return 0

    # '@' capability selectors route to a concrete node (least-busy match)
    if getattr(args, "node", None) and args.node.startswith("@"):
        try:
            resolved = c.resolve_node(args.node)
        except (KeyError, RuntimeError) as e:
            _verdict(False, args.cmd, args.node, f"error={e}", jm, {"error": str(e)})
            return 1
        print(f"[obtnet] {args.node} -> {resolved}", file=sys.stderr)
        args.node = resolved

    if args.cmd == "list":
        rep = c.list_nodes()
        if jm:
            print(json.dumps(rep.get("nodes", []))); return 0
        for s in rep.get("nodes", []):
            caps = s.get("capabilities", {})
            dt = s.get("clock_offset_ms")
            print(f"{s['name']:16s} {s['addr']:28s} {caps.get('os','?')}/{caps.get('arch','?')}"
                  f" gpu={caps.get('gpu','-')} load={s.get('load',0):.2f}"
                  f" jobs={s.get('n_jobs',0)}"
                  f" dt={'?' if dt is None else format(dt, '+.1f') + 'ms'}"
                  f" ping_age={s.get('last_ping_age_s','?')}s")
        return 0

    if args.cmd == "info":
        print(json.dumps(c.node_info(args.node), indent=None if jm else 2)); return 0

    if args.cmd in ("run", "submit"):
        if not cmd_argv:
            print(f"no argv given (use: {args.cmd} <node> -- cmd args...)", file=sys.stderr)
            return 2
        env = dict(kv.split("=", 1) for kv in args.env)
        if args.cmd == "run":
            t0 = time.time()
            rep = c.run(args.node, cmd_argv, env=env, cwd=args.cwd,
                        timeout_s=args.timeout, output_globs=args.out)
            dt = time.time() - t0
            if not rep.get("ok"):
                _verdict(False, "run", args.node, f"error={rep.get('error')} {dt:.1f}s",
                         jm, {"error": rep.get("error")})
                return 1
            if not jm:
                sys.stdout.write(rep["stdout"])
                if rep["stderr"]:
                    sys.stderr.write(rep["stderr"])
                for o in rep.get("outputs", []):
                    print(f"[output] {o['name']} {o['bytes']}B sha={o['sha256'][:12]}"
                          f"{' (cached remote)' if o.get('cached') else ''}", file=sys.stderr)
            _verdict(rep.get("rc") == 0, "run", args.node,
                     f"rc={rep.get('rc')} {dt:.1f}s stdout={len(rep['stdout'])}B "
                     f"stderr={len(rep['stderr'])}B files={len(rep.get('outputs', []))}",
                     jm, {"rc": rep.get("rc"), "dur_s": round(dt, 1),
                          "outputs": rep.get("outputs", []) if jm else None})
            return rep.get("rc", 0)
        else:  # submit
            rep = c.job_submit(args.node, cmd_argv, env=env, cwd=args.cwd,
                               timeout_s=args.timeout, output_globs=args.out)
            ok = bool(rep.get("ok"))
            _verdict(ok, "submit", args.node,
                     f"job={rep.get('job')}" if ok else f"error={rep.get('error')}",
                     jm, {"job": rep.get("job"), "error": rep.get("error")})
            return 0 if ok else 1

    if args.cmd in ("build", "test", "scene"):
        kind = {"build": "project.build", "test": "test", "scene": "scene.run"}[args.cmd]
        argv2 = cmd_argv or (["ork.build.py"] if args.cmd == "build" else None)
        if not argv2:
            print(f"no argv given (use: {args.cmd} <node> -- cmd args...)", file=sys.stderr)
            return 2
        env = dict(kv.split("=", 1) for kv in args.env)
        extra = {}
        if args.cmd == "scene":
            extra = {"windowed": args.windowed, "markers": args.markers}
            if args.windowed and not jm:
                print("[obtnet] WINDOWED run — a window will open on the node",
                      file=sys.stderr)
        rep = c.job_submit(args.node, argv2, kind=kind, env=env, cwd=args.cwd,
                           timeout_s=args.timeout, output_globs=args.out, **extra)
        if not rep.get("ok"):
            _verdict(False, args.cmd, args.node, f"error={rep.get('error')}", jm,
                     {"error": rep.get("error")})
            return 1
        job = rep["job"]
        if args.asy:
            _verdict(True, args.cmd, args.node, f"job={job} (async)", jm, {"job": job})
            return 0
        rep = c.job_wait(args.node, job, timeout_s=args.timeout + 60)
        s = rep.get("summary") or {}
        ok = bool(s.get("verdict_ok"))
        if args.cmd == "scene" and not jm:
            for ln in s.get("markers", []):
                print(f"  {ln}", file=sys.stderr)
        for o in (rep.get("outputs") or []):
            if not jm:
                print(f"[output] {o['name']} {o['bytes']}B sha={o['sha256'][:12]}",
                      file=sys.stderr)
        if not ok and rep.get("ok") and not jm:
            if args.cmd == "build":            # bounded: just the error lines
                el = c.job_log(args.node, job, stream="stdout", tail=15, grep="error")
                for ln in (el.get("lines") or []):
                    print(ln, file=sys.stderr)
            _print_job_fail_tail(c, args.node, job)
        detail = {"build": lambda: f"errors={s.get('errors','?')} warnings={s.get('warnings','?')}",
                  "test": lambda: f"passed={s.get('passed','?')} failed={s.get('failed','?')}",
                  "scene": lambda: f"rc={rep.get('rc')} markers={len(s.get('markers', []))}",
                  }[args.cmd]()
        _verdict(ok, args.cmd, args.node,
                 f"{detail} {rep.get('dur_s', 0)}s files={len(rep.get('outputs') or [])} job={job}",
                 jm, {"job": job, "state": rep.get("state"), "rc": rep.get("rc"),
                      "summary": s, "outputs": rep.get("outputs")})
        return 0 if ok else 1

    if args.cmd == "status":
        rep = c.job_status(args.node, args.job)
        if not rep.get("ok"):
            _verdict(False, "status", args.node, f"error={rep.get('error')}", jm)
            return 1
        _verdict(True, "status", args.node,
                 f"{rep['job']} state={rep['state']} rc={rep.get('rc')} "
                 f"{rep.get('dur_s', 0)}s out={rep.get('stdout_bytes', 0)}B "
                 f"err={rep.get('stderr_bytes', 0)}B files={len(rep.get('outputs', []))}",
                 jm, {k: rep.get(k) for k in
                      ("job", "state", "rc", "dur_s", "outputs", "argv_head")})
        return 0

    if args.cmd == "wait":
        t0 = time.time()
        rep = c.job_wait(args.node, args.job, timeout_s=args.timeout)
        dt = time.time() - t0
        state = rep.get("state")
        ok = rep.get("ok") and state == proto.JOB_DONE and rep.get("rc") == 0
        if not ok and rep.get("ok") and not jm:      # terminal-but-bad: show tail
            _print_job_fail_tail(c, args.node, args.job)
        for o in (rep.get("outputs") or []):
            if not jm:
                print(f"[output] {o['name']} {o['bytes']}B sha={o['sha256'][:12]}",
                      file=sys.stderr)
        _verdict(ok, "wait", args.node,
                 f"{args.job} state={state} rc={rep.get('rc')} {rep.get('dur_s', 0)}s "
                 f"out={rep.get('stdout_bytes', 0)}B err={rep.get('stderr_bytes', 0)}B "
                 f"files={len(rep.get('outputs') or [])}",
                 jm, {k: rep.get(k) for k in
                      ("job", "state", "rc", "dur_s", "outputs", "error")})
        return 0 if ok else 1

    if args.cmd == "jobs":
        targets = [args.node] if args.node else \
            [n["name"] for n in c.list_nodes().get("nodes", [])
             if n.get("last_ping_age_s", 1e9) < 5.0]
        all_jobs, failed = [], []
        for t in targets:
            rep = c.job_list(t, limit=args.limit)
            if rep.get("ok"):
                all_jobs += [{**j, "node": t} for j in rep.get("jobs", [])]
            else:
                failed.append(t)
        if jm:
            print(json.dumps(all_jobs)); return 0
        for j in sorted(all_jobs, key=lambda j: j["queued_at"]):
            print(f"{j['node']:10s} {j['job']} {j['state']:9s} rc={str(j.get('rc')):5s} "
                  f"{j.get('dur_s', 0) or 0:8.1f}s {j['argv_head']}")
        scope = args.node or f"fleet({len(targets)})"
        _verdict(not failed, "jobs", scope,
                 f"n={len(all_jobs)}" + (f" unreachable={failed}" if failed else ""), jm)
        return 0 if not failed else 1

    if args.cmd == "cancel":
        rep = c.job_cancel(args.node, args.job)
        _verdict(bool(rep.get("ok")), "cancel", args.node,
                 f"{args.job}" if rep.get("ok") else f"error={rep.get('error')}", jm,
                 {"job": args.job, "error": rep.get("error")})
        return 0 if rep.get("ok") else 1

    if args.cmd == "log":
        rep = c.job_log(args.node, args.job,
                        stream="stderr" if args.stderr else "stdout",
                        tail=args.tail, grep=args.grep)
        if not rep.get("ok"):
            _verdict(False, "log", args.node, f"error={rep.get('error')}", jm)
            return 1
        if jm:
            print(json.dumps(rep.get("lines", []))); return 0
        for ln in rep.get("lines", []):
            print(ln)
        _verdict(True, "log", args.node,
                 f"{args.job} {len(rep.get('lines', []))} lines of {rep.get('bytes', 0)}B"
                 f"{' (truncated window)' if rep.get('truncated') else ''}", jm)
        return 0

    if args.cmd == "fetch":
        t0 = time.time()
        try:
            n = c.fetch(args.node, args.sha, args.dest)
        except (RuntimeError, KeyError) as e:
            _verdict(False, "fetch", args.node, f"error={e}", jm, {"error": str(e)})
            return 1
        _verdict(True, "fetch", args.node,
                 f"sha={args.sha[:12]} {n}B {time.time()-t0:.1f}s -> {args.dest}",
                 jm, {"sha256": args.sha, "bytes": n, "dest": args.dest})
        return 0

    if args.cmd == "upload":
        sha = c.upload(args.node, args.path)
        _verdict(True, "upload", args.node, f"sha={sha[:12]}", jm, {"sha256": sha})
        return 0

    if args.cmd == "sync":
        t0 = time.time()
        try:
            r = c.sync(args.node, args.local_dir, args.remote_dir,
                       pull=args.pull, delete=args.delete,
                       excludes=args.exclude, dry=args.dry)
        except (RuntimeError, KeyError) as e:
            _verdict(False, "sync", args.node, f"error={e}", jm, {"error": str(e)})
            return 1
        way = "pull" if args.pull else "push"
        if args.v and not jm:
            for pth in r["changed"][:50]:
                print(f"  {pth}", file=sys.stderr)
            if len(r["changed"]) > 50:
                print(f"  ... +{len(r['changed'])-50} more", file=sys.stderr)
        mb = r["bytes"] / 1e6
        if args.dry:
            _verdict(True, "sync", args.node,
                     f"DRY {way} files={r['files']} links={r['links']} "
                     f"deletes={r['deletes']} {mb:.1f}MB of {r['total_files']} total",
                     jm, r if jm else None)
            return 0
        match = r["tree"] == r["want_tree"]
        _verdict(match, "sync", args.node,
                 f"{way} files={r['files']} links={r['links']} del={r['deleted']} "
                 f"{mb:.1f}MB {time.time()-t0:.1f}s "
                 f"tree={'MATCH ' + r['tree'][:12] if match else 'MISMATCH!'}",
                 jm, r if jm else None)
        return 0 if match else 1

    if args.cmd == "diff":
        try:
            r = c.diff(args.node, args.local_dir, args.remote_dir,
                       excludes=args.exclude)
        except (RuntimeError, KeyError) as e:
            _verdict(False, "diff", args.node, f"error={e}", jm, {"error": str(e)})
            return 1
        tags = {}
        for tag, rel in r["entries"]:
            tags[tag] = tags.get(tag, 0) + 1
        if jm:
            print(json.dumps({"ok": True, "verb": "diff", "node": args.node,
                              "equal": r["equal"], "counts": tags,
                              "entries": r["entries"][:args.limit],
                              "truncated": len(r["entries"]) > args.limit}))
        else:
            for tag, rel in r["entries"][:args.limit]:
                print(f"{tag} {rel}")
            if len(r["entries"]) > args.limit:
                print(f"... +{len(r['entries']) - args.limit} more (--limit)")
            _verdict(True, "diff", args.node,
                     f"{'EQUAL' if r['equal'] else 'DIFFER'} "
                     f"+{tags.get('+',0)} -{tags.get('-',0)} M{tags.get('M',0)} "
                     f"L{tags.get('L',0)} ({r['local_files']} local vs "
                     f"{r['remote_files']} remote files)")
        return 0 if r["equal"] else 1

    if args.cmd == "watch":
        c.watch(node_filter=args.node, grep=args.grep)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
