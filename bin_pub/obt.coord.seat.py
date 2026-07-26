#!/usr/bin/env python3
"""obt.coord.seat — bootstrap, validate, and scaffold an obtnet coordinator seat.

The whole coordinator-messaging system is redeployable from ork.build on any box:
this tool scaffolds ~/coordination/, wires the seat's identity into the obt global
config, and emits canonical taskset folders. Stdlib only; every path derives from
$HOME at call time, so tests can point HOME at a scratch dir and everything
relocates. Each subcommand ends with one greppable verdict: `[obtcoord] ok|FAIL ...`.

  init --seat <name> [--master <addr>] [--role sub|master]
        idempotently scaffold the seat; merge coordid (+controller for subs) into
        ~/.obt-global/obtnet.json; master ensures ACTIVE_TASKSET; prints next steps.
  check [--seat <name>]
        porcelain PASS/FAIL per check; best-effort node-registration probe.
  taskset new <path>
        emit the canonical taskset skeleton (TASKSET FORMAT v1).
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEPOSIT_TOOL = "obt.net.msg.deposit.py"


# -- paths (evaluated per-call so a HOME override relocates everything) --------
def _home():
    return Path(os.environ.get("HOME") or Path.home())


def _coord_root():
    return _home() / "coordination"


def _config_path():
    return _home() / ".obt-global" / "obtnet.json"


def _verdict(ok, verb, rest=""):
    print(f"[obtcoord] {'ok' if ok else 'FAIL'} {verb} {rest}".rstrip())


def _load_config():
    try:
        return json.loads(_config_path().read_text())
    except Exception:
        return {}


def _save_config(cfg):
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=1) + "\n")
    os.replace(tmp, p)


def _normalize_addr(addr):
    """tcp://host:7461 from lazy forms ('host', 'host:7461', 'tcp://host')."""
    if not addr:
        return addr
    addr = addr.strip()
    if "://" not in addr:
        addr = "tcp://" + addr
    scheme, rest = addr.split("://", 1)
    if ":" not in rest:
        rest = rest + ":7461"
    return f"{scheme}://{rest}"


def _find_deposit_tool():
    """Prefer the INSTALLED bin (on PATH), fall back to a sibling of this script."""
    w = shutil.which(DEPOSIT_TOOL)
    cands = ([Path(w)] if w else []) + [Path(__file__).resolve().parent / DEPOSIT_TOOL]
    for c in cands:
        if c and c.is_file():
            return c
    return None


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------
def cmd_init(args):
    seat, role = args.seat, args.role
    root = _coord_root()
    for d in (root / "inbox" / "acked", root / "bin",
              root / "tasksets", root / "decisions"):
        d.mkdir(parents=True, exist_ok=True)

    dst = root / "bin" / DEPOSIT_TOOL
    src = _find_deposit_tool()
    dep_note = None
    if src and src.is_file():
        if (not dst.exists()) or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)          # no-clobber-if-equal: idempotent
        os.chmod(dst, os.stat(dst).st_mode | 0o111)
    else:
        dep_note = f"WARN: {DEPOSIT_TOOL} not found to copy (is ork.build bin installed?)"

    cfg = _load_config()
    cfg["coordid"] = seat                       # merge — preserves other keys
    if role == "sub" and args.master:
        cfg["controller"] = _normalize_addr(args.master)
    _save_config(cfg)

    if role == "master":
        at = root / "ACTIVE_TASKSET"
        if not at.exists():
            at.write_text("")                   # empty ok

    print("next steps:")
    if role == "sub":
        stage = os.environ.get("OBT_STAGE", "<your-obt-stagedir>")
        master = cfg.get("controller", "<master-addr>")
        print(f"  launch the restricted coordinator node:")
        print(f"    obt.env.launch.py --stagedir {stage} \\")
        print(f"      --command 'obt.net.node.py --controller {master} "
              f"--name coord-{seat} --restrict msg,sync'")
    print(f"  arm the message monitor:")
    print(f"    tail -n0 -f ~/coordination/inbox.stream")
    if dep_note:
        print(f"  {dep_note}")
    _verdict(True, "init", f"seat<{seat}> role<{role}>")
    return 0


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------
def _check_registration(seat):
    if not seat:
        return ("SKIP", "registration", "no seat/coordid to look up")
    try:
        r = subprocess.run(["obt.net.py", "--json", "list"],
                           capture_output=True, timeout=8)
    except Exception as e:
        return ("SKIP", "registration", f"controller unreachable ({type(e).__name__})")
    if r.returncode != 0:
        return ("SKIP", "registration", "controller unreachable")
    try:
        names = {n.get("name") for n in json.loads(r.stdout.decode() or "[]")}
    except Exception:
        return ("SKIP", "registration", "unparseable list output")
    want = f"coord-{seat}"
    if want in names:
        return ("PASS", "registration", f"{want} registered")
    if seat in names:
        return ("INFO", "registration", f"{seat} registered (name != {want})")
    return ("INFO", "registration", f"{want} not registered (controller reachable)")


def cmd_check(args):
    root = _coord_root()
    cfg = _load_config()
    seat = args.seat or cfg.get("coordid")
    checks = []

    need = [root, root / "inbox", root / "inbox" / "acked", root / "bin",
            root / "tasksets", root / "decisions", 'issues', 'deviations']
    missing = [str(d) for d in need if not d.is_dir()]
    checks.append(("PASS" if not missing else "FAIL", "dirs",
                   "scaffold complete" if not missing else f"missing {missing}"))

    dep = root / "bin" / DEPOSIT_TOOL
    checks.append(("PASS", "deposit-tool", f"present +x {dep}")
                  if dep.is_file() and os.access(dep, os.X_OK)
                  else ("FAIL", "deposit-tool", f"missing/non-exec {dep}"))

    checks.append(("PASS", "coordid", f"coordid={seat}") if seat
                  else ("FAIL", "coordid", "not set in obtnet.json"))

    if dep.is_file():
        try:
            td = Path(tempfile.mkdtemp(prefix="obtcoord_selftest_"))
            b64 = base64.b64encode(b"obt.coord.seat self-test").decode()
            r = subprocess.run([sys.executable, str(dep), "--from", "selftest",
                                "--subject", "selftest", "--payload-b64", b64,
                                "--inbox-root", str(td)],
                               capture_output=True, timeout=15)
            ok = (r.returncode == 0 and any((td / "inbox").glob("*.md"))
                  and (td / "inbox.stream").exists())
            shutil.rmtree(td, ignore_errors=True)
            checks.append(("PASS", "deposit-selftest", "wrote md+stream to temp inbox")
                          if ok else
                          ("FAIL", "deposit-selftest",
                           f"rc={r.returncode} {r.stderr.decode(errors='replace')[:120]}"))
        except Exception as e:
            checks.append(("FAIL", "deposit-selftest", str(e)))
    else:
        checks.append(("FAIL", "deposit-selftest", "deposit tool absent"))

    checks.append(_check_registration(seat))

    for lvl, name, detail in checks:
        print(f"{lvl:4s} {name:16s} {detail}")
    npass = sum(1 for l, _, _ in checks if l == "PASS")
    nfail = sum(1 for l, _, _ in checks if l == "FAIL")
    ninfo = sum(1 for l, _, _ in checks if l in ("INFO", "SKIP"))
    _verdict(nfail == 0, "check", f"seat<{seat}> pass={npass} info={ninfo} fail={nfail}")
    return 0 if nfail == 0 else 1


# ---------------------------------------------------------------------------
# taskset new  (TASKSET FORMAT v1 — template embedded; no orkid checkout needed)
# ---------------------------------------------------------------------------
TASKSET_TMPL = """\
# {title}

intent:  <one-line intent>
created: {created}
seats:   []

<!-- TASKSET FORMAT v1 — one folder, git-trackable, switch by path
       ("master, use taskset <path>").
     epics/<slug>.md    one file per epic
     tasks/<slug>.md    one file per task
     BOARD.md           GENERATED rollup (master-owned; hand edits regenerated away)
     AWAITING_OWNER.md  GENERATED decision queue
     decisions/         owner rulings, one file each (audit trail)

     Epic frontmatter: id, title, priority (P1..), status (open|active|done|parked),
                       seats [..], interacts [epic-ids]  — body: outcome, notes.
     Task frontmatter: id, epic, seat, status (todo|active|blocked|review|done|parked),
                       blockers [task-ids], gates (the <=6min proof list)
                       — body: what / done-when / evidence.

     Rules: humans edit anything but BOARD/AWAITING_OWNER; master validates on load
     (dangling blockers, seat/anchor mismatches, cross-epic interactions) and
     regenerates BOARD on every land/gate/decision; slugs are stable ids; status
     flips are the workflow; commit whenever. -->
"""

EPIC_TMPL = """\
---
id: <epic-slug>
title: <epic title>
priority: P1
status: open
seats: []
interacts: []
---
outcome: <what "done" looks like for this epic>
notes:
"""

TASK_TMPL = """\
---
id: <task-slug>
epic: <epic-slug>
seat: <seat-name>
status: todo
blockers: []
gates: []
---
what: <the change>
done-when: <observable completion>
evidence: <how proven, <=6min gate>
"""

BOARD_TMPL = """\
<!-- GENERATED by the master — do not hand-edit; regenerated on every land/gate/decision. -->
# BOARD (generated)

(empty — no epics or tasks yet)
"""

AWAITING_TMPL = """\
<!-- GENERATED — owner decision queue; regenerated by the master. -->
# AWAITING OWNER (generated)

(no pending decisions)
"""


def _write_if_missing(path, text):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return True


def cmd_taskset(args):
    if args.tscmd != "new":
        _verdict(False, "taskset", f"unknown subcommand {args.tscmd!r}")
        return 2
    dest = Path(args.path).expanduser()
    for d in (dest, dest / "epics", dest / "tasks", dest / "decisions"):
        d.mkdir(parents=True, exist_ok=True)
    title = dest.name or "taskset"
    created = time.strftime("%Y-%m-%d", time.gmtime())
    _write_if_missing(dest / "TASKSET.md", TASKSET_TMPL.format(title=title, created=created))
    _write_if_missing(dest / "epics" / "_template.md", EPIC_TMPL)
    _write_if_missing(dest / "tasks" / "_template.md", TASK_TMPL)
    _write_if_missing(dest / "BOARD.md", BOARD_TMPL)
    _write_if_missing(dest / "AWAITING_OWNER.md", AWAITING_TMPL)
    _write_if_missing(dest / "decisions" / ".gitkeep", "")
    _verdict(True, "taskset", f"new {dest}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="obt.coord.seat.py",
                                 description="bootstrap/validate a coordinator seat")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("init", help="scaffold + wire a seat (idempotent)")
    pi.add_argument("--seat", required=True)
    pi.add_argument("--master", default=None, help="controller addr (subs)")
    pi.add_argument("--role", choices=["sub", "master"], default="sub")
    pc = sub.add_parser("check", help="validate a seat (porcelain PASS/FAIL)")
    pc.add_argument("--seat", default=None, help="default: coordid from config")
    pt = sub.add_parser("taskset", help="taskset scaffolding")
    tsub = pt.add_subparsers(dest="tscmd", required=True)
    ptn = tsub.add_parser("new")
    ptn.add_argument("path")
    args = ap.parse_args(argv)
    return {"init": cmd_init, "check": cmd_check, "taskset": cmd_taskset}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
