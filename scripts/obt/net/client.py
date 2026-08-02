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
import socket
import subprocess
import sys
import time
from pathlib import Path

import zmq

from obt.net import proto
from obt.net.coordpaths import config_path, coord_root
from obt.net.upload_cache import sha256_hex


# Identity + mail roots are FUNCTIONS, not constants: they hang off
# obt.net.coordpaths.coord_home() ($OBT_COORD_HOME, else $HOME), so a second
# seat on one login account gets its own identity and inbox. See coordpaths.
# well-known, venv-independent location of the deposit tool on ssh recipients
# (deployed there so a bare `ssh host python3 <path>` needs only system python3).
# This one is a REMOTE path expanded by the recipient's shell — the recipient's
# own env, not ours, decides where its coordination tree lives.
SSH_DEPOSIT_PATH = "$HOME/coordination/bin/obt.net.msg.deposit.py"


def _load_global_config():
    try:
        return json.loads(config_path().read_text())
    except Exception:
        return {}


def _coordid():
    """Sender identity: explicit `coordid` in obtnet.json, else short hostname."""
    return _load_global_config().get("coordid") or socket.gethostname().split(".")[0]


def _sshhosts():
    """Map of ssh-target-name -> ssh destination (host alias) for msg/push/pull."""
    hosts = _load_global_config().get("sshhosts") or {}
    return {k: (v or k) for k, v in hosts.items()}


def resolve_controller(explicit=None):
    """Resolution order: --controller > OBTNET_CONTROLLER > <coord_home>/
    .obt-global/obtnet.json > localhost. Returns (addr, source)."""
    if explicit:
        return proto.normalize_controller_addr(explicit), "arg"
    env = os.environ.get("OBTNET_CONTROLLER")
    if env:
        return proto.normalize_controller_addr(env), "env"
    cfg_path = config_path()
    try:
        addr = json.loads(cfg_path.read_text())["controller"]
        return proto.normalize_controller_addr(addr), str(cfg_path)
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
        live = self._live_nodes()
        terms = spec[1:].split(",")
        picked = [n for n in live if all(self._node_matches(n, t) for t in terms)]
        if not picked:
            raise KeyError(f"no live node matches {spec!r} "
                           f"(live: {sorted(n['name'] for n in live)})")
        picked.sort(key=lambda n: (n.get("n_jobs", 0), n.get("load", 0.0)))
        return picked[0]["name"]

    def _live_nodes(self):
        return [n for n in self.list_nodes().get("nodes", [])
                if n.get("last_ping_age_s", 1e9) < 5.0]

    @staticmethod
    def _node_matches(n, term):
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

    def resolve_nodes(self, spec: str):
        """FAN-OUT resolution: 'a,b,c' = literal list; '@each' = every live
        node; '@each:linux' / '@each:gpu=3090' = every live match. Anything
        else = ONE node via resolve_node. Ordered, deduped."""
        if spec.startswith("@each"):
            live = self._live_nodes()
            terms = spec.split(":", 1)[1].split(",") if ":" in spec else []
            return sorted(n["name"] for n in live
                          if all(self._node_matches(n, t) for t in terms))
        if "," in spec:
            out = []
            for s in spec.split(","):
                r = self.resolve_node(s.strip())
                if r not in out:
                    out.append(r)
            return out
        return [self.resolve_node(spec)]

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
        sha = (sha or "").strip().lower()
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise RuntimeError(
                f"fetch needs a full 64-hex sha256, got {len(sha)} chars ({sha!r}); "
                "prefixes are not resolvable at the fetch socket. The verdict/[output] "
                "line prints only a 12-char preview — get the full sha from "
                "`obt.net.py --json status/wait <node> <job>`.")
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

    def _pushlog_path(self, node, remote_dir):
        key = sha256_hex(f"{node}|{remote_dir}".encode())[:16]
        return Path.home() / ".obtnet" / "pushlog" / f"{key}.json"

    def _remote_tracked_dirt(self, node, remote_dir):
        """relpaths (to remote_dir) of tracked-modified files, or None if the
        destination is not inside a git work tree."""
        rc, out = self._remote_git(node, remote_dir, "rev-parse", "--show-prefix")
        if rc:
            return None
        prefix = out.strip()
        _, stat = self._remote_git(node, remote_dir, "status", "--porcelain", "--", ".")
        dirty = []
        for ln in stat.splitlines():
            ln = ln.rstrip()
            if not ln or ln.lstrip().startswith("??"):
                continue
            # robust to the transport's strip() eating the first line's leading
            # status space: take everything after the 2-char status field,
            # wherever it starts. Renames: keep the NEW name.
            p = ln[2:].lstrip() if len(ln) > 2 and ln[1] in " MADRCU" else ln.split(None, 1)[-1]
            p = p.strip().strip('"')
            if " -> " in p:
                p = p.split(" -> ", 1)[1]
            if prefix and p.startswith(prefix):
                p = p[len(prefix):]
            dirty.append(p)
        return dirty

    def sync(self, node, local_dir, remote_dir, pull=False, delete=False,
             excludes=None, dry=False, progress=None, force=False):
        """Make the destination tree equal the source tree (push: local->node,
        pull: node->local). Only changed blobs travel (content-addressed,
        dedup'd, sha-verified); returns a result dict whose 'tree' hashes
        match on both sides when the sync is faithful.

        DIRT GUARD (push only): refuses to clobber NODE-SIDE edits — a
        to-be-overwritten/deleted file that is tracked-dirty at the
        destination AND does not match what our own last push left there
        (the pushlog) is somebody else's work; --force overrides. Pull has
        no guard (the controller clobbering its own tree is deliberate)."""
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
        pushlog = {}
        plpath = self._pushlog_path(node, remote_dir)
        try:
            pushlog = json.loads(plpath.read_text())
        except Exception:
            pass
        if not pull and not dry and not force and (to_send or to_delete):
            dirty = self._remote_tracked_dirt(node, remote_dir)
            if dirty:
                touched = set(to_send) | set(to_delete)
                at_risk = sorted(
                    r for r in (touched & set(dirty))
                    if dst.get(r, {}).get("sha256") != pushlog.get(r))
                if at_risk:
                    raise RuntimeError(
                        f"DIRT GUARD: {len(at_risk)} node-side edited file(s) would be "
                        f"clobbered: {at_risk[:5]}{'...' if len(at_risk) > 5 else ''} "
                        f"— pull/merge them first, or --force to overwrite")
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
            for r in to_send:                      # remember what WE left there
                pushlog[r] = src[r]["sha256"]
            for r in to_delete:
                pushlog.pop(r, None)
            plpath.parent.mkdir(parents=True, exist_ok=True)
            plpath.write_text(json.dumps(pushlog))
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

    # -- gitsync (base-commit alignment; bundles because we never push) ----------
    def _local_git(self, repo, *args):
        import subprocess
        r = subprocess.run(["git", "-C", str(repo)] + list(args),
                           capture_output=True, text=True)
        return r.returncode, r.stdout.strip()

    @staticmethod
    def _check_remote_path(repo, node):
        """Remote argv is exec'd WITHOUT a shell (that is what lets a restricted
        seat allowlist the 'git' head), so '~' never expands — git would receive
        the literal string and report 'not a git repo'. Fail with the real
        reason instead of that lie. (The file verbs expanduser server-side, so
        this only binds the git legs.)"""
        s = str(repo)
        if s.startswith("~"):
            raise RuntimeError(
                f"remote path {s!r} on {node} starts with '~': remote commands run "
                f"without a shell, so '~' is not expanded — pass the absolute path")

    def _remote_git(self, node, repo, *args):
        """One DIRECT `git ...` argv on the node — never shell-wrapped, so a
        restricted seat node (allowed heads: git) accepts it.
        A node that never RAN the command (unknown node, offline, restricted
        head) is not a git rc: raise the real reason, exactly as
        _remote_git_step does. Folding it into rc=1 made every transport
        failure read as a broken repo at the call sites."""
        self._check_remote_path(repo, node)
        rep = self.run(node, ["git", "-C", str(repo)] + [str(a) for a in args],
                       timeout_s=30)
        if not rep.get("ok"):
            det = rep.get("detail") or rep.get("error")
            raise RuntimeError(f"remote `git {args[0]}` on {node} did not run: {det}")
        return rep.get("rc", 1), (rep.get("stdout") or "").strip()

    def _remote_git_step(self, node, repo, *args, timeout_s=120):
        """_remote_git for steps whose FAILURE TEXT matters: returns the full
        reply (stderr included) and raises loudly when the node refuses to run
        it at all (e.g. a restricted head)."""
        self._check_remote_path(repo, node)
        rep = self.run(node, ["git", "-C", str(repo)] + [str(a) for a in args],
                       timeout_s=timeout_s)
        if not rep.get("ok"):
            det = rep.get("detail") or rep.get("error")
            raise RuntimeError(f"remote `git {args[0]}` on {node} did not run: {det}")
        return rep

    # -- gitsync: LFS objects (a bundle carries POINTERS, never the content) --
    #
    # A git bundle transports commits/trees/blobs — and an LFS-tracked file's
    # blob IS the ~130-byte pointer. So a node that lacks the real object dies
    # in the smudge filter at checkout ("external filter 'git-lfs
    # filter-process' failed"), and `git lfs pull` cannot save it: lane commits
    # are never pushed, so no LFS server has the object either. The controller
    # is the only holder, hence: stage the missing objects over the same file
    # verbs the bundle rides, BEFORE the checkout.
    SMUDGE_MARKERS = ("smudge filter", "external filter", "filter-process",
                      "Error downloading object", "should have been pointers",
                      "Smudge error")

    @classmethod
    def _smudge_failure(cls, text):
        """The smudge-failure lines in a git leg's stderr, or "" — the check
        that does NOT trust rc (a node with filter.lfs.required=false, or
        lfs.skipdownloaderrors, fails the smudge and still exits 0, leaving
        POINTER TEXT where an asset belongs)."""
        hits = [ln.strip() for ln in (text or "").splitlines()
                if any(m in ln for m in cls.SMUDGE_MARKERS)]
        return "\n".join(hits[:6])

    @staticmethod
    def _lfs_store_relpath(oid):
        """LFS store layout — content-addressed, which is what makes a plain
        dir-sync of the missing objects safe (never a delete: every node's
        store is its own superset)."""
        return f"{oid[:2]}/{oid[2:4]}/{oid}"

    @staticmethod
    def _parse_lfs_ls_files(text):
        """`git lfs ls-files --long <ref>` -> [(oid, marker, path)].
        Line: '<64-hex oid> <*|-> <path>' (paths may contain spaces).
        The marker reports WORKING-TREE materialization ('*' real content on
        disk, '-' pointer or absent) — NOT object-store presence; store
        presence is answered by the file-verb manifest instead."""
        out = []
        for ln in (text or "").splitlines():
            parts = ln.split(" ", 2)
            if len(parts) != 3:
                continue
            oid, mark, path = parts[0].strip().lower(), parts[1], parts[2].strip()
            if len(oid) != 64 or any(c not in "0123456789abcdef" for c in oid):
                continue
            out.append((oid, mark, path))
        return out

    @staticmethod
    def _chunks(seq, n):
        seq = list(seq)
        for i in range(0, len(seq), n):
            yield seq[i:i + n]

    def _git_common_dir(self, node, repo):
        """Absolute .git dir that HOLDS THE LFS STORE. A linked worktree keeps
        its lfs objects in the COMMON dir, so --absolute-git-dir would name the
        wrong store; node=None asks the local repo."""
        args = ("rev-parse", "--path-format=absolute", "--git-common-dir")
        rc, out = (self._local_git(repo, *args) if node is None
                   else self._remote_git(node, repo, *args))
        if rc == 0 and out.strip().startswith("/"):
            return out.strip()
        args = ("rev-parse", "--absolute-git-dir")
        rc, out = (self._local_git(repo, *args) if node is None
                   else self._remote_git(node, repo, *args))
        return out.strip() if rc == 0 else None

    def _lfs_ls_files(self, node, repo, ref):
        """LFS files of ref's tree: [(oid, marker, path)], or None when git-lfs
        is not available there (no git-lfs = no smudge = nothing to repair).
        Empty list = the repo simply has no LFS. node=None asks the local
        repo."""
        args = ("lfs", "ls-files", "--long", ref)
        if node is None:
            rc, out = self._local_git(repo, *args)
        else:
            rep = self.run(node, ["git", "-C", str(repo)] + [str(a) for a in args],
                           timeout_s=180)
            if not rep.get("ok"):
                return None
            rc, out = rep.get("rc", 1), (rep.get("stdout") or "")
        if rc:
            return None
        return self._parse_lfs_ls_files(out)

    def _lfs_stage_missing(self, node, local_repo, remote_repo, r_gitdir,
                           l_head, max_bytes):
        """Give the node every LFS object the TARGET tree needs and its store
        lacks. Enumeration is local (`git lfs ls-files` on the target commit —
        one cheap command, and the controller is the only holder anyway);
        presence is the node's store manifest over the fetch socket, where the
        file NAME is the sha256 of the content, so 'present and intact' is one
        comparison. Only the missing objects travel, and nothing is ever
        deleted. Returns a dict folded into the gitsync result."""
        needed = self._lfs_ls_files(None, local_repo, l_head)
        if needed is None:
            return {"lfs": "skipped (no git-lfs on the controller)"}
        if not needed:
            # repo has no LFS at this commit — clean no-op (and lfs_needed=0
            # tells the caller the pointer scan has nothing to look for)
            return {"lfs_objects": 0, "lfs_needed": 0}
        l_common = self._git_common_dir(None, local_repo)
        r_common = self._git_common_dir(node, remote_repo) or r_gitdir
        if not l_common:
            return {"lfs": "skipped (local git dir unresolved)"}
        l_store = Path(l_common) / "lfs" / "objects"
        r_store = f"{r_common}/lfs/objects"
        addr = self._fetch_addr(node)
        rep = self._fetch_req(addr, proto.make_request(
            proto.OP_TREE_MANIFEST, root=r_store, excludes=[]),
            timeout_ms=600000)                 # cold store hash can be minutes
        if not rep.get("ok"):
            raise RuntimeError(f"cannot read the LFS store of {remote_repo} on "
                               f"{node} ({r_store}): {rep.get('error')}")
        present = {rel: e.get("sha256") for rel, e in (rep["manifest"] or {}).items()}
        want, seen = [], set()
        for oid, _mark, _path in needed:
            if oid in seen:
                continue
            seen.add(oid)
            rel = self._lfs_store_relpath(oid)
            if present.get(rel) != oid:        # absent, or corrupt in-place
                want.append(oid)
        if not want:
            return {"lfs_objects": 0, "lfs_needed": len(seen)}
        have, absent = [], []
        for oid in want:
            (have if (l_store / self._lfs_store_relpath(oid)).is_file()
             else absent).append(oid)
        if not have:
            return {"lfs_objects": 0, "lfs_needed": len(seen),
                    "lfs_absent_locally": absent[:10]}
        nbytes = sum((l_store / self._lfs_store_relpath(o)).stat().st_size
                     for o in have)
        if nbytes > max_bytes:
            raise RuntimeError(
                f"{node} lacks {len(have)} LFS object(s) totalling "
                f"{nbytes/1e6:.0f}MB — that is a store SEED, not a sync delta "
                f"(limit {max_bytes/1e6:.0f}MB). Raise it with --lfs-max-mb, or "
                f"seed the store once with: obt.net.py sync {node} "
                f"{l_store} {r_store}")
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            for oid in have:
                rel = self._lfs_store_relpath(oid)
                dst = Path(td) / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.link(l_store / rel, dst)      # no copy when same fs
                except OSError:
                    import shutil
                    shutil.copyfile(l_store / rel, dst)
            rs = self.sync(node, td, r_store, force=True)   # never --delete
        if rs["tree"] != rs["want_tree"]:
            raise RuntimeError(f"LFS object staging to {r_store} did not verify")
        out = {"lfs_objects": len(have), "lfs_bytes": nbytes,
               "lfs_needed": len(seen)}
        if absent:
            out["lfs_absent_locally"] = absent[:10]
        return out

    # -- gitsync: debris from an ABORTED checkout ----------------------------
    #
    # A checkout that dies in the smudge filter has already created some of the
    # new-in-target files. They survive as untracked collisions ("would be
    # overwritten by checkout") that block every retry. They are OUR litter,
    # not human work — provable: the content is exactly what the target tree
    # holds for that path (real content, or the LFS pointer for it).
    @staticmethod
    def _literal(paths):
        """Pathspec magic: a path is a PATH here, never a glob (assets are full
        of '[' and '#'), and -z output keeps git from quoting non-ASCII names."""
        return [f":(literal){p}" for p in paths]

    def _remote_untracked(self, node, repo, paths):
        """Which of `paths` exist as untracked files on the node (git-only, so
        a restricted seat can answer)."""
        found = []
        for chunk in self._chunks(paths, 400):
            rep = self._remote_git_step(node, repo, "ls-files", "--others",
                                        "--exclude-standard", "-z", "--",
                                        *self._literal(chunk), timeout_s=120)
            if rep.get("rc") != 0:
                raise RuntimeError(
                    f"remote `git ls-files` on {node} failed: "
                    f"{(rep.get('stderr') or '')[-200:]}")
            found += [p for p in (rep.get("stdout") or "").split("\0") if p]
        return found

    def _remote_blob_ids(self, node, repo, paths, no_filters):
        """{path: blob id} for files ON THE NODE, via `git hash-object` — the
        restricted-seat-safe content proof (argv[0] is git, no exec token
        needed). With filters an LFS-materialized file hashes to its POINTER
        blob (what a commit would hold); --no-filters hashes the literal bytes
        (what a pointer file already is). Failure -> {} (proof unavailable =
        not proven ours)."""
        out = {}
        flags = ["--no-filters"] if no_filters else []
        for chunk in self._chunks(paths, 200):
            try:
                rep = self._remote_git_step(node, repo, "hash-object", *flags,
                                            "--", *chunk, timeout_s=180)
            except RuntimeError:
                return {}
            if rep.get("rc") != 0:             # partial output misaligns: drop
                return {}
            ids = [ln.strip() for ln in (rep.get("stdout") or "").splitlines()
                   if ln.strip()]
            if len(ids) != len(chunk):
                return {}
            out.update(dict(zip(chunk, ids)))
        return out

    def _local_tree_blobs(self, repo, ref, paths):
        """{path: blob id} in the LOCAL target tree, for the given paths."""
        out = {}
        for chunk in self._chunks(paths, 400):
            rc, txt = self._local_git(repo, "ls-tree", "-r", "-z", ref, "--",
                                      *self._literal(chunk))
            if rc:
                continue
            for rec in txt.split("\0"):
                if "\t" not in rec:
                    continue
                meta, path = rec.split("\t", 1)
                bits = meta.split()
                if len(bits) >= 3 and bits[1] == "blob":
                    out[path] = bits[2]
        return out

    def _classify_debris(self, node, local_repo, remote_repo, l_head, paths):
        """(ours, foreign) for colliding untracked paths: OURS = the node's
        file content is exactly the target tree's blob for that path, so only
        our own aborted checkout could have written it. Anything else is
        somebody's work and keeps the loud refusal."""
        want = self._local_tree_blobs(local_repo, l_head, paths)
        filtered = self._remote_blob_ids(node, remote_repo, paths, no_filters=False)
        raw = self._remote_blob_ids(node, remote_repo, paths, no_filters=True)
        ours, foreign = [], []
        for p in paths:
            w = want.get(p)
            (ours if w and (filtered.get(p) == w or raw.get(p) == w)
             else foreign).append(p)
        return ours, foreign

    def gitsync(self, node, local_repo, remote_repo, dry=False, lfs=True,
                lfs_max_bytes=1 << 30):
        """Make the node repo's git state (branch + HEAD) equal the controller
        repo's, WITHOUT push: thin git bundle -> content-addressed blob ->
        node fetches from the bundle file and checkouts the same branch@sha.
        LFS objects the target tree needs and the node lacks are staged into
        its store first (a bundle carries pointers only), and the checkout is
        verified by rc AND by a pointer scan (a failed smudge can exit 0).
        Preconditions (fail loudly): local HEAD known and ON A BRANCH; remote
        has no tracked-file dirt; remote HEAD is an ancestor of local HEAD
        (true divergence is a human decision, not a sync)."""
        import subprocess, tempfile
        rc, l_head = self._local_git(local_repo, "rev-parse", "HEAD")
        if rc:
            raise RuntimeError(f"{local_repo} is not a git repo")
        _, l_branch = self._local_git(local_repo, "rev-parse", "--abbrev-ref", "HEAD")
        if l_branch == "HEAD" or not l_branch:
            # detached: the remote leg would compose `checkout -B HEAD <sha>`
            # and die on git's own "'HEAD' is not a valid branch name", which
            # names neither the cause nor the cure. Say both, before anything
            # touches the node. (Lane worktrees are often detached.)
            raise RuntimeError(
                f"local HEAD is DETACHED at {l_head[:12]} in {local_repo} — gitsync "
                f"aligns a BRANCH (it checks the node out to branch@sha), so there is "
                f"no name to give the node: check a branch out here first "
                f"(git -C {local_repo} switch -c <branch>), or gitsync from a branch "
                f"checkout of the same commit")
        rc, r_head = self._remote_git(node, remote_repo, "rev-parse", "HEAD")
        if rc:
            raise RuntimeError(f"remote {remote_repo} on {node}: not a git repo (or git failed)")
        _, r_branch = self._remote_git(node, remote_repo, "rev-parse", "--abbrev-ref", "HEAD")
        r_dirty = self._remote_tracked_dirt(node, remote_repo) or []
        state = {"local": f"{l_branch}@{l_head[:12]}", "remote": f"{r_branch}@{r_head[:12]}",
                 "remote_dirty": len(r_dirty)}
        if r_head == l_head:
            out = {**state, "action": "already-aligned", "ok": True}
            if lfs:
                # a checkout that lied (rc=0 over a failed smudge) leaves the
                # ref AT THE TARGET with stub/pointer assets, and every retry
                # would short-circuit right here calling it aligned — so say
                # what the tree actually holds.
                listing = self._lfs_ls_files(node, remote_repo, l_head)
                stubs = sorted(p for _oid, mark, p in (listing or []) if mark != "*")
                if stubs:
                    out["lfs_pointers"] = stubs[:10]
                    out["action"] += (
                        f" — WARNING {len(stubs)} LFS file(s) on {node} are NOT real "
                        f"content ({', '.join(stubs[:3])}...): the sha matches but "
                        f"those assets are pointers/absent")
            return out
        own_wip = []
        if r_dirty:
            # exempt OUR OWN pushed WIP (pushlog + remote content-hash proof);
            # anything else is somebody's work — refuse.
            pushlog = {}
            try:
                pushlog = json.loads(self._pushlog_path(node, remote_repo).read_text())
            except Exception:
                pass
            # ownership proof, either way: remote content matches what our last
            # push recorded (pushlog) OR matches our CURRENT local content (what
            # we'd push anyway — also heals pushlogs older than the file).
            from obt.net.tree_sync import _sha256_file
            local_sha = {}
            for f in r_dirty:
                lp = Path(local_repo) / f
                if lp.is_file():
                    local_sha[f] = _sha256_file(lp)
            hashes = {}
            rep = self.run(node, ["python3", "-c",
                "import hashlib,sys\n"
                "for f in sys.argv[1:]:\n"
                "  print(hashlib.sha256(open(f,'rb').read()).hexdigest(), f)",
                *r_dirty], cwd=remote_repo, timeout_s=60)
            if not rep.get("ok") and rep.get("error") == "restricted":
                # a restricted seat allowlists 'git' only, so the ownership
                # proof cannot be computed — say THAT, instead of reporting
                # every dirty file as somebody else's work.
                raise RuntimeError(
                    f"{remote_repo} on {node} has {len(r_dirty)} tracked-dirty file(s) "
                    f"({', '.join(r_dirty[:3])}...) and {node} is a RESTRICTED node, so "
                    f"the own-WIP ownership proof (a content hash) cannot run there — "
                    f"clean that tree by hand, or gitsync via an unrestricted node")
            for ln in (rep.get("stdout") or "").splitlines():
                parts = ln.split(None, 1)
                if len(parts) == 2:
                    hashes[parts[1]] = parts[0]
            own_wip = [f for f in r_dirty
                       if hashes.get(f) and
                       (hashes[f] == pushlog.get(f) or hashes[f] == local_sha.get(f))]
            foreign = sorted(set(r_dirty) - set(own_wip))
            if foreign:
                raise RuntimeError(
                    f"remote repo has FOREIGN tracked-file changes ({len(foreign)}: "
                    f"{', '.join(foreign[:3])}...) — pull/merge them first; "
                    f"gitsync refuses to clobber")
        rc, _ = self._local_git(local_repo, "merge-base", "--is-ancestor", r_head, l_head)
        if rc:
            raise RuntimeError(
                f"DIVERGED: remote {r_head[:12]} is not an ancestor of local {l_head[:12]} "
                f"— resolve by hand (gitsync only fast-forwards)")
        n_commits = self._local_git(local_repo, "rev-list", "--count",
                                    f"{r_head}..{l_head}")[1]
        if dry:
            return {**state, "action": f"would-fast-forward {n_commits} commits", "ok": True}
        # The remote leg is composed of DIRECT `git ...` argv steps — never a
        # shell compound. argv[0] is what a restricted seat node allowlists
        # ('git' for the sync token), and `sh -c "git ... && git ..."` presents
        # argv[0]='sh', which such a node correctly refuses. The bundle
        # therefore cannot ride as a run-input either (it materializes into a
        # server-chosen temp workdir whose path only a shell's $PWD could name):
        # it is STAGED at a client-known absolute path via the FETCH socket,
        # whose file verbs move content without exec and stay available under
        # every restrict set. Staging lives inside the remote .git dir — same
        # filesystem, and invisible to `git status`, so it can never look like
        # working-tree dirt.
        rc, r_gitdir = self._remote_git(node, remote_repo, "rev-parse",
                                        "--absolute-git-dir")
        if rc or not r_gitdir:
            raise RuntimeError(f"cannot resolve the git dir of {remote_repo} on {node}")
        stage_dir = f"{r_gitdir}/obtnet-gitsync"
        with tempfile.TemporaryDirectory() as td:
            bpath = Path(td) / "gitsync.bundle"
            r = subprocess.run(["git", "-C", str(local_repo), "bundle", "create",
                                str(bpath), f"{r_head}..HEAD"],
                               capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(f"bundle create failed: {r.stderr.strip()[:200]}")
            data = bpath.read_bytes()
            rs = self.sync(node, td, stage_dir, force=True)   # file verbs only
            if rs["tree"] != rs["want_tree"]:
                raise RuntimeError(f"bundle staging to {stage_dir} did not verify")
        remote_bundle = f"{stage_dir}/gitsync.bundle"
        # what this fast-forward will write, from the LOCAL repo (both commits
        # are here): added paths are the only ones that can collide with an
        # UNTRACKED file, the whole delta is what the smudge filter must serve.
        added, delta = [], set()
        rc, txt = self._local_git(local_repo, "diff", "--no-renames",
                                  "--name-status", "-z", r_head, l_head)
        if rc == 0:
            fields = [f for f in txt.split("\0") if f]
            for st, p in zip(fields[0::2], fields[1::2]):
                delta.add(p)
                if st.startswith("A"):
                    added.append(p)
        lfs_info, debris = {}, []
        try:
            rep = self._remote_git_step(node, remote_repo, "fetch", remote_bundle)
            if rep.get("rc") != 0:
                raise RuntimeError(f"remote git fetch of the bundle failed: "
                                   f"{(rep.get('stderr') or '')[-300:]}")
            if lfs:
                lfs_info = self._lfs_stage_missing(node, local_repo, remote_repo,
                                                   r_gitdir, l_head, lfs_max_bytes)
            if added:
                hits = self._remote_untracked(node, remote_repo, added)
                if hits:
                    debris, foreign_files = self._classify_debris(
                        node, local_repo, remote_repo, l_head, hits)
                    if foreign_files:
                        raise RuntimeError(
                            f"{len(foreign_files)} untracked file(s) on {node} would be "
                            f"overwritten by this checkout and are NOT ours "
                            f"({', '.join(foreign_files[:3])}...) — their content is not "
                            f"what {l_head[:12]} holds for those paths; move or remove "
                            f"them by hand; gitsync refuses to clobber")
                    # every collision is provably our own aborted-checkout
                    # litter (content == the target blob), so -f overwrites
                    # exactly those files with what they were meant to be
            co = ["checkout", "-q"] + (["-f"] if (own_wip or debris) else []) + \
                 ["-B", l_branch, l_head]
            rep = self._remote_git_step(node, remote_repo, *co)
            err = rep.get("stderr") or ""
            smudge = self._smudge_failure(err)
            if rep.get("rc") != 0:
                raise RuntimeError(
                    (f"remote git checkout FAILED IN THE LFS SMUDGE FILTER "
                     f"(the node lacks the object and no server has it): {smudge}"
                     if smudge else f"remote git checkout failed: {err[-300:]}"))
            if smudge:
                # rc lied: a filter marked non-required (or skipdownloaderrors)
                # fails the smudge and still exits 0, leaving POINTER TEXT in
                # the working tree. Never let that pass as a good sync.
                raise RuntimeError(
                    f"remote git checkout returned rc=0 but the LFS smudge filter "
                    f"FAILED (pointer text left in the tree): {smudge}")
        finally:                      # drop the staged bundle (file verb, no exec)
            with tempfile.TemporaryDirectory() as empty:
                try:
                    self.sync(node, empty, stage_dir, delete=True, force=True)
                except Exception:
                    pass              # a leftover bundle is litter, not a failure
                                      # — and never masks the real error
        rc2, r_head2 = self._remote_git(node, remote_repo, "rev-parse", "HEAD")
        if r_head2 != l_head:
            raise RuntimeError(f"post-sync mismatch: remote at {r_head2[:12]}")
        pointers = []
        # NOTE the scan is NOT gated on `lfs`: --no-lfs opts out of MOVING
        # objects, never out of the truth about what landed.
        if delta and lfs_info.get("lfs_needed", 1):
            # POINTER SCAN — the verification that does not trust rc: every
            # LFS path this sync wrote must be real content on disk now
            # ('*'), not a pointer ('-').
            listing = self._lfs_ls_files(node, remote_repo, l_head)
            pointers = sorted(p for oid, mark, p in (listing or [])
                              if mark != "*" and p in delta)
            if pointers:
                raise RuntimeError(
                    f"checkout left {len(pointers)} LFS file(s) as POINTERS on {node} "
                    f"({', '.join(pointers[:3])}...) — the objects never reached the "
                    f"node's store; the tree is at {l_head[:12]} but those assets are "
                    f"text stubs")
        out = {**state, "action": f"fast-forwarded {n_commits} commits",
               "remote_now": f"{l_branch}@{l_head[:12]}",
               "bundle_bytes": len(data), "ok": True, **lfs_info}
        if lfs_info.get("lfs_objects"):
            out["action"] += (f" (+{lfs_info['lfs_objects']} LFS object(s), "
                              f"{lfs_info.get('lfs_bytes', 0)/1e6:.1f}MB)")
        if debris:
            out["cleared_debris"] = debris
            out["action"] += f" (cleared {len(debris)} aborted-checkout file(s))"
        if own_wip:
            out["discarded_own_wip"] = own_wip
            out["action"] += f" (discarded {len(own_wip)} own-WIP file(s) — re-sync to restore)"
        return out

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
#          | msg send|list|ack | push/pull <target> | route <target>
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


# ---------------------------------------------------------------------------
# coordinator messaging (pilot): msg send/list/ack, push/pull, @coords fan-out
# ---------------------------------------------------------------------------

def _utc_ts():
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _parse_deposit_stdout(text):
    """The deposit tool prints one JSON result line; pull it out of stdout."""
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("ok"):
                return d
            raise RuntimeError(f"deposit error: {d.get('error')}")
    raise RuntimeError(f"deposit produced no result line: {text[:300]!r}")


# ---------------------------------------------------------------------------
# ROUTING CLASSES — a send's route is DERIVED from the verb plus DECLARED
# config, never discovered by trying links until one answers. Exactly one class
# applies to a target, and no class ever falls back to another.
#
#   WORK   run/submit/build/test/scene + sync/gitsync/diff/fetch — fleet work.
#          Route: our OWN controller -> our own worker node. That is the ONLY
#          route; WORK never consults cfg['master'] and never uses ssh. A
#          target that is not a node of our controller fails loudly (resolve_node
#          / the controller's unknown_node reply). Not classified here — the
#          worker verbs keep their existing resolution untouched.
#   COORD  msg send/list/ack, @coords — targets are SEATS, and the route
#          follows the coordination ROLE:
#            coord-seat   : I am the master and the sub seat registers
#                           'coord-<seat>' on MY controller -> that node link.
#            coord-master : I am a sub (cfg['master'] declared) -> the master's
#                           controller, reusing the proven deposit protocol
#                           over tcp.
#          No automatic fallback either way: a down link is a loud FAIL that
#          names the dead link and what to do about it.
#   SSH    the target is a declared sshhosts entry AND is not a seat/node name
#          (a machine that runs no node). A first-class declared class, NOT a
#          fallback for the others.
#
# push/pull classify by TARGET, not by verb: a WORK-node target is file staging
# to our own fleet and rides the own-controller work pipe (content-addressed
# sync/fetch, exactly as before); a seat/master/ssh target rides the coord pipe.
# Only `msg` is seat-only.
#
# A target classifiable two ways (e.g. a worker node named like a seat) is a
# CONFIG ERROR: loud FAIL naming the ambiguity, never a silent pick. An unknown
# target fails listing every registry that was checked.
#
# cfg['master'] is read HERE and nowhere else; it is never the client's default
# controller — that stays the seat's OWN controller (bac9de2).
# ---------------------------------------------------------------------------

ROUTE_PROBE_TIMEOUT_MS = 2500   # bounded: a dead controller answers "down", not "hang"
LIVE_AGE_S = 5.0                # heartbeat age past which a registration is stale

CLASS_WORK = "work-node"
CLASS_COORD_SEAT = "coord-seat"
CLASS_COORD_MASTER = "coord-master"
CLASS_SSH = "ssh"

# reply codes meaning the LINK failed (nothing was delivered) rather than the
# recipient refusing. Both are loud FAILs — they differ only in the hint.
LINK_ERRORS = (proto.ERR_RELAY_TIMEOUT, proto.ERR_UNKNOWN_NODE, proto.ERR_TIMEOUT)


class RouteError(RuntimeError):
    """No route, an ambiguous route, or the single computed route is down.
    Carries the `checked` registry lines so the failure says what was looked
    at."""

    def __init__(self, message, checked=None):
        self.checked = list(checked or [])
        super().__init__(message)


def _master_addr():
    """Master controller address, declared by `obt.coord.seat.py init --role sub
    --master ...` under cfg['master']. Its presence is what makes this seat a
    SUB; it is deliberately NOT the client's default controller."""
    addr = _load_global_config().get("master")
    return proto.normalize_controller_addr(addr) if addr else None


def _master_coordid():
    """Optional cfg['master_coordid']: the master seat's name. Declared -> the
    master is matched BY NAME. Absent -> a sub's otherwise-unclassified
    coordination target is the master BY ROLE (a sub's only coordination link
    goes up)."""
    return _load_global_config().get("master_coordid")


def _roster(client, timeout_ms=ROUTE_PROBE_TIMEOUT_MS):
    """{name: record} registered at `client`'s controller, or None when that
    controller does not answer inside the bounded probe. None means UNKNOWN,
    never "empty" — classification says so out loud instead of guessing."""
    try:
        rep = client._request(proto.make_request(proto.OP_LIST_NODES),
                              timeout_ms=timeout_ms)
    except (zmq.ZMQError, OSError, ValueError):
        return None
    if not rep.get("ok"):
        return None
    return {n["name"]: n for n in rep.get("nodes", [])}


def _liveness(rec):
    """(is_live, human) for a roster record."""
    if rec is None:
        return False, "NOT REGISTERED"
    age = rec.get("last_ping_age_s")
    if age is None:
        return False, "no heartbeat"
    return (age < LIVE_AGE_S,
            f"{'LIVE' if age < LIVE_AGE_S else 'STALE'} ping_age={age}s")


def classify(c, target):
    """Derive THE route for `target` from declared config + registries.
    Deterministic and side-effect free (nothing is sent). Returns
      {class, target, transport, controller, controller_role, client, node,
       dest, record, checked[]}
    Raises RouteError on ambiguity, when no class applies, or when the computed
    class's controller cannot be reached to complete the route."""
    checked = []
    own_addr = c.controller_addr
    roster = _roster(c)
    if roster is None:
        checked.append(f"own fleet roster: controller {own_addr} UNREACHABLE "
                       f"(no reply in {ROUTE_PROBE_TIMEOUT_MS}ms)")
    else:
        checked.append(f"own fleet roster ({own_addr}): "
                       f"{','.join(sorted(roster)) or '(empty)'}")

    seat_node = None          # seat registration on our own controller
    work_node = None          # plain worker node on our own controller
    if roster is not None:
        coord_name = target if target.startswith("coord-") else f"coord-{target}"
        if coord_name in roster:
            seat_node = coord_name
        if target in roster and not target.startswith("coord-"):
            work_node = target

    maddr = _master_addr()
    mid = _master_coordid()
    hosts = _sshhosts()
    checked.append("master: " + (
        f"{maddr}" + (f" coordid={mid}" if mid else " (coordid not declared)")
        if maddr else "not declared — this seat is a master"))
    checked.append(f"sshhosts: {','.join(sorted(hosts)) or '(none)'}")

    master_target = False
    if maddr:
        if mid:
            master_target = (target == mid)
        else:
            # ROLE rule: a sub's coordination goes UP. Anything that is not one
            # of our own seat/worker nodes and not a declared ssh host is the
            # master. Declare cfg['master_coordid'] to make it a name match.
            master_target = not seat_node and not work_node and target not in hosts

    # -- collision = config error, never a silent pick -----------------------
    named = []
    if seat_node:
        named.append(f"{CLASS_COORD_SEAT} (node {seat_node} on {own_addr})")
    if work_node:
        named.append(f"{CLASS_WORK} (node {work_node} on {own_addr})")
    if master_target and mid:
        named.append(f"{CLASS_COORD_MASTER} (declared master coordid {mid})")
    if len(named) > 1:
        raise RouteError(
            f"AMBIGUOUS target {target!r}: classifiable as " + " AND ".join(named)
            + " — that is a config error (rename the worker node or the seat); "
              "routing refuses to pick", checked)

    if seat_node:
        return {"class": CLASS_COORD_SEAT, "target": target, "transport": "node",
                "controller": own_addr, "controller_role": "own", "client": c,
                "node": seat_node, "dest": None, "record": roster.get(seat_node),
                "checked": checked}
    if work_node:
        return {"class": CLASS_WORK, "target": target, "transport": "node",
                "controller": own_addr, "controller_role": "own", "client": c,
                "node": work_node, "dest": None, "record": roster.get(work_node),
                "checked": checked}
    if master_target:
        mclient = Client(maddr)
        mroster = _roster(mclient)
        if mroster is None:
            raise RouteError(
                f"class={CLASS_COORD_MASTER}: master controller {maddr} unreachable "
                f"(no reply in {ROUTE_PROBE_TIMEOUT_MS}ms) — the master seat owns "
                f"that controller; an explicit --controller override is available",
                checked)
        checked.append(f"master roster ({maddr}): "
                       f"{','.join(sorted(mroster)) or '(empty)'}")
        node = next((n for n in (target, f"coord-{target}") if n in mroster), None)
        if node is None:
            raise RouteError(
                f"class={CLASS_COORD_MASTER}: master controller {maddr} registers "
                f"neither {target!r} nor 'coord-{target}' — the master seat must run "
                f"a node there to receive coordination", checked)
        return {"class": CLASS_COORD_MASTER, "target": target, "transport": "node",
                "controller": maddr, "controller_role": "master", "client": mclient,
                "node": node, "dest": None, "record": mroster.get(node),
                "checked": checked}
    if target in hosts:
        return {"class": CLASS_SSH, "target": target, "transport": "ssh",
                "controller": None, "controller_role": None, "client": None,
                "node": None, "dest": hosts[target], "record": None,
                "checked": checked}
    raise RouteError(f"no route to {target!r}: no routing class applies", checked)


def coord_route(c, target):
    """classify() for `msg` — MESSAGES address seats only. A fleet WORKER node
    has no coordination inbox: loud FAIL, never a silent deposit. (push/pull do
    NOT use this: they classify by target, work-node included.)"""
    r = classify(c, target)
    if r["class"] == CLASS_WORK:
        raise RouteError(
            f"class={CLASS_WORK}: {target!r} is a fleet WORKER node on "
            f"{r['controller']}, not a coordination seat — messages address a "
            f"seat (registered as 'coord-<seat>'), the master (cfg['master']), "
            f"or an sshhosts machine", r["checked"])
    return r


def _link_down(r, why):
    """The loud FAIL text for a computed route whose link is down — the hint
    names who owns the dead end, which differs per class."""
    if r["class"] == CLASS_COORD_MASTER:
        return (f"class={r['class']}: master link {r['node']}@{r['controller']} down "
                f"({why}) — the master seat owns that controller/node; an explicit "
                f"--controller override is available")
    if r["class"] == CLASS_WORK:
        return (f"class={r['class']}: node {r['node']} link stalled/down on "
                f"{r['controller']} ({why}) — check `obt.net.py list`")
    return (f"class={r['class']}: {r['node']} link stalled/down on {r['controller']} "
            f"({why}) — that seat restarts its own coord node")


def _print_checked(checked, out=sys.stderr, indent="  "):
    for line in checked or []:
        print(f"{indent}checked: {line}", file=out)


def _coord_targets(c):
    """@coords fan-out set: every LIVE node named coord-* on our own controller
    PLUS every sshhosts entry (ordered, deduped). The roster probe is BOUNDED —
    an unreachable own controller degrades the set to the declared sshhosts, it
    never aborts the broadcast. (Callers classify each target and collapse
    duplicates onto one route.)"""
    out = []
    roster = _roster(c) or {}
    for n in sorted(roster):
        if n.startswith("coord-") and n not in out:
            live, _ = _liveness(roster[n])
            if live:
                out.append(n)
    for h in sorted(_sshhosts()):
        if h not in out:
            out.append(h)
    return out


def _msg_send_node(r, sender, subject, ts, payload_b64):
    """Deposit over the computed node route (`r` from coord_route/classify):
    argv is exec'd DIRECTLY on the node (no shell), so subject/base64 payload
    carry safely as argv elements. On a restricted seat this passes because the
    deposit head is allow-listed.
    A DOWN LINK raises RouteError naming the dead link (no fallback exists — the
    class is the route); a recipient that ANSWERS badly (restricted refusal, the
    deposit tool erroring) raises RuntimeError: an application error to surface,
    not a routing problem."""
    argv = ["obt.net.msg.deposit.py", "--from", sender, "--subject", subject,
            "--ts", ts, "--payload-b64", payload_b64]
    nc, node = r["client"], r["node"]
    try:
        rep = nc.run(node, argv, timeout_s=30)
    except (zmq.ZMQError, OSError) as e:          # controller itself unreachable
        raise RouteError(_link_down(r, f"{type(e).__name__} {e}"), r["checked"])
    if not rep.get("ok"):
        err = rep.get("error")
        det = f"{err}{': ' + str(rep['detail']) if rep.get('detail') else ''}"
        if err in LINK_ERRORS:
            raise RouteError(_link_down(r, det), r["checked"])
        raise RuntimeError(f"{node} refused the deposit: {det}")
    if rep.get("rc") != 0:
        raise RuntimeError(f"deposit rc={rep.get('rc')} on {node}: "
                           f"{rep.get('stderr','')[:200]}")
    return _parse_deposit_stdout(rep.get("stdout", ""))


def _msg_send_ssh(dest, sender, subject, ts, payload_b64):
    """Deposit over bare ssh: the entire message rides a JSON blob on STDIN
    (zero shell interpolation of subject/payload); the remote shell only ever
    sees the fixed `python3 <path> --stdin-json` words. Runs the same tool via
    system python3 — no obt venv needed on the recipient."""
    blob = json.dumps({"from": sender, "subject": subject, "ts": ts,
                       "payload_b64": payload_b64}).encode("utf-8")
    argv = ["ssh", "-o", "BatchMode=yes", dest,
            "python3", SSH_DEPOSIT_PATH, "--stdin-json"]
    try:
        r = subprocess.run(argv, input=blob, capture_output=True, timeout=45)
    except subprocess.TimeoutExpired:
        raise RouteError(f"class={CLASS_SSH}: ssh {dest} did not answer in 45s "
                         f"— the ssh route is down (no fallback: ssh IS a class)")
    if r.returncode == 255:                        # ssh's own transport failure
        raise RouteError(f"class={CLASS_SSH}: ssh {dest} unreachable (rc=255): "
                         f"{r.stderr.decode(errors='replace')[:200]}")
    if r.returncode != 0:                          # the recipient answered badly
        raise RuntimeError(f"ssh deposit rc={r.returncode}: "
                           f"{r.stderr.decode(errors='replace')[:300]}")
    return _parse_deposit_stdout(r.stdout.decode(errors="replace"))


def _do_msg_send(c, target, sender, subject, ts, payload_b64):
    """Route one message by CLASS (single computed route, no fallback);
    returns (class, deposit_result_dict)."""
    r = coord_route(c, target)
    if r["transport"] == "node":
        return r["class"], _msg_send_node(r, sender, subject, ts, payload_b64)
    return r["class"], _msg_send_ssh(r["dest"], sender, subject, ts, payload_b64)


def _read_frontmatter(path):
    """Parse the from/subject/ts frontmatter of an inbox .md; best-effort."""
    fm = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            first = f.readline()
            if first.strip() != "---":
                return fm
            for line in f:
                if line.strip() == "---":
                    break
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
    except OSError:
        pass
    return fm


def _inbox_messages():
    """Local unacked inbox messages, newest first: list of (ts, from, subject, path)."""
    inbox = coord_root() / "inbox"
    rows = []
    if inbox.is_dir():
        for p in inbox.glob("*.md"):
            fm = _read_frontmatter(p)
            rows.append((fm.get("ts", p.name[:16]), fm.get("from", "?"),
                         fm.get("subject", ""), str(p)))
    rows.sort(key=lambda r: r[0], reverse=True)
    return rows


def _push_pull(c, target, local, remote, pull):
    """File transfer routed by the target's CLASS — the general classifier, no
    verb special-casing: a work-node target stages into our own fleet over the
    own-controller node pipe (content-addressed sync/fetch), a seat/master
    target rides the same pipe at its controller, an ssh-class target uses scp.
    One computed route, no fallback. Returns the class token."""
    r = classify(c, target)
    if r["transport"] == "ssh":
        dest = r["dest"]
        if pull:
            argv = ["scp", "-q", "-o", "BatchMode=yes", f"{dest}:{remote}", local]
        else:
            argv = ["scp", "-q", "-o", "BatchMode=yes", local, f"{dest}:{remote}"]
        try:
            rr = subprocess.run(argv, capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            raise RouteError(f"class={CLASS_SSH}: scp {dest} did not answer in 300s")
        if rr.returncode == 255:
            raise RouteError(f"class={CLASS_SSH}: ssh {dest} unreachable (rc=255): "
                             f"{rr.stderr.decode(errors='replace')[:200]}")
        if rr.returncode != 0:
            raise RuntimeError(f"scp rc={rr.returncode}: "
                               f"{rr.stderr.decode(errors='replace')[:300]}")
        return r["class"]
    nc, node = r["client"], r["node"]
    # LOCAL filesystem work happens outside the link-error catch: a missing
    # local file is our own error, never a "dead link" diagnosis.
    payload = None if pull else Path(local).read_bytes()
    try:
        if pull:                  # hash the remote file, fetch its blob by sha
            rem_dir = os.path.dirname(remote) or "."
            rep = nc._fetch_req(nc._fetch_addr(node), proto.make_request(
                proto.OP_TREE_MANIFEST, root=rem_dir, excludes=[]))
            if not rep.get("ok"):
                raise RuntimeError(f"remote manifest failed: {rep.get('error')}")
            entry = (rep.get("manifest") or {}).get(os.path.basename(remote))
            if not entry or entry.get("t") != "f":
                raise RuntimeError(f"remote file not found: {remote}")
            nc.fetch(node, entry["sha256"], local)
        else:                     # stage the single file, content-sync it over
            import tempfile
            import shutil
            tmp = Path(tempfile.mkdtemp(prefix="obtnet_push_"))
            try:
                (tmp / os.path.basename(remote)).write_bytes(payload)
                nc.sync(node, str(tmp), os.path.dirname(remote) or ".")
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
    except zmq.ZMQError as e:                  # the link, not the recipient
        raise RouteError(_link_down(r, f"{type(e).__name__} {e}"), r["checked"])
    return r["class"]


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
    p = sub.add_parser("gitsync",
                       help="align node repo's git base (branch+HEAD) to the controller's "
                            "via bundle (no push); then diffs/patches line up")
    p.add_argument("node")
    p.add_argument("local_repo")
    p.add_argument("remote_repo")
    p.add_argument("--dry", action="store_true")
    p.add_argument("--tree", action="store_true",
                   help="follow with a content sync (carries the uncommitted delta)")
    p.add_argument("--exclude", action="append", default=[],
                   help="extra excludes for --tree")
    p.add_argument("--no-lfs", action="store_true",
                   help="skip LFS object staging (the pointer-scan verification "
                        "still runs — you can opt out of moving bytes, not of "
                        "knowing what landed)")
    p.add_argument("--lfs-max-mb", type=int, default=1024,
                   help="refuse an LFS staging bigger than this (a store SEED, "
                        "not a sync delta); default 1024")
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
    p.add_argument("--force", action="store_true",
                   help="override the dirt guard (clobber node-side edits)")
    p.add_argument("--dry", action="store_true", help="report the diff, change nothing")
    p.add_argument("--exclude", action="append", default=[], help="extra exclude pattern")
    p.add_argument("-v", action="store_true", help="list changed paths (first 50)")
    # -- coordinator messaging pilot ---------------------------------------
    pmsg = sub.add_parser("msg", help="coordinator messaging (send/list/ack)")
    msub = pmsg.add_subparsers(dest="msgcmd", required=True)
    ps = msub.add_parser("send", help="deposit a message to a node or ssh host "
                                       "(or @coords to broadcast)")
    ps.add_argument("target")
    ps.add_argument("--subject", required=True)
    g = ps.add_mutually_exclusive_group(required=True)
    g.add_argument("--body", help="inline message body text")
    g.add_argument("--body-file", help="read message body from a file ('-' = stdin)")
    pls = msub.add_parser("list", help="list this box's local inbox, newest first")
    pls.add_argument("--inbox", action="store_true",
                     help="(default view; reserved for future scopes)")
    pak = msub.add_parser("ack", help="move an inbox message to inbox/acked/")
    pak.add_argument("ref", help="message file path, or a ts / filename fragment")
    ppush = sub.add_parser("push", help="send a file to a seat/ssh host (routed like msg)")
    ppush.add_argument("target"); ppush.add_argument("local"); ppush.add_argument("remote")
    ppull = sub.add_parser("pull", help="fetch a file from a seat/ssh host (routed like msg)")
    ppull.add_argument("target"); ppull.add_argument("remote"); ppull.add_argument("local")
    prt = sub.add_parser("route", help="show the derived routing CLASS, the single "
                                       "computed route and its liveness (sends nothing)")
    prt.add_argument("target")
    args = ap.parse_args(raw)

    c = Client(args.controller)
    jm = args.json

    if args.cmd == "config":
        if args.addr:
            cfg_path = config_path()
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            addr = proto.normalize_controller_addr(args.addr)
            cfg_path.write_text(json.dumps({"controller": addr}, indent=1))
            _verdict(True, "config", addr, f"written {cfg_path}", jm,
                     {"controller": addr, "path": str(cfg_path)})
        else:
            addr, src = resolve_controller(args.controller)
            if jm:
                print(json.dumps({"controller": addr, "source": src}))
            else:
                print(f"controller: {addr}   (from {src})")
        return 0

    if args.cmd == "msg":
        if args.msgcmd == "send":
            sender = _coordid()
            ts = _utc_ts()
            if args.body_file:
                data = (sys.stdin.buffer.read() if args.body_file == "-"
                        else Path(args.body_file).read_bytes())
            else:
                data = (args.body or "").encode("utf-8")
            payload_b64 = base64.b64encode(data).decode()
            if args.target == "@coords":
                targets = _coord_targets(c)
                if not targets:
                    _verdict(False, "msg", "@coords",
                             "no coord-* nodes or sshhosts to broadcast to", jm)
                    return 1
                fails, seen = [], {}
                for t in targets:
                    # the same seat can appear twice (coord-<seat> node AND an
                    # sshhosts entry) — classification collapses both onto ONE
                    # route, so deposit once, not twice.
                    try:
                        r = coord_route(c, t)
                        key = (r["class"], r["controller"], r["node"], r["dest"])
                        if key in seen:
                            print(f"[obtnet] {t} -> same route as {seen[key]} "
                                  f"(class={r['class']}); skipped", file=sys.stderr)
                            continue
                        seen[key] = t
                        via, res = _do_msg_send(c, t, sender, args.subject, ts,
                                                payload_b64)
                        _verdict(True, "msg", t,
                                 f"subject<{args.subject}> via<{via}>", jm,
                                 {"target": t, "via": via, "path": res.get("path")})
                    except Exception as e:
                        if isinstance(e, RouteError) and not jm:
                            _print_checked(e.checked)
                        _verdict(False, "msg", t, f"error={e}", jm, {"error": str(e)})
                        fails.append(t)
                n = len(seen) + len(fails)
                _verdict(not fails, "msg", f"@coords({n})",
                         f"ok={len(seen)}/{n}"
                         + (f" failed={fails}" if fails else ""), jm)
                return 0 if not fails else 1
            try:
                via, res = _do_msg_send(c, args.target, sender, args.subject, ts,
                                        payload_b64)
            except Exception as e:
                if isinstance(e, RouteError) and not jm:
                    _print_checked(e.checked)
                _verdict(False, "msg", args.target, f"error={e}", jm, {"error": str(e)})
                return 1
            _verdict(True, "msg", args.target,
                     f"subject<{args.subject}> via<{via}>", jm,
                     {"target": args.target, "via": via, "path": res.get("path"),
                      "ts": ts, "from": sender})
            return 0

        if args.msgcmd == "list":
            rows = _inbox_messages()
            if jm:
                print(json.dumps([{"ts": r[0], "from": r[1], "subject": r[2],
                                   "path": r[3]} for r in rows]))
            else:
                for ts_, frm, subj, pth in rows:
                    print(f"{ts_}  {frm:16s}  {subj[:50]:50s}  {pth}")
            _verdict(True, "msg", "inbox", f"n={len(rows)}", jm)
            return 0

        if args.msgcmd == "ack":
            inbox = coord_root() / "inbox"
            acked = inbox / "acked"
            cand = Path(args.ref)
            if not cand.is_file():
                matches = [p for p in inbox.glob("*.md")
                           if args.ref in p.name]
                if len(matches) == 0:
                    _verdict(False, "msg", "ack", f"no inbox message matches {args.ref!r}",
                             jm)
                    return 1
                if len(matches) > 1:
                    _verdict(False, "msg", "ack",
                             f"ambiguous ref {args.ref!r} matches {len(matches)}: "
                             f"{sorted(p.name for p in matches)}", jm)
                    return 1
                cand = matches[0]
            acked.mkdir(parents=True, exist_ok=True)
            target_path = acked / cand.name
            os.replace(str(cand), str(target_path))
            _verdict(True, "msg", "ack", f"{cand.name} -> inbox/acked/", jm,
                     {"acked": str(target_path)})
            return 0

    if args.cmd in ("push", "pull"):
        try:
            via = _push_pull(c, args.target, args.local, args.remote,
                             pull=(args.cmd == "pull"))
        except Exception as e:
            if isinstance(e, RouteError) and not jm:
                _print_checked(e.checked)
            _verdict(False, args.cmd, args.target, f"error={e}", jm, {"error": str(e)})
            return 1
        _verdict(True, args.cmd, args.target,
                 f"{args.local} {'<-' if args.cmd == 'pull' else '->'} {args.remote} "
                 f"via<{via}>", jm,
                 {"local": args.local, "remote": args.remote, "via": via})
        return 0

    if args.cmd == "route":
        # topology-verification instrument: derive the CLASS and the single
        # computed route, report that route's liveness. Sends NOTHING.
        try:
            r = classify(c, args.target)
        except RouteError as e:
            if jm:
                print(json.dumps({"ok": False, "verb": "route",
                                  "target": args.target, "class": None,
                                  "error": str(e), "checked": e.checked}))
            else:
                _print_checked(e.checked, out=sys.stdout, indent="")
                _verdict(False, "route", args.target, str(e))
            return 1
        if r["transport"] == "node":
            live, live_txt = _liveness(r["record"])
            link = f"{r['node']}@{r['controller']}"
        else:
            live, live_txt = True, "unprobed (ssh is dialed on use)"
            link = f"ssh:{r['dest']}"
        if jm:
            print(json.dumps({"ok": bool(live), "verb": "route",
                              "target": args.target, "class": r["class"],
                              "transport": r["transport"],
                              "controller": r["controller"],
                              "controller_role": r["controller_role"],
                              "node": r["node"], "dest": r["dest"],
                              "liveness": live_txt, "checked": r["checked"]}))
            return 0 if live else 1
        print(f"target:     {args.target}")
        print(f"class:      {r['class']}")
        print(f"transport:  {r['transport']}")
        if r["transport"] == "node":
            print(f"controller: {r['controller']} ({r['controller_role']})")
            print(f"node:       {r['node']}")
        else:
            print(f"ssh dest:   {r['dest']}")
        print(f"liveness:   {live_txt}")
        _print_checked(r["checked"], out=sys.stdout, indent="")
        _verdict(live, "route", args.target,
                 f"class={r['class']} via={r['transport']} link={link} {live_txt}")
        return 0 if live else 1

    # '@' selectors route to a node; comma-lists and '@each[:terms]' FAN OUT
    # across nodes (working-copy verbs loop; execution verbs submit-all then
    # wait-all = simultaneous cross-machine runs).
    FAN_VERBS = ("run", "build", "test", "scene", "sync", "gitsync")
    fan_targets = None
    if getattr(args, "node", None) and (args.node.startswith("@") or "," in args.node):
        try:
            targets = c.resolve_nodes(args.node) if args.cmd in FAN_VERBS \
                else [c.resolve_node(args.node)]
        except (KeyError, RuntimeError) as e:
            _verdict(False, args.cmd, args.node, f"error={e}", jm, {"error": str(e)})
            return 1
        if len(targets) == 1:
            if targets[0] != args.node:
                print(f"[obtnet] {args.node} -> {targets[0]}", file=sys.stderr)
            args.node = targets[0]
        else:
            print(f"[obtnet] {args.node} -> {','.join(targets)}", file=sys.stderr)
            fan_targets = targets

    if fan_targets and args.cmd in ("sync", "gitsync"):
        fails = []
        for n in fan_targets:
            try:
                if args.cmd == "gitsync":
                    r = c.gitsync(n, args.local_repo, args.remote_repo, dry=args.dry,
                                  lfs=not args.no_lfs,
                                  lfs_max_bytes=args.lfs_max_mb * 1000000)
                    _verdict(True, "gitsync", n, r["action"], jm, r if jm else None)
                else:
                    r = c.sync(n, args.local_dir, args.remote_dir, pull=args.pull,
                               delete=args.delete, excludes=args.exclude, dry=args.dry,
                               force=args.force)
                    ok = args.dry or r["tree"] == r["want_tree"]
                    _verdict(ok, "sync", n,
                             f"files={r.get('files')} tree="
                             + ("DRY" if args.dry else
                                ("MATCH" if ok else "MISMATCH!")), jm, r if jm else None)
                    if not ok:
                        fails.append(n)
            except Exception as e:    # one node's failure is a verdict, never
                _verdict(False, args.cmd, n, f"error={e}", jm, {"error": str(e)})
                fails.append(n)       # a traceback that eats the whole fan-out
        _verdict(not fails, args.cmd, f"fleet({len(fan_targets)})",
                 f"ok={len(fan_targets)-len(fails)}/{len(fan_targets)}"
                 + (f" failed={fails}" if fails else ""), jm)
        return 0 if not fails else 1

    if fan_targets and args.cmd in ("run", "build", "test", "scene"):
        kind = {"run": "command", "build": "project.build",
                "test": "test", "scene": "scene.run"}[args.cmd]
        argv2 = cmd_argv or (["ork.build.py"] if args.cmd == "build" else None)
        if not argv2:
            print(f"no argv given (use: {args.cmd} <nodes> -- cmd...)", file=sys.stderr)
            return 2
        env = dict(kv.split("=", 1) for kv in getattr(args, "env", []) or [])
        extra = {}
        if args.cmd == "scene":
            extra = {"windowed": args.windowed, "markers": args.markers}
        timeout = getattr(args, "timeout", 600)
        jobs = {}
        for n in fan_targets:                      # submit ALL first = simultaneous
            rep = c.job_submit(n, argv2, kind=kind, env=env,
                               cwd=getattr(args, "cwd", None), timeout_s=timeout,
                               output_globs=getattr(args, "out", []) or [], **extra)
            if rep.get("ok"):
                jobs[n] = rep["job"]
            else:
                _verdict(False, args.cmd, n, f"submit error={rep.get('error')}", jm)
        fails = [n for n in fan_targets if n not in jobs]
        for n, job in jobs.items():                # then wait each (they overlap)
            rep = c.job_wait(n, job, timeout_s=timeout + 60)
            s = rep.get("summary") or {}
            ok = bool(s.get("verdict_ok")) if s else                 (rep.get("state") == proto.JOB_DONE and rep.get("rc") == 0)
            detail = (f"errors={s.get('errors')} warnings={s.get('warnings')}"
                      if args.cmd == "build" else
                      f"passed={s.get('passed')} failed={s.get('failed')}"
                      if args.cmd == "test" else f"rc={rep.get('rc')}")
            _verdict(ok, args.cmd, n, f"{detail} {rep.get('dur_s', 0)}s job={job}", jm,
                     {"node": n, "job": job, "summary": s} if jm else None)
            if args.cmd == "run" and not jm:       # fleet-run: show a bounded tail
                for ln in (c.job_log(n, job, tail=5).get("lines") or []):
                    print(f"  {n}: {ln}")
            if not ok:
                fails.append(n)
        _verdict(not fails, args.cmd, f"fleet({len(fan_targets)})",
                 f"ok={len(fan_targets)-len(fails)}/{len(fan_targets)}"
                 + (f" failed={sorted(fails)}" if fails else ""), jm)
        return 0 if not fails else 1

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
                det = rep.get("detail")
                _verdict(False, "run", args.node,
                         f"error={rep.get('error')}{': ' + det if det else ''} {dt:.1f}s",
                         jm, {"error": rep.get("error"), "detail": det})
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
            det = rep.get("detail")
            _verdict(ok, "submit", args.node,
                     f"job={rep.get('job')}" if ok else
                     f"error={rep.get('error')}{': ' + det if det else ''}",
                     jm, {"job": rep.get("job"), "error": rep.get("error"), "detail": det})
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
            det = rep.get("detail")
            _verdict(False, args.cmd, args.node,
                     f"error={rep.get('error')}{': ' + det if det else ''}", jm,
                     {"error": rep.get("error"), "detail": det})
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
                       excludes=args.exclude, dry=args.dry, force=args.force)
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

    if args.cmd == "gitsync":
        try:
            r = c.gitsync(args.node, args.local_repo, args.remote_repo, dry=args.dry,
                          lfs=not args.no_lfs,
                          lfs_max_bytes=args.lfs_max_mb * 1000000)
        except Exception as e:        # ANY failure ends in a verdict line — a
            # smudge fatal that escaped as a traceback (or as silence) is the
            # rc lie this verb is not allowed to tell.
            _verdict(False, "gitsync", args.node, f"error={e}", jm, {"error": str(e)})
            return 1
        _verdict(True, "gitsync", args.node,
                 f"{r['action']} local={r['local']} remote={r['remote']}"
                 + (f" bundle={r['bundle_bytes']}B" if "bundle_bytes" in r else ""),
                 jm, r if jm else None)
        if args.tree and not args.dry:
            rs = c.sync(args.node, args.local_repo, args.remote_repo,
                        excludes=args.exclude)
            match = rs["tree"] == rs["want_tree"]
            _verdict(match, "gitsync+tree", args.node,
                     f"files={rs['files']} del={rs['deleted']} "
                     f"tree={'MATCH' if match else 'MISMATCH!'}", jm, rs if jm else None)
            return 0 if match else 1
        return 0

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
