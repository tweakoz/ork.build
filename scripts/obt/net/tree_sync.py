"""obt.net.tree_sync — manifest machinery for the sync verb (git-free
working-tree transport between machines — code AND data, no commits
required).

A tree manifest maps relpath -> entry:
  file:    {"t": "f", "sha256": ..., "size": ..., "mode": 0o755}
  symlink: {"t": "l", "target": "..."}
Directories are implicit (created on materialize); empty dirs don't sync
(same stance as git). Sockets/fifos are skipped. Walks never follow
symlinked dirs (a link to a dir is recorded as a link).

Determinism: manifests are plain dicts; tree_hash() hashes the sorted
serialization — two trees with equal content yield the same hash on any
OS/arch, which is how a sync proves itself in one verdict token.

Hash cache: hashing multi-GB data trees every sync is the slow part, so
shas are cached per absolute root under ~/.obtnet/treecache keyed by
(size, mtime_ns); only touched files re-hash on repeat syncs.
"""

import fnmatch
import hashlib
import json
import os
from pathlib import Path

# always-excluded names/patterns (matched against each path COMPONENT and the
# relpath): VCS innards, editor/OS litter, python bytecode, and `.build` —
# obt's own in-tree build-dir convention (never sync object files across
# machines/arches; 3000+ .o entries buried the first real orkid diff).
DEFAULT_EXCLUDES = [".git", ".svn", "__pycache__", "*.pyc", ".DS_Store",
                    ".build", ".obtnet_tmp*"]


def _excluded(relpath, excludes):
    parts = relpath.split("/")
    for pat in excludes:
        if fnmatch.fnmatch(relpath, pat):
            return True
        for comp in parts:
            if fnmatch.fnmatch(comp, pat):
                return True
    return False


def _sha256_file(p, bufsize=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


class _HashCache:
    """(relpath, size, mtime_ns) -> sha256, persisted per tree root."""

    def __init__(self, root: Path):
        key = hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()[:16]
        self.path = Path.home() / ".obtnet" / "treecache" / f"{key}.json"
        try:
            self.data = json.loads(self.path.read_text())
        except Exception:
            self.data = {}
        self.dirty = False

    def get(self, rel, size, mtime_ns):
        e = self.data.get(rel)
        if e and e[0] == size and e[1] == mtime_ns:
            return e[2]
        return None

    def put(self, rel, size, mtime_ns, sha):
        self.data[rel] = [size, mtime_ns, sha]
        self.dirty = True

    def save(self):
        if not self.dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data))
        os.replace(tmp, self.path)


def build_manifest(root, excludes=None):
    """Walk root -> manifest dict. Missing root -> empty manifest (a sync
    into a fresh machine starts from nothing)."""
    root = Path(root)
    excludes = list(DEFAULT_EXCLUDES) + list(excludes or [])
    manifest = {}
    if not root.exists():
        return manifest
    cache = _HashCache(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = os.path.relpath(dirpath, root)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")
        # prune excluded dirs in place (never descend)
        dirnames[:] = [d for d in sorted(dirnames)
                       if not _excluded((rel_dir + "/" + d).lstrip("/"), excludes)]
        # symlinked dirs appear in dirnames with followlinks=False? no — they
        # appear in dirnames but aren't descended; record them as links:
        for d in list(dirnames):
            full = os.path.join(dirpath, d)
            if os.path.islink(full):
                rel = (rel_dir + "/" + d).lstrip("/")
                manifest[rel] = {"t": "l", "target": os.readlink(full)}
                dirnames.remove(d)
        for fn in sorted(filenames):
            rel = (rel_dir + "/" + fn).lstrip("/")
            if _excluded(rel, excludes):
                continue
            full = os.path.join(dirpath, fn)
            try:
                st = os.lstat(full)
            except OSError:
                continue
            import stat as _stat
            if _stat.S_ISLNK(st.st_mode):
                manifest[rel] = {"t": "l", "target": os.readlink(full)}
                continue
            if not _stat.S_ISREG(st.st_mode):
                continue                        # sockets/fifos/devices
            sha = cache.get(rel, st.st_size, st.st_mtime_ns)
            if sha is None:
                sha = _sha256_file(full)
                cache.put(rel, st.st_size, st.st_mtime_ns, sha)
            # git's stance on modes: only the exec bit is content; everything
            # else is local umask convention (mac 644 vs ubuntu 664 would
            # otherwise make EVERY file "differ" across machines)
            mode = 0o755 if (st.st_mode & 0o100) else 0o644
            manifest[rel] = {"t": "f", "sha256": sha, "size": st.st_size,
                             "mode": mode}
    cache.save()
    return manifest


def tree_hash(manifest):
    """Deterministic hash of a manifest — equal trees, equal hash, any OS."""
    ser = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(ser.encode()).hexdigest()


def diff_manifests(src, dst):
    """What must change so dst == src.
    Returns (to_send, to_link, to_delete): file relpaths whose blobs dst
    needs, symlinks to (re)create, and dst-only paths."""
    to_send, to_link = [], []
    for rel, e in src.items():
        d = dst.get(rel)
        if e["t"] == "f":
            if d is None or d.get("t") != "f" or d.get("sha256") != e["sha256"] \
               or d.get("mode") != e["mode"]:
                to_send.append(rel)
        else:  # symlink
            if d is None or d.get("t") != "l" or d.get("target") != e["target"]:
                to_link.append(rel)
    to_delete = [rel for rel in dst if rel not in src]
    return to_send, to_link, to_delete


def classify_diff(local, remote):
    """Symmetric A/B classification for the diff verb:
    '+' local-only, '-' remote-only, 'M' content/exec differs, 'L' link
    target or file-vs-link type differs. Returns sorted (tag, relpath)."""
    out = []
    for rel in sorted(set(local) | set(remote)):
        a, b = local.get(rel), remote.get(rel)
        if b is None:
            out.append(("+", rel))
        elif a is None:
            out.append(("-", rel))
        elif a["t"] != b["t"]:
            out.append(("L", rel))
        elif a["t"] == "l":
            if a["target"] != b["target"]:
                out.append(("L", rel))
        elif a["sha256"] != b["sha256"] or a["mode"] != b["mode"]:
            out.append(("M", rel))
    return out


def safe_relpath(rel):
    """Reject traversal — every path a peer hands us must stay inside root."""
    if rel.startswith("/") or rel.startswith("~"):
        return False
    parts = rel.split("/")
    return ".." not in parts and all(p not in ("", ".") for p in parts)


def materialize_tree(root, entries, blob_reader, deletes=()):
    """Apply manifest entries into root. blob_reader(sha) -> bytes source for
    files (already sha-verified by the transport). tmp+rename per file — a
    killed sync never leaves a truncated file, only missing updates.
    Returns (n_files, n_links, n_deleted)."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    nf = nl = nd = 0
    for rel, e in entries.items():
        if not safe_relpath(rel):
            raise ValueError(f"unsafe relpath {rel!r}")
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if e["t"] == "l":
            if dest.is_symlink() or dest.exists():
                _rm(dest)
            os.symlink(e["target"], dest)
            nl += 1
        else:
            tmp = dest.parent / (".obtnet_tmp." + dest.name)
            with open(tmp, "wb") as f:
                f.write(blob_reader(e["sha256"]))
            os.chmod(tmp, e["mode"])
            os.replace(tmp, dest)
            nf += 1
    for rel in deletes:
        if not safe_relpath(rel):
            raise ValueError(f"unsafe delete relpath {rel!r}")
        p = root / rel
        if p.is_symlink() or p.exists():
            _rm(p)
            nd += 1
            d = p.parent            # prune now-empty dirs up to root
            while d != root:
                try:
                    d.rmdir()
                except OSError:
                    break
                d = d.parent
    return nf, nl, nd


def _rm(p):
    import shutil
    if p.is_symlink() or p.is_file():
        p.unlink()
    elif p.is_dir():
        shutil.rmtree(p)
