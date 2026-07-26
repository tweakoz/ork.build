#!/usr/bin/env python3
"""obt.net.msg.deposit — recipient-side message writer for the obtnet
coordinator-messaging pilot.

A message is ONE markdown file in the recipient's inbox PLUS one metadata line
appended to a persistent stream file (the LLM-side wake target). This tool is
SELF-CONTAINED (stdlib only) so it runs identically whether invoked by an
obtnet node job (argv, direct exec — no shell) or over a bare ssh remote command
(stdin-json — zero shell interpolation). It never depends on the `obt` package
being importable, so plain system python3 on any host can run it.

Payload transport is ALWAYS base64 (args mode) or a JSON blob on stdin (ssh
mode) — arbitrary message content is NEVER shell-interpolated.

Layout (under --inbox-root, default ~/coordination):
  inbox/<utc-ts>__from-<sender>__<slug>.md    frontmatter(from,subject,ts)+body
  inbox/acked/                                  ack destination (created here)
  inbox.stream                                  <ts>\t<from>\t<subject>\t<path>

Writes are atomic: the .md is written to a temp file in the same dir and
os.replace()'d into place; the stream line is a single append AFTER the file
lands (a monitor tailing the stream never sees a line before its file exists).
"""

import argparse
import base64
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path


def _slugify(text, maxlen=48, default="msg"):
    s = re.sub(r"[^A-Za-z0-9]+", "-", (text or "").strip().lower()).strip("-")
    s = s[:maxlen].strip("-")
    return s or default


def _one_line(text):
    """Collapse to a single line — for the TSV stream field and YAML scalar."""
    return re.sub(r"\s+", " ", (text or "").replace("\t", " ")).strip()


def _utc_ts():
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def deposit(sender, subject, payload, ts=None, slug=None, inbox_root=None):
    sender = _one_line(sender) or "unknown"
    subject_full = _one_line(subject)
    ts = ts or _utc_ts()
    slug = _slugify(slug or subject_full)
    root = Path(inbox_root) if inbox_root else (Path.home() / "coordination")
    inbox = root / "inbox"
    acked = inbox / "acked"
    inbox.mkdir(parents=True, exist_ok=True)
    acked.mkdir(parents=True, exist_ok=True)

    sender_fn = _slugify(sender, default="unknown")
    base = f"{ts}__from-{sender_fn}__{slug}"
    dest = inbox / f"{base}.md"
    n = 2
    while dest.exists():                       # same-second collision guard
        dest = inbox / f"{base}-{n}.md"
        n += 1

    body = (f"---\n"
            f"from: {sender}\n"
            f"subject: {subject_full}\n"
            f"ts: {ts}\n"
            f"---\n"
            f"{payload}")
    if not body.endswith("\n"):
        body += "\n"

    fd, tmp = tempfile.mkstemp(prefix=".obtnet_msg_", dir=str(inbox))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(body)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dest)                   # atomic publish
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    stream = root / "inbox.stream"
    line = f"{ts}\t{sender}\t{subject_full}\t{dest}\n"
    with open(stream, "a", encoding="utf-8") as sf:   # append AFTER the file lands
        sf.write(line)
        sf.flush()
        os.fsync(sf.fileno())

    return {"ok": True, "path": str(dest), "stream": str(stream), "ts": ts,
            "from": sender, "subject": subject_full}


def main(argv=None):
    ap = argparse.ArgumentParser(description="obtnet message deposit (recipient side)")
    ap.add_argument("--from", dest="sender", default=None)
    ap.add_argument("--subject", default=None)
    ap.add_argument("--ts", default=None)
    ap.add_argument("--slug", default=None)
    ap.add_argument("--payload-b64", default=None,
                    help="message body as base64 (args mode; safe under direct exec)")
    ap.add_argument("--stdin-json", action="store_true",
                    help="read {from,subject,ts,slug,payload_b64} as JSON on stdin "
                         "(ssh mode; zero shell interpolation)")
    ap.add_argument("--inbox-root", default=None,
                    help="override coordination root (default ~/coordination)")
    args = ap.parse_args(argv)

    if args.stdin_json:
        try:
            blob = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        except Exception as e:
            print(json.dumps({"ok": False, "error": f"bad stdin-json: {e}"}))
            return 2
        sender = blob.get("from")
        subject = blob.get("subject")
        ts = blob.get("ts")
        slug = blob.get("slug")
        payload_b64 = blob.get("payload_b64") or ""
        inbox_root = blob.get("inbox_root") or args.inbox_root
    else:
        sender = args.sender
        subject = args.subject
        ts = args.ts
        slug = args.slug
        payload_b64 = args.payload_b64 or ""
        inbox_root = args.inbox_root

    if not subject:
        print(json.dumps({"ok": False, "error": "missing --subject"}))
        return 2
    try:
        payload = base64.b64decode(payload_b64).decode("utf-8", errors="replace")
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"bad payload-b64: {e}"}))
        return 2

    try:
        res = deposit(sender, subject, payload, ts=ts, slug=slug, inbox_root=inbox_root)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"deposit failed: {e}"}))
        return 1
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
