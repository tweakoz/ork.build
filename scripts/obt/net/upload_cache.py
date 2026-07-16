"""obt.net.upload_cache — content-addressed blob store for obtnet nodes.

Blobs live at <root>/<sha256> with a small .json sidecar. Dedup by sha:
upload_query short-circuits re-sends. Lifted (design) from the Z64 server's
UploadCache; generalized paths, no domain assumptions.
"""

import hashlib
import json
import os
from pathlib import Path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class UploadCache:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, sha: str) -> Path:
        if len(sha) != 64 or not all(c in "0123456789abcdef" for c in sha.lower()):
            raise ValueError(f"bad sha256: {sha!r}")
        return self.root / sha.lower()

    def has(self, sha: str) -> bool:
        return self.path_for(sha).exists()

    def put(self, data: bytes, tag: str = "") -> str:
        sha = sha256_hex(data)
        p = self.path_for(sha)
        if not p.exists():
            tmp = p.with_suffix(".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, p)  # atomic publish
            p.with_suffix(".json").write_text(
                json.dumps({"sha256": sha, "bytes": len(data), "tag": tag}))
        return sha

    def get(self, sha: str) -> bytes:
        return self.path_for(sha).read_bytes()

    def materialize(self, sha: str, dest: Path) -> Path:
        """Copy a cached blob to dest (for run_command inputs)."""
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.get(sha))
        return dest
