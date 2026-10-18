#!/usr/bin/env python3
"""tests/test_gitsync_lfs.py — obt.net gitsync: LFS transport, aborted-checkout
debris, and the smudge rc lie. Two scratch git repos on THIS box; no obtnet
node, no controller, no fleet.

The node legs are served locally (`run` execs here; the fetch-socket file verbs
are answered by the same tree_sync machinery a node uses), so everything the
verb decides — LFS enumeration/staging, debris classification, checkout
composition, pointer scan — is the real code under test. Imports the REPO copy
of obt.net, not an installed mirror.

  ./tests/test_gitsync_lfs.py          # one PASS/FAIL line per case
Needs git and git-lfs on PATH; skips (rc 0) without git-lfs.
"""
import os
import shutil
import subprocess
import sys
import traceback
import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))     # the repo copy wins

from obt.net import client as netclient, proto, tree_sync   # noqa: E402

LAB = Path(os.environ.get("TMPDIR", "/tmp")) / "obtnet-gitsync-lfs-gate"
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
           GIT_CONFIG_NOSYSTEM="1")
RESULTS = []


class LocalClient(netclient.Client):
    def __init__(self, restricted=False):
        self.controller_addr = "tcp://127.0.0.1:7461"
        self.blobs = {}                      # sha -> bytes (the node's cache)
        self.restricted = restricted         # allow only argv[0] == 'git'
        self.run_log = []
        self.fail_next_checkout = False

    # -- exec leg ----------------------------------------------------------
    def run(self, node, argv, env=None, cwd=None, timeout_s=300,
            inputs=None, output_globs=None):
        argv = [str(a) for a in argv]
        self.run_log.append(argv)
        if self.restricted and argv[0] != "git":
            return {"ok": False, "error": "restricted", "detail": f"head {argv[0]!r}"}
        run_env = dict(ENV)
        run_env.update(env or {})
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                           env=run_env)
        return {"ok": True, "rc": r.returncode, "stdout": r.stdout, "stderr": r.stderr}

    def _run_long(self, node, argv, cwd=None, env=None, timeout_s=10800):
        return self.run(node, argv, cwd=cwd, env=env, timeout_s=timeout_s)

    # -- fetch socket ------------------------------------------------------
    def _fetch_addr(self, node):
        return "local"

    def _fetch_req(self, addr, payload, timeout_ms=120000):
        msg = proto.parse_message(payload)
        op = msg.get("op")
        if op == proto.OP_TREE_MANIFEST:
            m = tree_sync.build_manifest(Path(msg["root"]).expanduser(),
                                         msg.get("excludes"))
            return proto.parse_message(
                proto.make_reply_ok(manifest=m, tree=tree_sync.tree_hash(m)))
        if op == proto.OP_BLOB_PUT:
            sha = msg["sha256"]
            if msg.get("probe"):
                if sha in self.blobs:
                    return proto.parse_message(proto.make_reply_ok(done=True, dedup=True))
                partial = self.blobs.get(sha + ".part", b"")
                return proto.parse_message(proto.make_reply_ok(
                    done=False, next_offset=len(partial)))
            data = base64.b64decode(msg["bytes_b64"])
            off, total = int(msg["offset"]), int(msg["total"])
            buf = bytearray(self.blobs.get(sha + ".part", b""))
            buf[off:off + len(data)] = data
            if off + len(data) < total:
                self.blobs[sha + ".part"] = bytes(buf)
                return proto.parse_message(proto.make_reply_ok(
                    done=False, next_offset=off + len(data)))
            self.blobs[sha] = bytes(buf)
            self.blobs.pop(sha + ".part", None)
            return proto.parse_message(proto.make_reply_ok(done=True))
        if op == proto.OP_TREE_APPLY:
            root = Path(msg["root"]).expanduser()
            entries = msg["entries"]
            nf, nl, nd = tree_sync.materialize_tree(
                root, entries, lambda sha: self.blobs[sha],
                deletes=msg.get("deletes") or [])
            m = tree_sync.build_manifest(root, msg.get("excludes"))
            return proto.parse_message(proto.make_reply_ok(
                files=nf, links=nl, deleted=nd, tree=tree_sync.tree_hash(m)))
        if op == proto.OP_FETCH_CHUNK:
            data = self.blobs[msg["sha256"]]
            off = int(msg.get("offset", 0))
            chunk = data[off:off + proto.FETCH_CHUNK_BYTES]
            return proto.parse_message(proto.make_reply_ok(
                bytes_b64=base64.b64encode(chunk).decode(),
                eof=(off + len(chunk) >= len(data))))
        raise AssertionError(f"unhandled op {op}")


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", str(repo)] + [str(a) for a in args],
                       capture_output=True, text=True, env=ENV)
    if check and r.returncode:
        raise RuntimeError(f"git {args} rc={r.returncode}: {r.stderr}")
    return r.stdout.strip()


def mklab(name, lfs=True, extra_commit=True):
    """(src, node, base, tip): src has base+tip; node sits at base with an
    EMPTY lfs store and no remote to download from (the field case: lane
    commits are never pushed)."""
    root = LAB / name
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    src, node = root / "src", root / "node"
    subprocess.run(["git", "init", "-q", str(src)], check=True, env=ENV)
    if lfs:
        git(src, "lfs", "install", "--local")
        (src / ".gitattributes").write_text("*.bin filter=lfs diff=lfs merge=lfs -text\n")
    (src / "plain.txt").write_text("hello\n")
    git(src, "add", "-A"); git(src, "commit", "-qm", "base")
    base = git(src, "rev-parse", "HEAD")
    if extra_commit:
        if lfs:
            (src / "big.bin").write_bytes(os.urandom(200000))
        (src / "new.txt").write_text("new-in-target\n")
        (src / "plain.txt").write_text("hello again\n")
        git(src, "add", "-A"); git(src, "commit", "-qm", "tip")
    tip = git(src, "rev-parse", "HEAD")
    subprocess.run(["git", "clone", "-q", str(src), str(node)], check=True,
                   env=dict(ENV, GIT_LFS_SKIP_SMUDGE="1"))
    git(node, "checkout", "-q", "-B", "main", base)
    shutil.rmtree(node / ".git" / "lfs" / "objects", ignore_errors=True)
    git(node, "remote", "remove", "origin")
    return src, node, base, tip


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


def expect(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ---------------------------------------------------------------------------
@case("helpers: ls-files parse / store path / smudge markers")
def t_helpers():
    C = LocalClient()
    oid = "a" * 64
    rows = C._parse_lfs_ls_files(
        f"{oid} * ork.data/tex/a b.png\n{'b'*64} - x.bin\ngarbage line\n")
    expect(rows == [(oid, "*", "ork.data/tex/a b.png"), ("b" * 64, "-", "x.bin")],
           f"parse -> {rows}")
    expect(C._lfs_store_relpath(oid) == f"aa/aa/{oid}", "store relpath")
    expect(C._smudge_failure("") == "", "clean stderr")
    expect("smudge filter lfs failed" in C._smudge_failure(
        "Downloading x\nfatal: big.bin: smudge filter lfs failed\n"), "fatal caught")
    expect(C._smudge_failure("error: external filter 'git-lfs filter-process' failed"),
           "external filter caught")
    expect(list(C._chunks(range(5), 2)) == [[0, 1], [2, 3], [4]], "chunks")


# ---------------------------------------------------------------------------
@case("1. LFS objects travel: node lacking the object checks out clean")
def t_lfs_travel():
    src, node, base, tip = mklab("lfs")
    C = LocalClient()
    r = C.gitsync("testnode", str(src), str(node))
    expect(r["lfs_objects"] == 1, f"staged objects: {r}")
    expect(git(node, "rev-parse", "HEAD") == tip, "node HEAD")
    expect((node / "big.bin").read_bytes() == (src / "big.bin").read_bytes(),
           "big.bin is REAL content on the node")
    expect(git(node, "status", "--porcelain") == "", "clean tree")
    expect(r["action"].startswith("fast-forwarded"), r["action"])
    expect("LFS object" in r["action"], f"action names the LFS work: {r['action']}")


@case("1b. idempotent: re-run moves 0 objects, 0 bytes")
def t_idem():
    src, node, base, tip = mklab("idem")
    C = LocalClient()
    C.gitsync("testnode", str(src), str(node))
    r2 = C.gitsync("testnode", str(src), str(node))
    expect(r2["action"] == "already-aligned", f"second run: {r2}")
    # and a NEW commit that adds no LFS content stages nothing
    (src / "plain.txt").write_text("third\n")
    git(src, "commit", "-qam", "no new lfs")
    r3 = C.gitsync("testnode", str(src), str(node))
    expect(r3["lfs_objects"] == 0 and r3.get("lfs_needed") == 1,
           f"no new objects: {r3}")


@case("1c. no LFS in the repo: clean no-op, no pointer scan")
def t_nolfs():
    src, node, base, tip = mklab("nolfs", lfs=False)
    C = LocalClient()
    r = C.gitsync("testnode", str(src), str(node))
    expect(r["lfs_objects"] == 0 and r["lfs_needed"] == 0, f"no-op: {r}")
    expect(git(node, "rev-parse", "HEAD") == tip, "node HEAD")


@case("1d. object missing on BOTH sides: reported, then the failure is loud")
def t_absent_locally():
    src, node, base, tip = mklab("absent")
    shutil.rmtree(src / ".git" / "lfs" / "objects")     # controller lost it too
    C = LocalClient()
    try:
        r = C.gitsync("testnode", str(src), str(node))
        raise AssertionError(f"expected a loud failure, got {r}")
    except RuntimeError as e:
        expect("SMUDGE" in str(e).upper(), f"message names the smudge: {e}")
    expect(git(node, "rev-parse", "HEAD") == base, "node HEAD unmoved")


# ---------------------------------------------------------------------------
@case("2. aborted-checkout debris is cleared (own content), retry succeeds")
def t_debris():
    src, node, base, tip = mklab("debris")
    C = LocalClient()
    # exactly what an aborted checkout leaves: new-in-target files already
    # written, HEAD still at base, LFS object still missing
    shutil.copyfile(src / "new.txt", node / "new.txt")
    shutil.copyfile(src / "big.bin", node / "big.bin")   # materialized asset
    expect("new.txt" in git(node, "status", "--porcelain"), "debris is untracked")
    r = C.gitsync("testnode", str(src), str(node))
    expect(sorted(r.get("cleared_debris", [])) == ["big.bin", "new.txt"],
           f"debris classified as ours: {r.get('cleared_debris')}")
    expect(git(node, "rev-parse", "HEAD") == tip, "node HEAD")
    expect(git(node, "status", "--porcelain") == "", "clean tree")


@case("2b. debris that is an LFS POINTER (skip-smudge residue) is ours too")
def t_debris_pointer():
    src, node, base, tip = mklab("debrisptr")
    C = LocalClient()
    ptr = subprocess.run(["git", "-C", str(src), "cat-file", "-p", f"{tip}:big.bin"],
                         capture_output=True, env=ENV).stdout
    (node / "big.bin").write_bytes(ptr)
    (node / "new.txt").write_text("new-in-target\n")
    r = C.gitsync("testnode", str(src), str(node))
    expect("big.bin" in r.get("cleared_debris", []),
           f"pointer debris classified as ours: {r}")
    expect((node / "big.bin").read_bytes() == (src / "big.bin").read_bytes(),
           "pointer replaced by real content")


@case("2c. FOREIGN untracked collision keeps the loud refusal, changes nothing")
def t_foreign():
    src, node, base, tip = mklab("foreign")
    C = LocalClient()
    (node / "new.txt").write_text("SOMEBODY ELSE'S WORK\n")
    try:
        r = C.gitsync("testnode", str(src), str(node))
        raise AssertionError(f"expected refusal, got {r}")
    except RuntimeError as e:
        expect("new.txt" in str(e) and "NOT ours" in str(e), f"message: {e}")
    expect(git(node, "rev-parse", "HEAD") == base, "node HEAD unmoved")
    expect((node / "new.txt").read_text() == "SOMEBODY ELSE'S WORK\n",
           "foreign file untouched")


@case("2d. restricted node (git-only argv) still proves debris ownership")
def t_debris_restricted():
    src, node, base, tip = mklab("restricted")
    C = LocalClient(restricted=True)
    shutil.copyfile(src / "new.txt", node / "new.txt")
    r = C.gitsync("testnode", str(src), str(node))
    expect(r.get("cleared_debris") == ["new.txt"], f"cleared: {r}")
    expect(all(a[0] == "git" for a in C.run_log),
           f"non-git argv on a restricted node: "
           f"{[a[0] for a in C.run_log if a[0] != 'git']}")


@case("2e. debris with glob/space/non-ASCII names classifies correctly")
def t_debris_weird_names():
    src, node, base, tip = mklab("weird")
    nasty = ["tex [lod2]#1.png", "a file with spaces.txt", "kaffé_ø.txt"]
    for n in nasty:
        (src / n).write_text(f"content of {n}\n")
    git(src, "add", "-A"); git(src, "commit", "-qm", "nasty names")
    tip = git(src, "rev-parse", "HEAD")
    C = LocalClient()
    for n in nasty:
        shutil.copyfile(src / n, node / n)             # aborted-checkout debris
    (node / "new.txt").write_text("SOMEBODY ELSE'S WORK\n")   # ...and one foreign
    try:
        C.gitsync("testnode", str(src), str(node))
        raise AssertionError("expected the foreign refusal")
    except RuntimeError as e:
        expect("new.txt" in str(e) and "NOT ours" in str(e), f"message: {e}")
        for n in nasty:
            expect(n not in str(e), f"{n} misclassified as foreign: {e}")
    (node / "new.txt").unlink()
    r = C.gitsync("testnode", str(src), str(node))
    expect(sorted(r.get("cleared_debris", [])) == sorted(nasty),
           f"cleared: {r.get('cleared_debris')}")
    expect(git(node, "rev-parse", "HEAD") == tip, "node HEAD")


# ---------------------------------------------------------------------------
@case("3. rc lie: smudge fails with rc=0 (filter not required) -> loud FAIL")
def t_rc_lie():
    src, node, base, tip = mklab("rclie")
    git(node, "config", "filter.lfs.required", "false")
    C = LocalClient()
    # prove the lie exists first: raw checkout, no staging
    raw = subprocess.run(["git", "-C", str(node), "checkout", "-q", "-B", "main", tip],
                         capture_output=True, text=True, env=ENV)
    stub = (node / "big.bin").read_bytes()[:40] if (node / "big.bin").exists() else b"<absent>"
    print(f"   RAW CHECKOUT rc={raw.returncode} head={git(node,'rev-parse','HEAD')[:12]} "
          f"big.bin={stub!r}\n   stderr={raw.stderr.strip()[:160]!r}")
    expect(raw.returncode == 0, "the rc lie must reproduce (rc=0 over a failed smudge)")
    git(node, "reset", "-q", "--hard", base)
    subprocess.run(["git", "-C", str(node), "clean", "-qfd"], env=ENV)
    git(node, "checkout", "-q", "-B", "main", base)
    try:
        r = C.gitsync("testnode", str(src), str(node), lfs=False)  # no staging
        raise AssertionError(f"smudge failure passed as success: {r}")
    except RuntimeError as e:
        expect("smudge" in str(e).lower() or "POINTER" in str(e),
               f"verdict names the smudge: {e}")


@case("3b. pointer scan catches a silent pointer left in the tree")
def t_pointer_scan():
    src, node, base, tip = mklab("ptrscan")
    C = LocalClient()

    class SkipSmudge(type(C)):
        """A node whose checkout quietly writes pointers (skip-smudge) — rc=0,
        clean stderr, HEAD correct, asset a text stub."""
        def run(self, node_, argv, **kw):
            argv = [str(a) for a in argv]
            if "checkout" in argv:
                kw = dict(kw)
                r = subprocess.run(argv, capture_output=True, text=True,
                                   env=dict(ENV, GIT_LFS_SKIP_SMUDGE="1"))
                return {"ok": True, "rc": r.returncode, "stdout": r.stdout,
                        "stderr": r.stderr}
            return super().run(node_, argv, **kw)

    C2 = SkipSmudge()
    try:
        r = C2.gitsync("testnode", str(src), str(node), lfs=False)
        raise AssertionError(f"silent pointer passed as success: {r}")
    except RuntimeError as e:
        expect("POINTER" in str(e) and "big.bin" in str(e), f"verdict: {e}")


@case("3d. already-aligned tree with stub assets is NOT called clean")
def t_aligned_stubs():
    src, node, base, tip = mklab("alignedstub")
    # the state an rc-lying checkout leaves: ref at target, asset a stub
    subprocess.run(["git", "-C", str(node), "fetch", "-q", str(src), tip],
                   check=True, env=ENV)
    subprocess.run(["git", "-C", str(node), "checkout", "-q", "-f", "-B", "main", tip],
                   env=dict(ENV, GIT_LFS_SKIP_SMUDGE="1"), check=True)
    C = LocalClient()
    r = C.gitsync("testnode", str(src), str(node))
    expect(r["action"].startswith("already-aligned"), r["action"])
    expect("big.bin" in str(r.get("lfs_pointers")), f"stub reported: {r}")
    expect("WARNING" in r["action"], f"verdict line carries it: {r['action']}")


@case("3e. detached local HEAD is refused before the node is touched")
def t_detached():
    src, node, base, tip = mklab("detached")
    git(src, "checkout", "-q", "--detach", tip)
    C = LocalClient()
    try:
        r = C.gitsync("testnode", str(src), str(node))
        raise AssertionError(f"expected the detached-HEAD refusal, got {r}")
    except RuntimeError as e:
        expect("DETACHED" in str(e) and "branch" in str(e), f"message: {e}")
        expect("not a valid branch name" not in str(e), "git's confusing fatal leaked")
    expect(git(node, "rev-parse", "HEAD") == base, "node HEAD unmoved")
    expect(not (node / ".git" / "obtnet-gitsync").exists(), "nothing staged on the node")
    expect(not any("checkout" in a for a in C.run_log),
           f"node was touched: {C.run_log}")


@case("4. seed guard: an oversized staging is refused with the seed recipe")
def t_seed_guard():
    src, node, base, tip = mklab("seed")
    C = LocalClient()
    try:
        r = C.gitsync("testnode", str(src), str(node), lfs_max_bytes=1000)
        raise AssertionError(f"expected the seed refusal, got {r}")
    except RuntimeError as e:
        expect("store SEED" in str(e) and "--lfs-max-mb" in str(e), f"message: {e}")
        expect("obt.net.py sync" in str(e), "message hands over the seed recipe")
    expect(git(node, "rev-parse", "HEAD") == base, "node HEAD unmoved")


@case("4b. local repo is a LINKED WORKTREE: store resolves to the common dir")
def t_worktree():
    src, node, base, tip = mklab("worktree")
    wt = src.parent / "wt"
    git(src, "worktree", "add", "-q", "-b", "lane", str(wt), tip)
    C = LocalClient()
    r = C.gitsync("testnode", str(wt), str(node))
    expect(r["lfs_objects"] == 1, f"staged from the common-dir store: {r}")
    expect((node / "big.bin").read_bytes() == (src / "big.bin").read_bytes(),
           "real content on the node")


@case("4c. CLI flags reach the verb (--no-lfs / --lfs-max-mb)")
def t_cli_flags():
    src, node, base, tip = mklab("cliflags")
    import obt.net.client as nc
    calls = []

    class Spy(LocalClient):
        def gitsync(self, *a, **k):
            calls.append(k)
            return {"action": "noop", "local": "x", "remote": "y", "ok": True}

    real = nc.Client
    try:
        nc.Client = lambda *a, **k: Spy()
        nc.main(["gitsync", "testnode", str(src), str(node)])
        nc.main(["gitsync", "testnode", str(src), str(node),
                 "--no-lfs", "--lfs-max-mb", "7"])
    finally:
        nc.Client = real
    expect(calls[0]["lfs"] is True and calls[0]["lfs_max_bytes"] == 1024000000,
           f"defaults: {calls[0]}")
    expect(calls[1]["lfs"] is False and calls[1]["lfs_max_bytes"] == 7000000,
           f"flags: {calls[1]}")


@case("5. gitbootstrap creates a new branch-identical clone with real LFS data")
def t_bootstrap():
    src, old_node, base, tip = mklab("bootstrap")
    node = src.parent / "fresh"
    C = LocalClient()
    r = C.gitbootstrap("testnode", str(src), str(node))
    expect(r["action"] == "bootstrapped", f"result: {r}")
    expect(git(node, "rev-parse", "HEAD") == tip, "node HEAD")
    expect(git(node, "branch", "--show-current") ==
           git(src, "branch", "--show-current"), "node branch")
    expect((node / "big.bin").read_bytes() == (src / "big.bin").read_bytes(),
           "bootstrap materialized LFS content")
    expect(git(node, "status", "--porcelain") == "", "clean clone")


@case("5b. gitbootstrap refuses an existing repository")
def t_bootstrap_existing():
    src, node, base, tip = mklab("bootstrap-existing")
    C = LocalClient()
    try:
        C.gitbootstrap("testnode", str(src), str(node))
        raise AssertionError("expected existing-destination refusal")
    except RuntimeError as e:
        expect("already a Git repository" in str(e), f"message: {e}")


@case("5c. gitbootstrap refuses uncommitted source content")
def t_bootstrap_dirty_source():
    src, old_node, base, tip = mklab("bootstrap-dirty")
    node = src.parent / "fresh"
    (src / "not-committed.txt").write_text("required but absent from HEAD\n")
    C = LocalClient()
    try:
        C.gitbootstrap("testnode", str(src), str(node))
        raise AssertionError("expected dirty-source refusal")
    except RuntimeError as e:
        expect("uncommitted content" in str(e), f"message: {e}")
    expect(not node.exists(), "destination was not touched")


@case("5d. gitbootstrap resumes an interrupted same-commit LFS checkout")
def t_bootstrap_resume():
    src, old_node, base, tip = mklab("bootstrap-resume")
    node = src.parent / "fresh"
    C = LocalClient()
    C.gitbootstrap("testnode", str(src), str(node))
    pointer = subprocess.check_output(
        ["git", "-C", str(node), "show", "HEAD:big.bin"], env=ENV)
    (node / "big.bin").write_bytes(pointer)
    shutil.rmtree(node / ".git" / "lfs" / "objects", ignore_errors=True)
    r = C.gitbootstrap("testnode", str(src), str(node))
    expect(r["action"] == "resumed-bootstrap", f"result: {r}")
    expect((node / "big.bin").read_bytes() == (src / "big.bin").read_bytes(),
           "resume restored LFS content")


@case("5e. bootstrap creates an origin-less replica and preserves a configured origin")
def t_bootstrap_origin():
    src, old_node, base, tip = mklab("bootstrap-origin", lfs=False)
    node = src.parent / "fresh"
    C = LocalClient()
    C.gitbootstrap("testnode", str(src), str(node), lfs=False)
    expect(git(node, "remote") == "", "temporary origin removed")
    git(node, "remote", "add", "origin", str(src))
    C.gitbootstrap("testnode", str(src), str(node), lfs=False)
    expect(git(node, "remote", "get-url", "origin") == str(src), "explicit durable origin preserved")
    git(node, "fetch", "origin")
    token = netclient.hashlib.sha256((str(node) + tip).encode()).hexdigest()[:16]
    git(node, "remote", "set-url", "origin", f"{node}.obtnet-bootstrap-{token}")
    C.gitbootstrap("testnode", str(src), str(node), lfs=False)
    expect(git(node, "remote") == "", "old bootstrap's dangling origin repaired")


@case("5f. bootstrap refuses changed destination content without modifying it")
def t_bootstrap_dirty_destination():
    for kind in ("tracked", "staged", "untracked", "lfs", "deleted"):
        src, old_node, base, tip = mklab("bootstrap-dest-" + kind)
        node = src.parent / "fresh"
        C = LocalClient()
        C.gitbootstrap("testnode", str(src), str(node))
        path = node / ("new.txt" if kind == "untracked" else
                       "big.bin" if kind == "lfs" else "plain.txt")
        if kind == "deleted":
            path.unlink()
        else:
            path.write_text("unrelated destination edits\n")
        if kind == "staged":
            git(node, "add", "plain.txt")
        before = git(node, "status", "--porcelain=v1", "--untracked-files=all")
        for dry in (True, False):
            try:
                C.gitbootstrap("testnode", str(src), str(node), dry=dry)
                raise AssertionError(f"expected dirty destination refusal: {kind}")
            except RuntimeError as e:
                expect("destination" in str(e) and "uncommitted" in str(e), str(e))
            expect(git(node, "status", "--porcelain=v1", "--untracked-files=all") == before,
                   "destination index and worktree unchanged")
            expect(not path.exists() if kind == "deleted" else
                   path.read_text() == "unrelated destination edits\n", "user data preserved")


@case("5g. canonical LFS pointer does not excuse destination mode changes")
def t_bootstrap_pointer_mode():
    if os.name == "nt":
        return  # executable bits are not tracked on Windows
    src, old_node, base, tip = mklab("bootstrap-pointer-mode")
    node = src.parent / "fresh"
    C = LocalClient()
    C.gitbootstrap("testnode", str(src), str(node))
    pointer = subprocess.check_output(["git", "-C", str(node), "show", "HEAD:big.bin"], env=ENV)
    path = node / "big.bin"
    path.write_bytes(pointer)
    path.chmod(0o755)
    try:
        C.gitbootstrap("testnode", str(src), str(node))
        raise AssertionError("expected mode-change refusal")
    except RuntimeError as e:
        expect("uncommitted" in str(e), str(e))
    expect(path.read_bytes() == pointer and path.stat().st_mode & 0o111,
           "pointer and user mode change preserved")


@case("3c. every gitsync CLI failure ends in a [obtnet] FAIL line")
def t_cli_verdict():
    src, node, base, tip = mklab("cliverdict")
    import obt.net.client as nc
    seen = []
    real = nc._verdict
    nc._verdict = lambda ok, *a, **k: (seen.append((ok, a)), real(ok, *a, **k))[0]

    class Boom(LocalClient):
        def run(self, *a, **k):
            raise ZeroDivisionError("a failure type nobody enumerated")

    try:
        nc.Client = lambda *a, **k: Boom()
        rc = nc.main(["gitsync", "testnode", str(src), str(node)])
    finally:
        nc._verdict = real
    expect(rc == 1, f"rc={rc}")
    expect(seen and seen[-1][0] is False, f"verdict lines: {seen}")


def main():
    if subprocess.run(["git", "lfs", "version"], capture_output=True).returncode:
        print("SKIP: git-lfs is not on PATH (this gate is about LFS transport)")
        return 0
    shutil.rmtree(LAB, ignore_errors=True)
    LAB.mkdir(parents=True, exist_ok=True)
    # Clones do not inherit the source repo's local LFS filter config. Give
    # every fixture a private global config instead of relying on the user's
    # git-lfs installation (system config is disabled by ENV above).
    ENV["GIT_CONFIG_GLOBAL"] = str(LAB / "gitconfig")
    subprocess.run(["git", "lfs", "install", "--skip-repo"], env=ENV,
                   cwd=LAB, check=True, capture_output=True)
    before = {p for d in ("pushlog", "treecache")
              for p in (Path.home() / ".obtnet" / d).glob("*")}
    for name, fn in CASES:
        try:
            fn()
            RESULTS.append((True, name, ""))
            print(f"PASS {name}")
        except Exception as e:
            RESULTS.append((False, name, str(e)))
            print(f"FAIL {name}: {e}")
            traceback.print_exc()
    ok = sum(1 for r in RESULTS if r[0])
    print(f"\n{ok}/{len(RESULTS)} cases pass")
    # drop the pushlog/treecache entries this gate created (scratch paths only)
    for d in ("pushlog", "treecache"):
        for p in (Path.home() / ".obtnet" / d).glob("*"):
            if p not in before:
                p.unlink(missing_ok=True)
    if ok == len(RESULTS):
        shutil.rmtree(LAB, ignore_errors=True)     # keep the lab on failure
        return 0
    print(f"(scratch repos kept for inspection: {LAB})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
